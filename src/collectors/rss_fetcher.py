import feedparser
from datetime import datetime
import time

class RSSFetcher:
    def fetch(self, url):
        """
        Fetches an RSS feed and returns a list of items.
        """
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries:
                # Standardize the entry structure
                item = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', ''),
                    'description': entry.get('summary', entry.get('description', '')),
                    'date': self._parse_date(entry),
                    'raw_entry': entry  # Keep raw data just in case
                }
                items.append(item)
            return items
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    def _parse_date(self, entry):
        # Try to parse published date
        if hasattr(entry, 'published'):
            return entry.published
        elif hasattr(entry, 'updated'):
            return entry.updated
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
