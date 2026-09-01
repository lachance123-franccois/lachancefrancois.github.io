"""
Persistance SQLite.

Corrections par rapport à `database.py` :

- Une seule table au lieu de trois quasi identiques (60 colonnes au total,
  la plupart toujours vides).
- `mark_notified([])` ne construit plus `WHERE id IN ()`, qui est une erreur
  de syntaxe SQL. Le cas liste vide est traité.
- `cleanup_old` renvoie le vrai nombre de lignes supprimées. L'ancienne
  version lisait `cursor.rowcount` après la boucle : elle ne comptait que la
  dernière table. Elle comparait aussi `strftime('%s', ...)`, qui renvoie du
  texte, à un flottant — la comparaison était fausse.
- La connexion est utilisable comme gestionnaire de contexte, donc elle est
  fermée même en cas d'exception.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .models import Offer

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    id            TEXT PRIMARY KEY,
    kind          TEXT NOT NULL CHECK (kind IN ('phd','internship','housing')),
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    source        TEXT NOT NULL,
    description   TEXT,
    location      TEXT,
    organisation  TEXT,
    published     TEXT,
    keywords      TEXT,
    price         REAL,
    collected_at  TEXT NOT NULL,
    notified      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_offers_kind      ON offers(kind);
CREATE INDEX IF NOT EXISTS idx_offers_notified  ON offers(notified);
CREATE INDEX IF NOT EXISTS idx_offers_collected ON offers(collected_at);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    found       INTEGER NOT NULL,
    inserted    INTEGER NOT NULL,
    duration_s  REAL,
    status      TEXT NOT NULL,
    error       TEXT
);
"""


class Store:
    def __init__(self, path: str = "data/offers.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    # ---- écriture --------------------------------------------------------
    def insert(self, offers: Iterable[Offer]) -> int:
        """Insère les offres inconnues. Renvoie le nombre réellement ajouté."""
        rows = [
            (
                o.id, o.kind, o.title, o.url, o.source, o.description,
                o.location, o.organisation, o.published,
                json.dumps(o.keywords, ensure_ascii=False),
                o.price, o.collected_at,
            )
            for o in offers
        ]
        if not rows:
            return 0

        before = self.conn.total_changes
        self.conn.executemany(
            """INSERT OR IGNORE INTO offers
               (id, kind, title, url, source, description, location,
                organisation, published, keywords, price, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.conn.commit()
        inserted = self.conn.total_changes - before
        logger.info("%d offre(s) nouvelle(s) sur %d vue(s)", inserted, len(rows))
        return inserted

    def mark_notified(self, ids: List[str]) -> int:
        if not ids:            # l'ancien code produisait « IN () » → erreur SQL
            return 0
        placeholders = ",".join("?" * len(ids))
        cur = self.conn.execute(
            f"UPDATE offers SET notified = 1 WHERE id IN ({placeholders})", ids
        )
        self.conn.commit()
        return cur.rowcount

    def log_run(self, kind: str, found: int, inserted: int,
                duration_s: float, status: str = "ok",
                error: Optional[str] = None) -> None:
        self.conn.execute(
            """INSERT INTO runs (started_at, kind, found, inserted,
                                 duration_s, status, error)
               VALUES (?,?,?,?,?,?,?)""",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"),
             kind, found, inserted, duration_s, status, error),
        )
        self.conn.commit()

    # ---- lecture ---------------------------------------------------------
    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        try:
            d["keywords"] = json.loads(d.get("keywords") or "[]")
        except json.JSONDecodeError:
            d["keywords"] = []
        return d

    def pending(self, kind: Optional[str] = None) -> List[dict]:
        """Offres pas encore notifiées."""
        sql = "SELECT * FROM offers WHERE notified = 0"
        args: list = []
        if kind:
            sql += " AND kind = ?"
            args.append(kind)
        sql += " ORDER BY collected_at DESC"
        return [self._row_to_dict(r) for r in self.conn.execute(sql, args)]

    def recent(self, kind: Optional[str] = None, limit: int = 60) -> List[dict]:
        sql = "SELECT * FROM offers"
        args: list = []
        if kind:
            sql += " WHERE kind = ?"
            args.append(kind)
        sql += " ORDER BY collected_at DESC LIMIT ?"
        args.append(limit)
        return [self._row_to_dict(r) for r in self.conn.execute(sql, args)]

    def stats(self) -> dict:
        out = {"total": 0, "pending": 0, "by_kind": {}}
        for row in self.conn.execute(
            """SELECT kind,
                      COUNT(*) AS total,
                      SUM(CASE WHEN notified = 0 THEN 1 ELSE 0 END) AS pending
               FROM offers GROUP BY kind"""
        ):
            out["by_kind"][row["kind"]] = {
                "total": row["total"],
                "pending": row["pending"] or 0,
            }
            out["total"] += row["total"]
            out["pending"] += row["pending"] or 0

        last = self.conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT 5"
        ).fetchall()
        out["last_runs"] = [dict(r) for r in last]
        return out

    def cleanup_old(self, days: int = 90) -> int:
        """Supprime les offres collectées il y a plus de `days` jours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)) \
            .isoformat(timespec="seconds")
        # Les dates sont stockées en ISO 8601 UTC : la comparaison
        # lexicographique est équivalente à la comparaison chronologique.
        cur = self.conn.execute(
            "DELETE FROM offers WHERE collected_at < ?", (cutoff,)
        )
        self.conn.commit()
        logger.info("%d offre(s) ancienne(s) supprimée(s)", cur.rowcount)
        return cur.rowcount