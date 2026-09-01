# lachance123-franccois.github.io

Portfolio et outils de François Lachance Awounang-Ngounou — ingénieur
traitement du signal, image et machine learning, Toulouse.

Un seul dépôt, deux moitiés qui se parlent :

- **le site**, servi par GitHub Pages à
  [lachance123-franccois.github.io](https://lachance123-franccois.github.io) ;
- **le backend de veille**, un programme Python exécuté chaque matin par
  GitHub Actions, qui collecte des offres de stage, de thèse et de logement et
  republie `data/offers.json` — lu par la page `veille.html`.

---

## Structure

```
.
├── index.html               Accueil
├── machine-learning.html    Projets IA & machine learning
├── matlab.html              Projets signal & image
├── veille.html              Projet « veille automatisée » + tableau de bord
├── cv-op.html               CV (lecteur PDF intégré)
├── contact.html             Formulaire de contact
├── 404.html
│
├── css/theme.css            Design system — source unique de vérité
├── js/main.js               Navigation, animations, formulaire (toutes les pages)
├── js/projets-ml.js         Projets et visualisations de la page ML
├── js/veille.js             Tableau de bord de veille.html
├── assets/                  Icônes, image de partage, CV en PDF
│
├── tracker/                 Backend de veille (Python)
│   ├── models.py            Modèle d'offre + empreinte stable + mots-clés
│   ├── http.py              Client HTTP poli : robots.txt, délai, cache
│   ├── db.py                SQLite
│   ├── sources.py           Flux RSS + API CROUS, avec diagnostic
│   ├── notify.py            Digest email (texte + HTML)
│   ├── export.py            Écrit data/offers.json
│   └── cli.py               collect / check / stats / export / cleanup
├── tests/                   31 tests, sans accès réseau
├── config/                  feeds.json et config.example.json
├── data/offers.json         Produit par la collecte, lu par veille.html
│
├── manifest.json  robots.txt  sitemap.xml
└── .github/workflows/veille.yml
```

Les deux moitiés ne se croisent qu'en un point : **`data/offers.json`**. Le
Python l'écrit, le JavaScript le lit. Rien d'autre n'est partagé, ce qui permet
de travailler sur l'un sans casser l'autre.

---

## Le site

Aucune étape de compilation : du HTML, du CSS et du JavaScript natif.

```bash
python3 -m http.server 8000
# puis http://localhost:8000
```

Toutes les couleurs, tailles de texte et espacements viennent de
`css/theme.css`. Les pages n'ajoutent que ce qui leur est propre. Modifier une
variable dans le bloc `:root` change le site entier — c'est la raison d'être de
ce fichier, qui remplace les sept feuilles de style précédentes.

---

## La veille

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp config/config.example.json config/config.json
cp .env.example .env          # puis remplir les identifiants SMTP

python -m tracker.cli check     # les sources répondent-elles ?
python -m tracker.cli collect   # collecte, base, export JSON
python -m tracker.cli stats     # état de la base
```

| Commande | Effet |
|---|---|
| `collect` | collecte, insertion en base, écriture de `data/offers.json` |
| `collect --notify` | idem, plus l'envoi du digest par email |
| `check` | teste chaque source une par une, sans rien écrire |
| `stats` | offres par catégorie et dernières exécutions |
| `export` | régénère `data/offers.json` depuis la base |
| `cleanup --days 90` | supprime offres et cache anciens |

### Sources

Uniquement des sources destinées à être lues par des machines : flux RSS
publiés par les sites eux-mêmes, et l'API publique du CROUS. Le client HTTP
consulte `robots.txt` avant chaque requête, s'annonce avec un user-agent
identifiable, respecte le `Crawl-delay` déclaré et met les réponses en cache.
Les sites dont les conditions d'utilisation interdisent l'extraction
automatisée ne sont pas interrogés.

Ajouter une source : une entrée dans `config/feeds.json`, puis
`python -m tracker.cli check` pour vérifier qu'elle répond.

### Secrets

Les identifiants SMTP **ne sont jamais dans un fichier de configuration**. En
local ils viennent de `.env` (ignoré par Git), en CI des secrets GitHub.

| Variable | Rôle |
|---|---|
| `SMTP_HOST`, `SMTP_PORT` | serveur d'envoi |
| `SMTP_USER`, `SMTP_PASSWORD` | mot de passe **d'application**, pas celui du compte |
| `NOTIFY_TO` | destinataire du digest |

Deux tests vérifient qu'aucun secret n'est écrit en dur et que `.gitignore`
couvre la configuration locale.

### Tests

```bash
python -m pytest tests/ -q
```

31 tests, aucun accès réseau — les réponses HTTP sont simulées, la suite
tourne en une fraction de seconde et passe en CI.

---

## Automatisation

`.github/workflows/veille.yml` s'exécute chaque matin : il installe les
dépendances, lance les tests, restaure la base depuis le cache Actions,
collecte, envoie le digest, purge les offres de plus de 90 jours et committe
`data/offers.json`. GitHub Pages sert le nouveau fichier dans la minute.

---

## À compléter avant publication

Chercher `⟦` dans le dépôt : chaque occurrence est une valeur à renseigner.

- [ ] Dates de disponibilité dans le bandeau (présent sur toutes les pages)
- [ ] Résultats chiffrés des projets (`index.html`, `js/projets-ml.js`)
- [ ] Déposer `assets/pdf/CV_Francois_Lachance.pdf`
- [ ] Créer l'identifiant Formspree et remplacer `VOTRE_ID` dans `contact.html`
- [ ] Générer `assets/og-cover.png` (1200 × 630) et les icônes du manifeste
- [ ] Vérifier `config/feeds.json` avec `tracker check`
- [ ] Créer les cinq secrets GitHub Actions

Le détail, et les raisons, sont dans [`AUDIT.md`](AUDIT.md).