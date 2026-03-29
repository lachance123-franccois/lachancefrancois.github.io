# 🎯 Academic Tracker - Research Command Center

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Système de veille académique automatisé pour Toulouse**  
*Tracking intelligent des logements CROUS, thèses et stages en Image/Signal/Télécom*

[Demo](#demo) • [Fonctionnalités](#fonctionnalités) • [Installation](#installation) • [Usage](#usage)

</div>

---

## 🌟 Aperçu

Academic Tracker est un système de veille automatisé ultra-performant qui surveille quotidiennement :

- 🏠 **Logements CROUS** à Toulouse (avec filtre de prix)
- 🎓 **Thèses de doctorat** en traitement d'images, vidéo, signal et télécommunications
- 💼 **Stages M2/Ingénieur** dans les mêmes domaines

Le système scrape automatiquement plusieurs sources académiques, filtre les offres pertinentes, les stocke en base de données et envoie des **notifications email quotidiennes** avec un design HTML premium.

## ✨ Fonctionnalités

### 🤖 Scraping Intelligent
- **Multi-sources** : ABG, theses.fr, ADUM, CROUS, sites des laboratoires toulousains
- **Filtrage par mots-clés** : Focus sur image, video, signal, télécommunications, ML/DL
- **Déduplication** : Suppression automatique des doublons
- **Cache intelligent** : Évite les re-scraping inutiles

### 📊 Base de Données SQLite
- Stockage structuré de toutes les offres
- Historique des scraping avec statistiques
- Système de marquage "nouveau/notifié"
- Nettoyage automatique des anciennes offres

### 📧 Notifications Email Premium
- Templates HTML ultra-stylés (design futuriste)
- Digest quotidien avec toutes les nouvelles offres
- Statistiques visuelles
- Liens directs vers les offres

### 🎨 Dashboard Web Spectaculaire
- Interface React avec design "Research Command Center"
- Animations fluides et effets visuels
- Statistiques en temps réel
- Navigation par onglets (Logements/Thèses/Stages)
- Responsive design

### ⚙️ Automatisation GitHub Actions
- **Exécution quotidienne** à 8h (configurable)
- Commit automatique des résultats
- Gestion des erreurs et logs détaillés
- Nettoyage hebdomadaire des anciennes données

## 📁 Architecture

```
academic-tracker/
├── backend/
│   ├── main.py                 # Orchestrateur principal
│   ├── crous_scraper.py        # Scraper logements CROUS
│   ├── phd_scraper.py          # Scraper thèses
│   ├── internship_scraper.py   # Scraper stages
│   ├── database.py             # Gestionnaire SQLite
│   └── email_notifier.py       # Système d'emails
├── frontend/
│   └── index.html              # Dashboard React
├── config/
│   └── config.json             # Configuration
├── .github/workflows/
│   └── daily-scrape.yml        # GitHub Actions
├── requirements.txt
└── README.md
```

## 🚀 Installation

### Prérequis

- Python 3.11+
- Un compte GitHub (pour l'automatisation)
- Un compte Gmail avec App Password (pour les emails)

### 1. Clone le repository

```bash
git clone https://github.com/votre-username/francois-tracker.git
cd francois-tracker
```

### 2. Installation des dépendances

```bash
pip install --break-system-packages -r requirements.txt
```

### 3. Configuration

Éditez `config/config.json` :

```json
{
  "email": {
    "enabled": true,
    "recipient": "votre-email@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "votre-email-envoi@gmail.com",
    "password": "votre-app-password-google"
  },
  "scraping": {
    "housing_max_price": 400,
    "enable_housing": true,
    "enable_phd": true,
    "enable_internship": true
  }
}
```

**⚠️ Important** : Pour Gmail, créez un **App Password** :
1. Allez dans les paramètres de sécurité Google
2. Activez la validation en 2 étapes
3. Créez un "App Password" pour "Mail"
4. Utilisez ce password dans la config

### 4. Configuration GitHub Actions (Automatisation)

Dans votre repository GitHub, ajoutez ces **Secrets** :
- `EMAIL_RECIPIENT` : Votre email de destination
- `EMAIL_SENDER` : Votre email Gmail
- `EMAIL_PASSWORD` : Votre App Password Gmail

Aller dans : Settings → Secrets and variables → Actions → New repository secret

## 📖 Usage

### Exécution manuelle

```bash
# Scraping complet avec notifications
cd backend
python main.py

# Scraping sans email
python main.py --no-email

# Afficher les statistiques uniquement
python main.py --stats

# Nettoyer les offres de plus de 90 jours
python main.py --cleanup 90
```

### Automatisation GitHub Actions

Une fois les secrets configurés, le workflow s'exécute **automatiquement tous les jours à 8h**.

Vous pouvez aussi le lancer manuellement :
1. Allez dans l'onglet "Actions" de votre repository
2. Sélectionnez "Academic Tracker - Daily Scraping"
3. Cliquez sur "Run workflow"

### Visualisation Web

Ouvrez `frontend/index.html` dans votre navigateur ou déployez-le sur GitHub Pages :

1. Activez GitHub Pages dans les settings
2. Sélectionnez la branche `main` et le dossier `/frontend`
3. Accédez à `https://votre-username.github.io/academic-tracker/`

## 🎨 Personnalisation

### Modifier les mots-clés de filtrage

Dans les scrapers (`phd_scraper.py`, `internship_scraper.py`), éditez :

```python
RELEVANT_KEYWORDS = [
    'vos', 'mots', 'clés', 'personnalisés'
]
```

### Changer le prix maximum des logements

Dans `config.json` :

```json
"housing_max_price": 700
```

### Adapter le design du dashboard

Éditez `frontend/index.html` - toutes les couleurs et styles sont dans le `<style>` tag.

Variables CSS principales :
```css
--primary: #00ff9d;      /* Couleur principale */
--secondary: #00b8ff;    /* Couleur secondaire */
--bg-dark: #0a0a0f;      /* Fond sombre */
```

## 📊 Statistiques et Monitoring

Le système log automatiquement :
- Nombre d'offres trouvées par scraping
- Nombre de nouvelles offres
- Durée d'exécution
- Erreurs éventuelles

Accédez aux stats via :

```bash
python main.py --stats
```

Exemple de sortie :
```
📊 System Statistics:
   Total housing offers: 24
   Total PhD offers: 18
   Total internship offers: 31
   Pending notifications: 8
```

## 🔧 Dépannage

### Les emails ne sont pas envoyés

1. Vérifiez que vous utilisez un **App Password**, pas votre mot de passe Gmail normal
2. Vérifiez que la validation en 2 étapes est activée
3. Testez la connexion SMTP manuellement

### Le scraping ne trouve rien

1. Les sites web peuvent changer leur structure HTML
2. Vérifiez les logs pour voir les erreurs spécifiques
3. Testez chaque scraper individuellement

### GitHub Actions échoue

1. Vérifiez que tous les Secrets sont correctement configurés
2. Regardez les logs détaillés dans l'onglet Actions
3. Testez en local d'abord

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Reporter des bugs
- Proposer des améliorations
- Ajouter de nouvelles sources de données
- Améliorer le design

## 📜 License

MIT License - Voir le fichier LICENSE pour plus de détails.

## 🙏 Crédits

Développé avec 💚 pour la communauté académique toulousaine.

**Technologies utilisées** :
- Python (requests, BeautifulSoup)
- SQLite
- React
- GitHub Actions
- HTML/CSS (design futuriste custom)

---

<div align="center">

**⭐ Si ce projet vous aide, n'oubliez pas de lui donner une étoile !**

Made with 🚀 by [Votre Nom]

</div>
