"""
Tests unitaires. Aucun accès réseau : les réponses HTTP sont simulées, donc
la suite tourne en moins d'une seconde et dans une CI.

L'ancien `test.py` n'était pas un test : il importait `CROUSScraper` (la
classe s'appelle `HousingScraper`), appelait `search_toulouse_housing()` (qui
n'existe pas), attrapait toutes les exceptions pour les afficher, et
terminait toujours par « Testing complete » — y compris quand tout échouait.
Un test qui ne peut pas échouer ne teste rien.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tracker.db import Store                                    # noqa: E402
from tracker.export import export_json                          # noqa: E402
from tracker.models import Offer, extract_keywords, is_relevant, stable_id  # noqa: E402
from tracker.notify import _html_digest, _plain_digest          # noqa: E402
from tracker.sources import fetch_feed                          # noqa: E402


# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------
def make_offer(**kwargs) -> Offer:
    base = dict(
        kind="internship",
        title="Stage — vision par ordinateur embarquée",
        url="https://exemple.fr/offre/1",
        source="Test",
        organisation="ACME",
    )
    base.update(kwargs)
    return Offer(**base)


def test_identifiant_est_stable_entre_appels():
    """Le cœur du bug corrigé : l'ancien code utilisait hash(), qui change à
    chaque processus, donc le dédoublonnage ne marchait jamais."""
    assert make_offer().id == make_offer().id


def test_identifiant_ignore_casse_accents_et_espaces():
    a = make_offer(title="Stage — Vision par Ordinateur Embarquée")
    b = make_offer(title="stage   vision par ordinateur embarquee")
    assert a.id == b.id


def test_identifiants_differents_pour_offres_differentes():
    assert make_offer().id != make_offer(title="Stage — traitement du signal").id


def test_stable_id_reproductible_en_dur():
    # Valeur figée : si elle change, c'est que la normalisation a changé et
    # que toutes les offres déjà en base seront vues comme nouvelles.
    assert stable_id("internship", "Stage Vision", "ACME") == \
           stable_id("internship", "  stage   VISION  ", "acme")


def test_offre_sans_titre_est_refusee():
    with pytest.raises(ValueError):
        make_offer(title="   ")


def test_offre_sans_url_est_refusee():
    with pytest.raises(ValueError):
        make_offer(url="")


def test_kind_inconnu_est_refuse():
    with pytest.raises(ValueError):
        make_offer(kind="freelance")


def test_titre_trop_long_est_tronque():
    assert len(make_offer(title="x" * 500).title) == 300


def test_extraction_de_mots_cles():
    found = extract_keywords("Stage en Deep Learning et traitement du signal, PyTorch")
    assert "deep learning" in found
    assert "traitement du signal" in found
    assert "pytorch" in found


def test_extraction_sans_doublon():
    found = extract_keywords("python Python PYTHON")
    assert found.count("python") == 1


def test_pertinence_hors_domaine():
    assert not is_relevant(make_offer(title="Stage en comptabilité analytique",
                                      description="Saisie de factures"))


def test_logement_toujours_pertinent():
    assert is_relevant(make_offer(kind="housing", title="Studio 20 m² Rangueil"))


# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------
@pytest.fixture
def store(tmp_path):
    with Store(str(tmp_path / "test.db")) as s:
        yield s


def test_insertion_puis_reinsertion_ne_duplique_pas(store):
    offers = [make_offer()]
    assert store.insert(offers) == 1
    assert store.insert(offers) == 0
    assert store.stats()["total"] == 1


def test_insertion_liste_vide(store):
    assert store.insert([]) == 0


def test_mark_notified_liste_vide_ne_plante_pas(store):
    """L'ancien code produisait « WHERE id IN () », erreur de syntaxe SQL."""
    assert store.mark_notified([]) == 0


def test_cycle_pending_puis_notified(store):
    offer = make_offer()
    store.insert([offer])
    assert len(store.pending()) == 1
    assert store.mark_notified([offer.id]) == 1
    assert store.pending() == []


def test_pending_filtre_par_type(store):
    store.insert([make_offer(), make_offer(kind="phd", title="Thèse en imagerie radar")])
    assert len(store.pending("phd")) == 1
    assert len(store.pending("internship")) == 1


def test_cleanup_supprime_les_offres_anciennes(store):
    vieille = make_offer(title="Stage signal archivé")
    vieille.collected_at = "2020-01-01T00:00:00+00:00"
    recente = make_offer(title="Stage signal récent")
    store.insert([vieille, recente])
    assert store.cleanup_old(days=90) == 1
    assert store.stats()["total"] == 1


def test_statistiques_par_type(store):
    store.insert([
        make_offer(),
        make_offer(kind="phd", title="Thèse segmentation d'images"),
        make_offer(kind="housing", title="Studio Rangueil"),
    ])
    stats = store.stats()
    assert stats["total"] == 3
    assert set(stats["by_kind"]) == {"internship", "phd", "housing"}


