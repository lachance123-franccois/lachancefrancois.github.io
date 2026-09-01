
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import List, Optional

import feedparser

from .http import PoliteSession
from .models import Offer, extract_keywords, is_relevant

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub(" ", text or "")


def load_feeds(path: str = "config/feeds.json") -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("fichier de flux introuvable : %s", path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("fichier de flux illisible (%s) : %s", path, exc)
        return {}


def fetch_feed(session: PoliteSession, url: str, name: str,
               kind: str, limit: int = 25) -> List[Offer]:
    """Lit un flux RSS ou Atom. Le corps passe par la session polie plutôt que
    par `feedparser.parse(url)` directement, pour bénéficier du cache, du
    délai entre requêtes et du user-agent identifié."""
    body = session.get_text(url)
    if body is None:
        logger.warning("flux injoignable : %s", name)
        return []

    parsed = feedparser.parse(body)
    if parsed.bozo and not parsed.entries:
        logger.warning("flux illisible : %s (%s)", name, parsed.get("bozo_exception"))
        return []

    offers: List[Offer] = []
    for entry in parsed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if not title or not link:
            continue

        description = _strip_html(
            entry.get("summary") or entry.get("description") or ""
        )
        try:
            offer = Offer(
                kind=kind,
                title=title,
                url=link,
                source=name,
                description=description,
                published=entry.get("published") or entry.get("updated"),
                keywords=extract_keywords(f"{title} {description}"),
            )
        except ValueError as exc:
            logger.debug("entrée ignorée dans %s : %s", name, exc)
            continue
        offers.append(offer)

    logger.info("%-32s %3d entrée(s)", name, len(offers))
    return offers


def collect_feeds(session: PoliteSession, feeds: dict) -> List[Offer]:
    out: List[Offer] = []
    for kind, entries in feeds.items():
        if kind.startswith("_") or not isinstance(entries, list):
            continue                      # clés de documentation
        for feed in entries:
            out.extend(fetch_feed(session, feed["url"], feed["name"], kind))
    return out



CROUS_TOOL_ID = 44
CROUS_SEARCH = "https://trouverunlogement.lescrous.fr/api/fr/search/{tool_id}"

CROUS_BOUNDS = {"Toulouse": "1.3120,43.6700_1.5230,43.5340"}


def fetch_crous(session: PoliteSession, city: str = "Toulouse",
                max_price: Optional[float] = None,
                tool_id: int = CROUS_TOOL_ID,
                bounds: Optional[str] = None) -> List[Offer]:
    """Interroge le moteur de recherche du CROUS.

    Ce service refuse GET et répond 405 « Method Not Allowed » : la requête
    doit être un POST avec un corps JSON. La première version du code faisait
    un GET, ce qui explique qu'aucun logement n'ait jamais été collecté.

    Le format de réponse a déjà changé plusieurs fois. Le parseur est donc
    défensif : toute forme inattendue produit un journal explicite indiquant
    les clés reçues, plutôt qu'une exception ou un silence.
    """
    url = CROUS_SEARCH.format(tool_id=tool_id)
    payload = {
        "idTool": tool_id,
        "need_aggregation": False,
        "page": 1,
        "pageSize": 50,
        "sector": None,
        "occupationMode": None,
        "bounds": bounds or CROUS_BOUNDS.get(city, CROUS_BOUNDS["Toulouse"]),
    }

    data = session.post_json(url, payload)
    if data is None:
        logger.warning(
            "CROUS : pas de réponse exploitable. Vérifier l'identifiant d'outil "
            "(%s) sur trouverunlogement.lescrous.fr — il figure dans l'URL "
            "/tools/<id>/search.", tool_id)
        return []

    items = (
        (data.get("results") or {}).get("items")
        or (data.get("data") or {}).get("residences")
        or data.get("items")
        or []
    )
    if not isinstance(items, list) or not items:
        logger.warning("CROUS : aucune annonce dans la réponse (clés reçues : %s)",
                       ", ".join(sorted(data.keys())) or "aucune")
        return []

    offers: List[Offer] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        price = None
        modes = item.get("occupationModes")
        if isinstance(modes, list) and modes:
            rent = (modes[0] or {}).get("rent")
            if isinstance(rent, dict):
                price = rent.get("min")
        if price is None:
            price = item.get("price")
        try:
            price = float(price)
            # Certains champs sont exprimés en centimes.
            if price > 5000:
                price /= 100
        except (TypeError, ValueError):
            price = None

        if max_price is not None and price is not None and price > max_price:
            continue

        residence = item.get("residence") if isinstance(item.get("residence"), dict) else {}
        item_id = item.get("id") or residence.get("id")

        try:
            offers.append(Offer(
                kind="housing",
                title=item.get("label") or residence.get("label") or "Logement CROUS",
                url=("https://trouverunlogement.lescrous.fr/tools/"
                     f"{tool_id}/accommodations/{item_id}"),
                source="CROUS",
                organisation=residence.get("label", ""),
                location=city,
                description=_strip_html(item.get("description", "")),
                price=price,
            ))
        except ValueError as exc:
            logger.debug("logement ignoré : %s", exc)

    logger.info("%-32s %3d logement(s)", "CROUS", len(offers))
    return offers


def collect_all(session: PoliteSession, feeds: dict,
                housing_city: str = "Toulouse",
                housing_max_price: Optional[float] = 600,
                with_housing: bool = True,
                crous_tool_id: int = CROUS_TOOL_ID,
                crous_bounds: Optional[str] = None) -> List[Offer]:
    offers = collect_feeds(session, feeds)
    if with_housing:
        offers.extend(fetch_crous(session, housing_city, housing_max_price,
                                  tool_id=crous_tool_id, bounds=crous_bounds))

    relevant = [o for o in offers if is_relevant(o)]
    dropped = len(offers) - len(relevant)
    if dropped:
        logger.info("%d offre(s) hors domaine écartée(s)", dropped)

    unique, seen = [], set()
    for offer in relevant:
        if offer.id not in seen:
            seen.add(offer.id)
            unique.append(offer)
    return unique


def check_sources(session: PoliteSession, feeds: dict) -> List[dict]:
    report = []
    for kind, entries in feeds.items():
        if kind.startswith("_") or not isinstance(entries, list):
            continue
        for feed in entries:
            start = time.time()
            body = session.get_text(feed["url"], use_cache=False)
            if body is None:
                report.append({"source": feed["name"], "kind": kind,
                               "status": "injoignable", "entries": 0,
                               "seconds": round(time.time() - start, 2)})
                continue
            parsed = feedparser.parse(body)
            report.append({
                "source": feed["name"], "kind": kind,
                "status": "ok" if parsed.entries else "vide",
                "entries": len(parsed.entries),
                "seconds": round(time.time() - start, 2),
            })

    start = time.time()
    housing = fetch_crous(session)
    report.append({"source": "CROUS", "kind": "housing",
                   "status": "ok" if housing else "vide ou injoignable",
                   "entries": len(housing),
                   "seconds": round(time.time() - start, 2)})
    return report