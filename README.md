# 📧 SCRAPFORGE - Email Scraper

**SCRAPFORGE** est un outil intelligent de collecte d'adresses emails depuis le web. Il utilise DuckDuckGo (moins limitant que Google) pour rechercher des sites web pertinents et extrait automatiquement les adresses emails.

## ✨ Fonctionnalités

- 🔍 **Recherche intelligente** : Utilise l'API DuckDuckGo pour trouver des sites pertinents
- 📧 **Extraction d'emails** : Détecte automatiquement les adresses emails dans le contenu web
- 🎯 **Filtrage avancé** : Exclut les domaines indésirables et les emails de spam
- 🌐 **Page de contact** : Recherche automatiquement les pages de contact si aucun email n'est trouvé
- 💾 **Sauvegarde temps réel** : Sauvegarde immédiate de chaque email trouvé
- ⚡ **Timeout intelligent** : Évite les blocages sur les sites lents

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

**Dépendances requises :**
```
requests
beautifulsoup4
duckduckgo-search
argparse
```

## 📋 Utilisation

```bash
python main.py
```

- Entrer votre requête de recherche
- Définir le nombre maximum d'emails à collecter


## 📁 Fichiers de sortie

Le script génère deux fichiers :

1. **`emails.txt`** : Sauvegarde simple et continue
2. **`emails_YYYYMMDD_HHMMSS.txt`** : Fichier horodaté avec métadonnées


## ⚙️ Configuration

### Domaines exclus

Le script exclut automatiquement certains domaines pour éviter les résultats indésirables :

**Sites web exclus :**
- Moteurs de recherche (Google, Bing, Yahoo)
- Réseaux sociaux (Facebook, Twitter, LinkedIn)
- Annuaires génériques (Pages Jaunes, Kompass)
- Sites de voyage (Booking, TripAdvisor)

**Domaines d'emails exclus :**
- Domaines de test (example.com, test.fr)
- Emails automatiques (noreply, donotreply)

### Personnalisation

Vous pouvez modifier les listes d'exclusion dans le code :

```python
excluded_domains = [
    'google.com', 'facebook.com', 'twitter.com',
    # Ajoutez vos exclusions ici
]

excluded_email_domains = [
    'example.com', 'noreply.com',
    # Ajoutez vos exclusions ici
]
```

## 🛡️ Bonnes pratiques et légalité

### ⚠️ Important - Respect de la vie privée

- **Respectez le RGPD** : N'utilisez les emails collectés qu'avec le consentement des propriétaires
- **Pas de spam** : N'utilisez jamais les emails collectés pour du spam ou du marketing non sollicité
- **Vérifiez les CGU** : Respectez les conditions d'utilisation des sites web visités

Cet outil est fourni à des fins éducatives et professionnelles. L'utilisateur est entièrement responsable de l'usage qu'il en fait et doit s'assurer de respecter toutes les lois applicables, notamment en matière de protection des données personnelles (RGPD, CCPA, etc.).

---

**Développé par RDSV01** - Version 1.0

*Utilisez cet outil de manière responsable et éthique* 🚀
