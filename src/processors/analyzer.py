try:
    import spacy
except ImportError:
    spacy = None
except Exception as e:
    # Catch-all for Pydantic/Config errors on bleeding edge Python
    print(f"Warning: Failed to import spacy: {e}")
    spacy = None

from collections import Counter

class ContentAnalyzer:
    def __init__(self, sources_config):
        self.config = sources_config
        self.use_nlp = False
        
        if spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.use_nlp = True
            except OSError:
                print("Warning: spaCy model 'en_core_web_sm' not found. Semantic filtering disabled.")
                print("Run: python -m spacy download en_core_web_sm")
            except Exception as e:
                 print(f"Warning: Failed to load spaCy model: {e}")
                 self.use_nlp = False
        else:
             print("Warning: spaCy library not available. Semantic filtering disabled.")

    def analyze(self, item, source_category):
        """
        Analyzes an item to see if it matches the category keywords.
        Uses NLP to filter out commercial noise if available.
        Returns the category if matched, or None.
        """
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        content = f"{title} {description}"

        # 1. First, basic keyword relevance check (Fast filter)
        category_config = self.config.get(source_category, [])
        keywords = set()
        for source_def in category_config:
            for kw in source_def.get('keywords', []):
                keywords.add(kw.lower())

        keyword_match = False
        for kw in keywords:
            if kw in content:
                item['matched_keyword'] = kw
                keyword_match = True
                break
        
        if not keyword_match:
            return None

        # 2. Semantic Filtering (Noise Reduction)
        # If we have NLP, ensure it's not just a sales pitch
        if self.use_nlp:
            if not self._is_technical_content(content):
                print(f"Filtered out as commercial/non-technical: {item.get('title')}")
                return None

        item['category'] = source_category
        return source_category

    def _is_technical_content(self, text):
        """
        Heuristic scoring to differentiate technical security content from marketing/shopping.
        """
        doc = self.nlp(text)
        
        # Lemmatize tokens to handle plurals/forms (e.g., "vulnerabilities" -> "vulnerability")
        tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct]
        
        technical_terms = {
            'vulnerability', 'exploit', 'cve', 'patch', 'firmware', 'backdoor', 
            'remote', 'execution', 'buffer', 'overflow', 'injection', 'xss', 
            'zero-day', 'malware', 'ransomware', 'attack', 'breach', 'protocol',
            'mqtt', 'tcp', 'udp', 'http', 'api', 'iot', 'security', 'botnet'
        }
        
        commercial_terms = {
            'buy', 'price', 'discount', 'sale', 'offer', 'deal', 'shop', 'store', 
            'subscription', 'coupon', 'limited', 'shipping', 'black friday', 
            'cyber monday', 'best', 'top', 'review', 'rating'
        }

        tech_score = 0
        commercial_score = 0

        for token in tokens:
            if token in technical_terms:
                tech_score += 1
            elif token in commercial_terms:
                commercial_score += 1

        # Logic: 
        # 1. If commercial score is high (>2) and tech score is low, reject.
        # 2. If it has high tech score, we tolerate some commercial words (e.g. "security product").
        
        if commercial_score > 2 and tech_score < 2:
            return False
            
        return True

