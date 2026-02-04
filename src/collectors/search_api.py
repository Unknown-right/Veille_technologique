import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class SearchAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')

    def search(self, query):
        """
        Uses Google Custom Search JSON API to find relevant articles.
        """
        if not self.api_key or not self.cse_id:
            print("Search API warning: Missing API Key or CSE ID in .env")
            return []
            
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Calculate date restriction (e.g., last 2 days to act like an alert)
        # Using 'd2' for last 2 days. This keeps results fresh.
        # q=query
        
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'dateRestrict': 'd2', 
            'sort': 'date'
        }

        try:
            print(f"Searching web for: {query}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._process_results(data)
        except Exception as e:
            print(f"Error searching Google API: {e}")
            return []

    def _process_results(self, data):
        items = []
        if 'items' not in data:
            return []

        for result in data['items']:
            item = {
                'title': result.get('title', 'No Title'),
                'link': result.get('link', ''),
                'description': result.get('snippet', ''),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # API doesn't always give clean dates, use fetch time
                'raw_entry': result
            }
            items.append(item)
        return items

