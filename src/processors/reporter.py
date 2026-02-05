import google.generativeai as genai
import os
import logging
from datetime import datetime

class GeminiReporter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Fallback to 'gemini-1.5-flash' via the latest alias which is usually more stable/accessible
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                logging.info("Gemini Reporter initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini: {e}")
        else:
            logging.warning("GEMINI_API_KEY not set. Reporting feature will be disabled.")

    def generate_digest(self, articles):
        """
        Generates a summary report for a list of articles.
        """
        if not self.model:
            return "Gemini API Key is missing. Please add GEMINI_API_KEY to your .env file."

        if not articles:
            return "No articles provided for the report."

        # Filter out articles without content
        valid_articles = [a for a in articles if a.get('content') and len(a.get('content')) > 200]
        
        if not valid_articles:
            return "No articles with sufficient content found to generate a report."

        logging.info(f"Generating report for {len(valid_articles)} articles...")

        # Construct the prompt
        context = ""
        for i, art in enumerate(valid_articles):
            # Truncate content to avoid token limits (though 1.5 Flash is generous)
            # 5000 chars is roughly 1-2 pages of text.
            content_snippet = art['content'][:5000] 
            context += f"""
---
ARTICLE {i+1}
Title: {art.get('title', 'Unknown')}
Source: {art.get('source', 'Unknown')}
Date: {art.get('published', 'Unknown')}
Content:
{content_snippet}
---
"""

        prompt = f"""
Tu es un expert analyste en cybersécurité spécialisé dans l'IoT (Internet des Objets) et la protection des données.
Ta mission est de créer un "Rapport de Veille Sécurité IoT" quotidien basé sur les articles fournis.

Le rapport doit être rédigé **en Français**, au format Markdown, et inclure :
1. **Synthèse Exécutive** : Un bref aperçu des tendances clés ou menaces critiques du jour, avec un focus particulier sur la **sécurité des données IoT**.
2. **Menaces Critiques** : Mets en évidence les vulnérabilités les plus importantes ou les attaques mentionnées.
3. **Tendances Émergentes** : Modèles d'attaques, nouvelles technologies ou stratégies de défense.
4. **Conseils Pratiques** : Recommandations spécifiques pour les administrateurs IT ou les utilisateurs.
5. **Résumés des Articles** : Une phrase clé pour chaque article pertinent.

Si les articles contiennent du "bruit" ou des informations commerciales non pertinentes, ignore-les. Concentre-toi sur l'impact technique et la sécurité.

ARTICLES À ANALYSER :
{context}
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini generation error: {e}")
            return f"An error occurred while generating the report with Gemini: {e}"
