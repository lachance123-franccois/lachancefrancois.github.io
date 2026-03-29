# 🚀 Guide de Démarrage Rapide

## Installation en 5 minutes

### 1. Prérequis
- Python 3.11+
- Compte GitHub
- Compte Gmail avec App Password

### 2. Installation

```bash
# Clone le projet
git clone https://github.com/votre-username/academic-tracker.git
cd academic-tracker

# Install dependencies
pip install --break-system-packages -r requirements.txt
```

### 3. Configuration Email (Gmail)

**Créer un App Password Gmail** :
1. Allez sur https://myaccount.google.com/security
2. Activez "Validation en 2 étapes"
3. Recherchez "Mots de passe des applications"
4. Créez un password pour "Mail"
5. Copiez le password généré (16 caractères)

**Éditez config/config.json** :
```json
{
  "email": {
    "enabled": true,
    "recipient": "votre-email@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "votre-gmail@gmail.com",
    "password": "xxxx xxxx xxxx xxxx"  ← Votre App Password
  }
}
```

### 4. Test Local

```bash
# Test rapide (sans email)
python test.py

# Premier scraping complet
cd backend
python main.py
```

### 5. Automatisation GitHub Actions

**Dans votre repository GitHub** :
1. Settings → Secrets and variables → Actions
2. Ajoutez 3 secrets :
   - `EMAIL_RECIPIENT` : votre-email@example.com
   - `EMAIL_SENDER` : votre-gmail@gmail.com
   - `EMAIL_PASSWORD` : votre-app-password

**Le workflow s'exécutera automatiquement tous les jours à 8h !**

### 6. Dashboard Web

**Option A - Local** :
Ouvrez `frontend/index.html` dans votre navigateur

**Option B - GitHub Pages** :
1. Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /frontend
4. Accédez à : `https://votre-username.github.io/academic-tracker/`

## 🎯 Commandes Utiles

```bash
# Scraping avec notifications
python backend/main.py

# Scraping sans email
python backend/main.py --no-email

# Voir les statistiques
python backend/main.py --stats

# Nettoyer les vieilles données
python backend/main.py --cleanup 90

# Lancer manuellement le workflow GitHub
# → Aller dans Actions → Run workflow
```

## 📧 Format des Emails

Vous recevrez chaque jour un email avec :
- 📊 Statistiques globales
- 🏠 Nouveaux logements CROUS
- 🎓 Nouvelles thèses de doctorat
- 💼 Nouveaux stages

Design premium avec :
- Interface futuriste
- Filtrage par mots-clés
- Liens directs vers les offres
- Keywords highlights

## 🔧 Personnalisation

### Changer le prix max des logements
```json
"housing_max_price": 700
```

### Modifier l'heure d'exécution
`.github/workflows/daily-scrape.yml` :
```yaml
cron: '0 7 * * *'  # 8h Paris (UTC+1)
```

### Ajouter des mots-clés
`backend/phd_scraper.py` et `internship_scraper.py` :
```python
KEYWORDS = [
    'vos-mots-clés-personnalisés'
]
```

## ❓ Problèmes Fréquents

### ❌ "Authentication failed" (Gmail)
→ Utilisez un **App Password**, pas votre mot de passe normal !

### ❌ "No module named 'requests'"
```bash
pip install --break-system-packages -r requirements.txt
```

### ❌ GitHub Actions échoue
→ Vérifiez que les 3 Secrets sont correctement configurés

### ❌ Aucune offre trouvée
→ Normal au début ! Les offres s'accumulent avec le temps

## 🎉 C'est Prêt !

Votre système de veille est maintenant actif. Vous recevrez :
- ✉️ Un email quotidien avec les nouvelles offres
- 📊 Des statistiques mises à jour
- 🗄️ Un historique complet en base de données

**Conseil** : Gardez un œil sur votre boîte mail chaque matin !

---

🚀 **Besoin d'aide ?** Consultez le README.md complet ou ouvrez une issue sur GitHub.
