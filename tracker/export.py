"""Export JSON consommé par la page web.

Le fichier est écrit à la racine du site (`data/offers.json`) : c'est le même
dépôt qui héberge le portfolio, et GitHub Pages le sert tel quel à
`veille.html`.

L'ancien tableau de bord affichait des données inventées — des stages chez
Continental et au CNES qui n'ont jamais existé. Il lit maintenant ce fichier,
et affiche un état vide explicite quand il n'y a rien : c'est une information,
pas un défaut.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .db import Store

logger = logging.getLogger(__name__)

PUBLIC_FIELDS = (
    "id", "kind", "title", "url", "source", "description",
    "location", "organisation", "published", "keywords", "price", "collected_at",
)


def export_json(store: Store, path: str = "data/offers.json",
                limit_per_kind: int = 60) -> int:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stats": store.stats(),
        "offers": {},
    }
    total = 0
    for kind in ("internship", "phd", "housing"):
        rows = store.recent(kind, limit=limit_per_kind)
        payload["offers"][kind] = [
            {k: row.get(k) for k in PUBLIC_FIELDS} for row in rows
        ]
        total += len(rows)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("%d offre(s) exportée(s) vers %s", total, path)
    return total