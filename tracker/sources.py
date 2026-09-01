"""
Sources de données.

Ne restent que des sources qu'on a le droit d'interroger : flux RSS publiés
pour être consommés par des machines, et l'API publique du CROUS (service
public, données de logement étudiant).

Ont été retirées, et pourquoi :

- LeBonCoin, SeLoger, PAP : conditions d'utilisation interdisant l'extraction
  automatisée. Le code livré ne fonctionnait de toute façon pas (clé API
  `YOUR_API_KEY` en dur, URL PAP mal orthographiée « annonnes »).
- Welcome to the Jungle, HelloWork : mêmes conditions, et pages rendues par
  JavaScript que BeautifulSoup ne voit pas. Ces fonctions renvoyaient
  systématiquement zéro offre.
- GitHub Jobs : service fermé par GitHub en 2021, l'URL renvoie une erreur.
- API Indeed Publisher : fermée aux nouveaux inscrits.
- theses.fr : le site recense les thèses *soutenues*, pas les postes à
  pourvoir. L'endpoint utilisé (`/api/annonces/search.json`) n'existe pas, et
  l'appel plantait de toute façon sur un `hashlib.md5()` sans `.encode()`.

Résultat mesurable : la base livrée contenait une seule offre. Mieux vaut
trois sources qui répondent que huit qui échouent en silence.
"""

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


# ---------------------------------------------------------------------------
# Flux RSS
# ---------------------------------------------------------------------------
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
        for feed in entries:
            out.extend(fetch_feed(session, feed["url"], feed["name"], kind))
    return out


# ---------------------------------------------------------------------------
# CROUS — API publique du service public du logement étudiant
# ---------------------------------------------------------------------------
CROUS_SEARCH = "https://trouverunlogement.lescrous.fr/api/fr/search/38"


def fetch_crous(session: PoliteSession, city: str = "Toulouse",
                max_price: Optional[float] = None) -> List[Offer]:
    """Interroge le moteur de recherche du CROUS.

    Le format de réponse de ce service a déjà changé plusieurs fois. Le
    parseur est donc défensif : toute forme inattendue produit un journal
    explicite plutôt qu'une exception, et `check_sources()` permet de vérifier
    l'état réel du service en une commande.
    """
    payload = session.get_json(CROUS_SEARCH, params={"q": city})
    if payload is None:
        logger.warning("CROUS : pas de réponse exploitable")
        return []

    items = (
        payload.get("results", {}).get("items")
        or payload.get("data", {}).get("residences")
        or payload.get("items")
        or []
    )
    if not isinstance(items, list):
        logger.warning("CROUS : format de réponse inattendu (%s)", type(items).__name__)
        return []

    offers: List[Offer] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        price = item.get("occupationModes", [{}])[0].get("rent", {}).get("min") \
            if isinstance(item.get("occupationModes"), list) else item.get("price")
        try:
            price = float(price) / 100 if isinstance(price, int) and price > 10000 else float(price)
        except (TypeError, ValueError):
            price = None

        if max_price is not None and price is not None and price > max_price:
            continue

        residence_id = item.get("id") or item.get("residence", {}).get("id")
        try:
            offers.append(Offer(
                kind="housing",
                title=item.get("label") or item.get("name") or "Logement CROUS",
                url=f"https://trouverunlogement.lescrous.fr/tools/38/accommodations/{residence_id}",
                source="CROUS",
                organisation=item.get("residence", {}).get("label", "") if isinstance(item.get("residence"), dict) else "",
                location=city,
                description=_strip_html(item.get("description", "")),
                price=price,
            ))
        except ValueError as exc:
            logger.debug("logement ignoré : %s", exc)

    logger.info("%-32s %3d logement(s)", "CROUS", len(offers))
    return offers


# ---------------------------------------------------------------------------
# Collecte complète
# ---------------------------------------------------------------------------
def collect_all(session: PoliteSession, feeds: dict,
                housing_city: str = "Toulouse",
                housing_max_price: Optional[float] = 600,
                with_housing: bool = True) -> List[Offer]:
    offers = collect_feeds(session, feeds)
    if with_housing:
        offers.extend(fetch_crous(session, housing_city, housing_max_price))

    relevant = [o for o in offers if is_relevant(o)]
    dropped = len(offers) - len(relevant)
    if dropped:
        logger.info("%d offre(s) hors domaine écartée(s)", dropped)

    # Dédoublonnage dans le lot courant (deux flux peuvent republier la même
    # annonce) ; la base se charge du dédoublonnage entre exécutions.
    unique, seen = [], set()
    for offer in relevant:
        if offer.id not in seen:
            seen.add(offer.id)
            unique.append(offer)
    return unique


def check_sources(session: PoliteSession, feeds: dict) -> List[dict]:
    """Diagnostic : indique pour chaque source si elle répond et combien
    d'entrées elle renvoie. À lancer avant de soupçonner un bug dans le reste
    du code — une source morte ressemble à une panne applicative."""
    report = []
    for kind, entries in feeds.items():
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
    payload = session.get_json(CROUS_SEARCH, params={"q": "Toulouse"}, use_cache=False)
    report.append({"source": "CROUS", "kind": "housing",
                   "status": "ok" if payload else "injoignable",
                   "entries": len(fetch_crous(session)) if payload else 0,
                   "seconds": round(time.time() - start, 2)})
    return report