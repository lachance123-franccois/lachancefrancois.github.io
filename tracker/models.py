from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


def _normalise(text: str) -> str:
    """Minuscules, sans accents, espaces compactés — pour comparer deux titres
    qui ne diffèrent que par la casse ou la ponctuation."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return text.strip()


def stable_id(*parts: str) -> str:
    """Identifiant reproductible : même entrée, même sortie, sur n'importe
    quelle machine et à n'importe quelle exécution."""
    payload = "|".join(_normalise(p) for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Offer:
    """Une offre, quelle que soit sa catégorie.

    L'ancienne version avait trois dataclasses presque identiques et trois
    tables SQL de vingt colonnes, dont la plupart restaient vides. Une seule
    structure avec un champ `extra` couvre les trois cas et divise le code
    de persistance par trois.
    """

    kind: str                       # "phd" | "internship" | "housing"
    title: str
    url: str
    source: str
    description: str = ""
    location: str = ""
    organisation: str = ""          # entreprise, laboratoire ou résidence
    published: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    price: Optional[float] = None   # logements uniquement
    collected_at: str = field(default_factory=now_iso)

    KINDS = ("phd", "internship", "housing")

    def __post_init__(self):
        if self.kind not in self.KINDS:
            raise ValueError(f"kind inconnu : {self.kind!r} (attendu {self.KINDS})")
        if not self.title.strip():
            raise ValueError("une offre doit avoir un titre")
        if not self.url.strip():
            raise ValueError("une offre doit avoir une URL")
        self.title = " ".join(self.title.split())[:300]
        self.description = " ".join(self.description.split())[:1000]

    @property
    def id(self) -> str:
        return stable_id(self.kind, self.title, self.organisation or self.url)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        return d


# Mots-clés du domaine : traitement du signal, image, apprentissage.
# Servent au filtrage de pertinence et à l'affichage.
KEYWORDS = [
    "image", "vision par ordinateur", "computer vision", "segmentation",
    "signal", "traitement du signal", "signal processing", "radar", "lidar",
    "deep learning", "machine learning", "apprentissage", "réseau de neurones",
    "neural network", "classification", "détection", "compression",
    "télécom", "telecom", "5g", "6g", "mimo", "antenne",
    "python", "pytorch", "tensorflow", "opencv", "matlab", "embarqué",
]


def extract_keywords(text: str, limit: int = 8) -> List[str]:
    low = _normalise(text)
    found = [kw for kw in KEYWORDS if _normalise(kw) in low]
    # dédoublonnage en conservant l'ordre de la liste de référence
    seen, out = set(), []
    for kw in found:
        if kw not in seen:
            seen.add(kw)
            out.append(kw)
    return out[:limit]


def is_relevant(offer: Offer) -> bool:
    """Une offre est pertinente si elle touche au domaine. Les logements ne
    sont pas filtrés sur les mots-clés techniques, évidemment."""
    if offer.kind == "housing":
        return True
    return bool(extract_keywords(f"{offer.title} {offer.description}"))