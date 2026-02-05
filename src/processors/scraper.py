import requests
from bs4 import BeautifulSoup
import logging
import re

class ContentFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_article_content(self, url):
        """
        Fetches and extracts the main text content from a URL.
        """
        try:
            logging.info(f"Fetching content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                element.extract()
            
            # Try to find the main article body
            article_body = soup.find('article')
            if not article_body:
                # Fallbacks for common classes
                article_body = soup.find(class_=re.compile(r'(content|article|post|story|body)'))
            
            if not article_body:
                article_body = soup.body

            if not article_body:
                return "Could not extract content."

            # Get text and clean it
            text = article_body.get_text(separator='\n')
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            # Join lines, preserving paragraphs (double newlines) but removing excessive spaces
            clean_text = '\n'.join(line for line in lines if line)
            
            if len(clean_text) < 100:
                 return "Content too short or extraction failed."

            return clean_text

        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return f"Error fetching content: {e}"
