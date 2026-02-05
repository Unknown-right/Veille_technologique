import time
import yaml
import threading
from src.collectors.rss_fetcher import RSSFetcher
from src.collectors.search_api import SearchAPI
from src.processors.analyzer import ContentAnalyzer
from src.processors.scraper import ContentFetcher
from src.processors.reporter import GeminiReporter

class WatchdogScheduler:
    def __init__(self, callback, report_callback=None):
        self.callback = callback
        self.report_callback = report_callback
        self.running = False
        
        # Load full config first
        self._full_config = self._load_full_config()
        self.sources_config = self._full_config.get('sources', {})
        self.search_watch_list = self._full_config.get('search_watch_list', [])
        
        self.settings_config = self._load_settings()
        
        self.rss_fetcher = RSSFetcher()
        self.search_api = SearchAPI()
        self.analyzer = ContentAnalyzer(self.sources_config)
        self.content_fetcher = ContentFetcher()
        self.reporter = GeminiReporter()
        self.seen_links = set() 
        self.current_cycle_accepted = []

    def _load_full_config(self):
        try:
            with open('config/sources.yaml', 'r') as f:
                data = yaml.safe_load(f)
                return data if data else {}
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
        interval = self.settings_config.get('refresh_interval_seconds', 3600)
        
        last_search_time = 0
        search_interval = 3600 # 1 hour for Google Search to save quota # USER REQUESTED: 3600s check
        
        while self.running:
            print("Starting collection cycle...")
            current_time = time.time()
            
            # Determine if we should run Google Search this cycle
            run_search = (current_time - last_search_time) >= search_interval
            
            self.collect_cycle(run_search=run_search)
            
            if run_search:
                last_search_time = current_time
            
            print(f"Cycle finished. Sleeping for {interval} seconds.")
            time.sleep(interval)

    def collect_cycle(self, run_search=False):
        self.current_cycle_accepted = [] # Reset for this cycle

        # 1. PROCESS RSS FEEDS
        for category, sources in self.sources_config.items():
            # Standard RSS processing
            for source in sources:
                url = source.get('url')
                source_name = source.get('name')
                
                print(f"Checking RSS: {source_name}...")
                items = self.rss_fetcher.fetch(url)
                self._process_items(items, source_name, category)

        # 2. PROCESS GOOGLE SEARCH (Active Monitoring)
        if run_search:
            print("Checking Google Search API (Specific Watch List)...")
            
            if not self.search_watch_list:
                print("  No 'search_watch_list' defined in config. Skipping search.")
            
            for query in self.search_watch_list:
                # We use a generic category mostly for UI grouping
                print(f"  Searching web for: {query}")
                search_results = self.search_api.search(query)
                self._process_items(search_results, "Google Search Watch", "network_transit")

        # 3. GENERATE REPORT (Gemini)
        if self.report_callback and self.current_cycle_accepted:
            print("Generating Gemini Report...")
            report_text = self.reporter.generate_digest(self.current_cycle_accepted)
            self.report_callback(report_text)

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
                
                # SCRAPE FULL CONTENT (Feature Request: "Récupérer directement les articles")
                print(f"  Fetching full content for: {item.get('title', 'Unknown')}...")
                full_text = self.content_fetcher.fetch_article_content(item['link'])
                item['content'] = full_text
                
                self.current_cycle_accepted.append(item)
            else:
                 # Item rejected by analyzer (Noise/Commercial)
                 # We still send it to UI but with a special flag so it goes to "Filtered" tab
                 item['source'] = source_name
                 item['category'] = category_hint # Keep original hint so we know where it *would* have gone
                 item['status'] = 'rejected'
                 item['content'] = "Content not fetched for filtered items."

            self.seen_links.add(item['link'])
            self.callback(item)

    def stop(self):
        self.running = False