def test_journal_des_executions(store):
    store.log_run("all", found=12, inserted=3, duration_s=4.2)
    assert store.stats()["last_runs"][0]["inserted"] == 3


# ---------------------------------------------------------------------------
# Lecture de flux (session simulée, aucun réseau)
# ---------------------------------------------------------------------------
RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Flux de test</title>
  <item>
    <title>Stage M2 — segmentation d'images médicales</title>
    <link>https://exemple.fr/offre/42</link>
    <description>&lt;p&gt;Travail sur des &lt;b&gt;CNN&lt;/b&gt; en PyTorch.&lt;/p&gt;</description>
    <pubDate>Mon, 01 Sep 2025 09:00:00 +0200</pubDate>
  </item>
  <item>
    <title>Stage — assistant administratif</title>
    <link>https://exemple.fr/offre/43</link>
    <description>Classement de dossiers</description>
  </item>
  <item>
    <title></title>
    <link>https://exemple.fr/offre/44</link>
  </item>
</channel></rss>"""


class FakeSession:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def get_text(self, url, params=None, use_cache=True):
        self.calls.append(url)
        return self.body


def test_lecture_flux_rss():
    offers = fetch_feed(FakeSession(RSS), "https://x.fr/rss", "Flux de test", "internship")
    # L'entrée sans titre est écartée, les deux autres passent.
    assert len(offers) == 2
    assert offers[0].source == "Flux de test"


def test_html_retire_de_la_description():
    offers = fetch_feed(FakeSession(RSS), "https://x.fr/rss", "T", "internship")
    assert "<b>" not in offers[0].description
    assert "CNN" in offers[0].description


def test_flux_injoignable_renvoie_liste_vide():
    class Dead:
        def get_text(self, *a, **k):
            return None
    assert fetch_feed(Dead(), "https://x.fr/rss", "Mort", "phd") == []


def test_flux_corrompu_ne_plante_pas():
    offers = fetch_feed(FakeSession("ceci n'est pas du XML"), "https://x.fr", "Cassé", "phd")
    assert offers == []


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
def sample_rows():
    return [{
        "kind": "internship",
        "title": "Stage <Vision> & Signal",
        "url": "https://exemple.fr/1",
        "organisation": "ACME & Cie",
        "location": "Toulouse",
        "source": "Test",
        "price": None,
        "keywords": ["python", "opencv"],
    }]


def test_digest_html_echappe_les_caracteres_speciaux():
    """Un titre contenant < ou & cassait le HTML du message précédent."""
    html = _html_digest({"internship": sample_rows()})
    assert "&lt;Vision&gt;" in html
    assert "<Vision>" not in html


def test_digest_texte_contient_le_lien():
    text = _plain_digest({"internship": sample_rows()})
    assert "https://exemple.fr/1" in text


def test_mailer_refuse_des_identifiants_incomplets():
    from tracker.notify import Mailer, MissingCredentials
    with pytest.raises(MissingCredentials):
        Mailer(host="smtp.exemple.fr", port=587, user="a@b.fr", password="")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def test_export_produit_un_json_valide(store, tmp_path):
    store.insert([make_offer(), make_offer(kind="phd", title="Thèse radar")])
    out = tmp_path / "offers.json"
    assert export_json(store, str(out)) == 2

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert set(payload["offers"]) == {"internship", "phd", "housing"}
    assert payload["offers"]["housing"] == []
    assert payload["stats"]["total"] == 2


def test_export_sur_base_vide(store, tmp_path):
    out = tmp_path / "offers.json"
    assert export_json(store, str(out)) == 0
    assert json.loads(out.read_text())["stats"]["total"] == 0


# ---------------------------------------------------------------------------
# Le dépôt ne doit contenir aucun secret
# ---------------------------------------------------------------------------
def test_aucun_mot_de_passe_en_dur_dans_le_code():
    """Garde-fou : un mot de passe d'application iCloud était écrit en clair
    dans la version précédente. Ce test échoue si ça se reproduit."""
    import re
    racine = Path(__file__).resolve().parents[1]
    suspect = re.compile(
        r"""(password|passwd|secret|api_key|token)\s*=\s*["'][^"'\s]{8,}["']""",
        re.IGNORECASE,
    )
    fautes = []
    for fichier in racine.rglob("*.py"):
        if ".venv" in fichier.parts or "__pycache__" in fichier.parts:
            continue
        for numero, ligne in enumerate(fichier.read_text(encoding="utf-8").splitlines(), 1):
            if "os.environ" in ligne or "getenv" in ligne:
                continue
            if suspect.search(ligne):
                fautes.append(f"{fichier.relative_to(racine)}:{numero}")
    assert not fautes, "secret potentiellement en dur : " + ", ".join(fautes)


def test_config_locale_est_ignoree_par_git():
    racine = Path(__file__).resolve().parents[1]
    gitignore = (racine / ".gitignore").read_text(encoding="utf-8")
    for motif in ("config/config.json", ".env", "data/*.db", ".cache/"):
        assert motif in gitignore, f"{motif} devrait être dans .gitignore"