# Watchdog de Sécurité IoT

Un outil de surveillance de sécurité sophistiqué conçu pour agréger, filtrer et organiser les actualités et les rapports de vulnérabilité liés à la sécurité de l'IoT (Internet des Objets). Cette application agit comme un "chien de garde" (watchdog), collectant des données provenant de diverses sources et utilisant le Traitement du Langage Naturel (NLP) pour séparer l'intelligence technique du bruit commercial.

## 🚀 Fonctionnalités

*   **Collecte Multi-Sources :**
    *   **Flux RSS :** Récupère automatiquement les articles de blogs de sécurité et de sites d'actualités configurés.
    *   **API Google Search :** Effectue une surveillance active à l'aide de requêtes de recherche dynamiques basées sur des mots-clés par catégorie.
*   **Filtrage Intelligent (NLP) :**
    *   Utilise **spaCy** pour l'analyse sémantique.
    *   Distingue le **contenu technique** (vulnérabilités, exploits, CVE) du **bruit commercial** (ventes, remises, marketing produit).
    *   Sépare automatiquement les articles rejetés dans un onglet spécifique "Filtré (Bruit)" pour révision.
*   **Interface Moderne :**
    *   Construite avec **CustomTkinter** pour une interface propre et sombre.
    *   Vue par onglets pour différentes couches de sécurité : *Capteurs & Appareils*, *Réseau & Transit*, *Destination & Stockage*.
*   **Persistance des Données :**
    *   Empêche les doublons.
    *   Exporte les données collectées au format JSON.

## 🛠 Prérequis

*   **Python 3.11** (Recommandé pour la compatibilité des bibliothèques).
*   **Clé API Google Cloud** & **ID Moteur de Recherche Personnalisé** (pour les fonctionnalités de recherche).

## 📦 Installation

Pour éviter les conflits de dépendances (spécifiquement avec spaCy et Pydantic), il est fortement recommandé d'utiliser un environnement virtuel avec Python 3.11.

1.  **Cloner le dépôt** (si applicable) ou naviguer vers le dossier du projet.

2.  **Créer un Environnement Virtuel :**
    ```powershell
    # Si vous avez le lanceur Python (py) installé :
    py -3.11 -m venv .venv
    
    # OU en utilisant la commande python standard (assurez-vous que c'est bien la version 3.11) :
    python -m venv .venv
    ```

3.  **Installer les Dépendances :**
    ```powershell
    # Activer l'environnement
    .\.venv\Scripts\Activate.ps1

    # Installer les paquets Python
    pip install -r requirements.txt

    # Télécharger le modèle de langue anglais pour spaCy
    python -m spacy download en_core_web_sm
    ```

## ⚙️ Configuration

### 1. Clés API (.env)
Vous devez fournir vos identifiants Google API pour que la fonctionnalité de recherche fonctionne.
Renommez le fichier `.env.example` en `.env` (ou créez-le) et ajoutez vos clés :

```ini
GOOGLE_API_KEY=votre_cle_api_ici
GOOGLE_CSE_ID=votre_id_cse_ici
```

### 2. Sources de surveillance (config/sources.yaml)
Vous pouvez personnaliser les flux RSS et les mots-clés surveillés en éditant `config/sources.yaml`. La structure est organisée par couches IoT :

```yaml
sources:
  sensors_devices:
    - name: "Nom de la Source"
      url: "https://rss.feed/url"
      keywords: ["firmware", "exploit"]
  # ... autres catégories
```

## ▶️ Utilisation

Lancez l'application en utilisant l'exécutable python de l'environnement virtuel :

```powershell
# Assurez-vous que votre environnement virtuel est actif
.\.venv\Scripts\python main.py
```

### Navigation dans l'interface
*   **Catégories :** Changez d'onglet pour voir les actualités spécifiques aux *Capteurs*, *Réseau*, ou *Cloud/Stockage*.
*   **Filtré (Bruit) :** Consultez cet onglet pour voir les articles que l'IA a identifiés comme commerciaux ou non pertinents (affichés en gris).
*   **Exporter :** Cliquez sur "Export to JSON" pour sauvegarder les résultats de la session actuelle.

## 📂 Structure du Projet

```
iot-security-watchdog/
├── config/             # Fichiers de configuration (settings.yaml, sources.yaml)
├── data/               # Stockage des éléments collectés (history.json)
├── src/                # Code source
│   ├── collectors/     # Logique de récupération RSS et API
│   ├── processors/     # Analyse de texte et logique NLP (spaCy)
│   ├── storage/        # Gestion des fichiers JSON
│   ├── ui/             # Implémentation de l'interface graphique CustomTkinter
│   └── utils/          # Planificateur (Scheduler) et coordination
├── main.py             # Point d'entrée
└── requirements.txt    # Dépendances du projet
```
