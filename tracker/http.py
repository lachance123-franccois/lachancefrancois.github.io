from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "AcademicTrackerBot/1.0 "
    "(+https://lachance123-franccois.github.io/; veille personnelle stage/these)"
)


class RobotsPolicy:
    """Consulte et met en cache le robots.txt de chaque domaine."""

    def __init__(self, user_agent: str = DEFAULT_UA):
        self.user_agent = user_agent
        self._parsers: dict[str, Optional[RobotFileParser]] = {}

    def _parser_for(self, url: str) -> Optional[RobotFileParser]:
        origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if origin in self._parsers:
            return self._parsers[origin]

        parser = RobotFileParser()
        parser.set_url(f"{origin}/robots.txt")
        try:
            parser.read()
        except Exception as exc:
            # Pas de robots.txt lisible : on n'invente pas d'autorisation,
            # mais on ne bloque pas non plus une ressource publique.
            logger.debug("robots.txt illisible pour %s : %s", origin, exc)
            parser = None
        self._parsers[origin] = parser
        return parser

    def allows(self, url: str) -> bool:
        parser = self._parser_for(url)
        if parser is None:
            return True
        allowed = parser.can_fetch(self.user_agent, url)
        if not allowed and getattr(parser, "disallow_all", False):
            # Conforme au RFC 9309 : un robots.txt renvoyant 401 ou 403
            # équivaut à un refus global. Cela se produit aussi derrière un
            # proxy d'entreprise, d'où le message explicite.
            logger.info(
                "robots.txt de %s inaccessible (401/403) : traité comme un refus",
                urlparse(url).netloc,
            )
        return allowed

    def crawl_delay(self, url: str, default: float = 2.0) -> float:
        parser = self._parser_for(url)
        if parser is None:
            return default
        try:
            delay = parser.crawl_delay(self.user_agent)
        except Exception:
            delay = None
        return float(delay) if delay else default


class PoliteSession:
    """Session HTTP : un appel à la fois, délai respecté, réponses en cache."""

    def __init__(
        self,
        user_agent: str = DEFAULT_UA,
        cache_dir: str = ".cache",
        cache_ttl_hours: float = 6.0,
        min_delay: float = 2.0,
        timeout: float = 20.0,
        respect_robots: bool = True,
    ):
        self.user_agent = user_agent
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl_hours * 3600
        self.min_delay = min_delay
        self.timeout = timeout
        self.respect_robots = respect_robots

        self.robots = RobotsPolicy(user_agent)
        self._last_request = 0.0

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ---- cache -----------------------------------------------------------
    def _cache_path(self, url: str, params: Optional[dict]) -> Path:
        key = hashlib.sha256(
            (url + json.dumps(params or {}, sort_keys=True)).encode()
        ).hexdigest()
        return self.cache_dir / f"{key}.json"

    def _read_cache(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > self.cache_ttl:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))["body"]
        except Exception:
            return None

    def _write_cache(self, path: Path, body: str, url: str) -> None:
        try:
            path.write_text(
                json.dumps({"url": url, "body": body}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.debug("écriture du cache impossible : %s", exc)

    def purge_cache(self, max_age_hours: float = 168.0) -> int:
        """Supprime les entrées trop vieilles. L'ancien cache grossissait
        indéfiniment : chaque page HTML complète y était conservée."""
        cutoff = time.time() - max_age_hours * 3600
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
                removed += 1
        return removed

    # ---- requêtes --------------------------------------------------------
    def _wait(self, delay: float) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request = time.time()

    def get_text(self, url: str, params: Optional[dict] = None,
                 use_cache: bool = True) -> Optional[str]:
        """Renvoie le corps de la réponse, ou None si la requête est refusée,
        interdite par robots.txt, ou en échec. Ne lève jamais : un appelant
        qui interroge cinq sources ne doit pas s'arrêter à la première panne."""
        if self.respect_robots and not self.robots.allows(url):
            logger.warning("robots.txt interdit %s — source ignorée", url)
            return None

        path = self._cache_path(url, params)
        if use_cache:
            cached = self._read_cache(path)
            if cached is not None:
                logger.debug("cache : %s", url)
                return cached

        delay = max(self.min_delay, self.robots.crawl_delay(url, self.min_delay))
        self._wait(delay)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.warning("échec réseau %s : %s", url, exc)
            return None

        if response.status_code == 429:
            logger.warning("429 sur %s — la source demande de ralentir", url)
            return None
        if not response.ok:
            logger.warning("HTTP %s sur %s", response.status_code, url)
            return None

        body = response.text
        self._write_cache(path, body, url)
        return body

    def post_json(self, url: str, payload: dict, use_cache: bool = True):
        """POST avec corps JSON.

        Nécessaire pour les services qui refusent GET : un code 405
        « Method Not Allowed » signifie que l'adresse existe mais que le verbe
        est mauvais — c'est le cas du moteur de recherche du CROUS.
        Le cache est indexé sur l'URL *et* le corps, sinon deux recherches
        différentes se recouvriraient.
        """
        if self.respect_robots and not self.robots.allows(url):
            logger.warning("robots.txt interdit %s — source ignorée", url)
            return None

        path = self._cache_path(url, payload)
        if use_cache:
            cached = self._read_cache(path)
            if cached is not None:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass

        self._wait(max(self.min_delay, self.robots.crawl_delay(url, self.min_delay)))

        try:
            response = self.session.post(
                url, json=payload, timeout=self.timeout,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
        except requests.RequestException as exc:
            logger.warning("échec réseau %s : %s", url, exc)
            return None

        if not response.ok:
            logger.warning("HTTP %s sur %s (POST)", response.status_code, url)
            return None

        self._write_cache(path, response.text, url)
        try:
            return response.json()
        except ValueError:
            logger.warning("réponse non JSON depuis %s", url)
            return None

    def discover_feeds(self, url: str):
        """Liste les flux RSS/Atom qu'une page déclare elle-même.

        Un site qui publie un flux le signale dans son en-tête HTML :
            <link rel="alternate" type="application/rss+xml" href="...">
        Chercher cette déclaration est plus fiable que deviner une adresse —
        c'est ainsi que les URL de config/feeds.json doivent être trouvées.
        """
        body = self.get_text(url, use_cache=False)
        if body is None:
            return []

        found = []
        pattern = re.compile(
            r'<link[^>]+rel=["\']alternate["\'][^>]*>', re.IGNORECASE)
        for tag in pattern.findall(body):
            if "rss" not in tag.lower() and "atom" not in tag.lower():
                continue
            href = re.search(r'href=["\']([^"\']+)["\']', tag)
            title = re.search(r'title=["\']([^"\']*)["\']', tag)
            if href:
                found.append({
                    "url": urljoin(url, href.group(1)),
                    "title": title.group(1) if title else "(sans titre)",
                })
        return found

    def get_json(self, url: str, params: Optional[dict] = None,
                 use_cache: bool = True):
        body = self.get_text(url, params=params, use_cache=use_cache)
        if body is None:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            logger.warning("réponse non JSON depuis %s", url)
            return None


def session_from_env() -> PoliteSession:
    return PoliteSession(
        user_agent=os.environ.get("TRACKER_USER_AGENT", DEFAULT_UA),
        cache_dir=os.environ.get("TRACKER_CACHE_DIR", ".cache"),
        min_delay=float(os.environ.get("TRACKER_MIN_DELAY", "2")),
    )