import time
import yaml
import threading
from src.collectors.rss_fetcher import RSSFetcher
from src.collectors.search_api import SearchAPI
from src.processors.analyzer import ContentAnalyzer

class WatchdogScheduler:
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.sources_config = self._load_sources()
        self.settings_config = self._load_settings()
        
        self.rss_fetcher = RSSFetcher()
        self.search_api = SearchAPI()
        self.analyzer = ContentAnalyzer(self.sources_config)
        self.seen_links = set() 

    def _load_sources(self):
        try:
            with open('config/sources.yaml', 'r') as f:
                data = yaml.safe_load(f)
                return data.get('sources', {})
        except Exception as e:
            print(f"Error loading sources: {e}")
            return {}

    def _load_settings(self):
        try:
            with open('config/settings.yaml', 'r') as f:
                data = yaml.safe_load(f)
                return data.get('app', {})
        except Exception:
            return {}

    def run_continuously(self):
        self.running = True
        interval = self.settings_config.get('refresh_interval_seconds', 1800)
        
        while self.running:
            print("Starting collection cycle...")
            self.collect_cycle()
            print(f"Cycle finished. Sleeping for {interval} seconds.")
            time.sleep(interval)

    def collect_cycle(self):
        # 1. PROCESS RSS FEEDS
        for category, sources in self.sources_config.items():
            for source in sources:
                url = source.get('url')
                source_name = source.get('name')
                
                print(f"Checking RSS: {source_name}...")
                items = self.rss_fetcher.fetch(url)
                self._process_items(items, source_name, category)

        # 2. PROCESS GOOGLE SEARCH (Active Monitoring)
        print("Checking Google Search API...")
        for category, sources in self.sources_config.items():
            # Gather all unique keywords for this category from the config
            all_keywords = set()
            for source in sources:
                if 'keywords' in source:
                    all_keywords.update(source['keywords'])
            
            if not all_keywords:
                continue

            # Construct a dynamic query: "IoT Security" AND (k1 OR k2 OR k3...)
            # Limit to top 5 keywords to stay within API limits and query length restrictions
            keywords_list = list(all_keywords)[:5]
            if not keywords_list:
                continue
                
            or_clause = " OR ".join([f'"{k}"' for k in keywords_list])
            query = f'"IoT Security" AND ({or_clause})'
                 
            search_results = self.search_api.search(query)
            self._process_items(search_results, "Google Search Watch", category)

    def _process_items(self, items, source_name, category_hint):
        for item in items:
            if item['link'] in self.seen_links:
                continue
            
            # Analyze
            # If it comes from search, we trust our query but still double check
            matched_category = self.analyzer.analyze(item, category_hint)
            
            # If analyzer returns a category, it passed the filter (keywords + NLP)
            if matched_category: 
                item['source'] = source_name
                item['category'] = matched_category
                item['status'] = 'accepted'
            else:
                 # Item rejected by analyzer (Noise/Commercial)
                 # We still send it to UI but with a special flag so it goes to "Filtered" tab
                 item['source'] = source_name
                 item['category'] = category_hint # Keep original hint so we know where it *would* have gone
                 item['status'] = 'rejected'

            self.seen_links.add(item['link'])
            self.callback(item)

    def stop(self):
        self.running = False
