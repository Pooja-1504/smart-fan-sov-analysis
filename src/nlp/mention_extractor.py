import re
from typing import Dict, List, Tuple
from rapidfuzz import fuzz
from .brand_lexicon import brand_lexicon
from ..storage.schemas import BrandMention


class MentionExtractor:
    
    def __init__(self, fuzzy_threshold: float = 85.0):
        self.fuzzy_threshold = fuzzy_threshold
        self.brand_patterns = self._build_regex_patterns()
    
    def _build_regex_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {}
        
        for brand in brand_lexicon.get_all_brands():
            variants = brand_lexicon.get_brand_variants(brand)
            # Escape special regex characters and create word boundary pattern
            escaped_variants = [re.escape(variant) for variant in variants]
            pattern_str = r'\b(?:' + '|'.join(escaped_variants) + r')\b'
            patterns[brand] = re.compile(pattern_str, re.IGNORECASE)
        
        return patterns
    
    def extract_exact_mentions(self, text: str) -> Dict[str, int]:
        mentions = {}
        text_clean = self._clean_text(text)
        
        for brand, pattern in self.brand_patterns.items():
            # Skip if this would be a false positive
            if brand_lexicon.should_exclude(text_clean, brand):
                continue
            
            matches = pattern.findall(text_clean)
            if matches:
                mentions[brand] = len(matches)
        
        return mentions
    
    def extract_fuzzy_mentions(self, text: str) -> Dict[str, Tuple[int, float]]:
        mentions = {}
        words = self._extract_words(text)
        
        for brand in brand_lexicon.get_all_brands():
            variants = brand_lexicon.get_brand_variants(brand)
            best_matches = []
            
            for word in words:
                for variant in variants:
                    ratio = fuzz.ratio(word.lower(), variant)
                    if ratio >= self.fuzzy_threshold:
                        best_matches.append((word, ratio))
            
            if best_matches:
                # Count unique matches, use highest confidence
                unique_words = {}
                for word, ratio in best_matches:
                    if word not in unique_words or ratio > unique_words[word]:
                        unique_words[word] = ratio
                
                count = len(unique_words)
                avg_confidence = sum(unique_words.values()) / len(unique_words) / 100
                mentions[brand] = (count, avg_confidence)
        
        return mentions
    
    def extract_mentions(self, text: str, use_fuzzy: bool = True) -> List[BrandMention]:
        if not text or not text.strip():
            return []
        
        mentions = []
        
        # Start with exact matches
        exact_mentions = self.extract_exact_mentions(text)
        
        # Add fuzzy matches if enabled
        fuzzy_mentions = {}
        if use_fuzzy:
            fuzzy_mentions = self.extract_fuzzy_mentions(text)
        
        # Combine results, preferring exact matches
        all_brands = set(exact_mentions.keys()) | set(fuzzy_mentions.keys())
        
        for brand in all_brands:
            exact_count = exact_mentions.get(brand, 0)
            fuzzy_result = fuzzy_mentions.get(brand, (0, 0.0))
            fuzzy_count, fuzzy_confidence = fuzzy_result if isinstance(fuzzy_result, tuple) else (fuzzy_result, 1.0)
            
            # Use exact if available, otherwise fuzzy
            if exact_count > 0:
                mentions.append(BrandMention(
                    brand=brand,
                    count=exact_count,
                    confidence=1.0
                ))
            elif fuzzy_count > 0:
                mentions.append(BrandMention(
                    brand=brand,
                    count=fuzzy_count,
                    confidence=fuzzy_confidence
                ))
        
        return mentions
    
    def _clean_text(self, text: str) -> str:
        # Remove URLs, hashtags, mentions
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_words(self, text: str) -> List[str]:
        text_clean = self._clean_text(text)
        # Split on word boundaries, filter out short words
        words = re.findall(r'\b\w{3,}\b', text_clean)
        return words


# Global instance
mention_extractor = MentionExtractor()


# Convenience function
def extract_brand_mentions(text: str, use_fuzzy: bool = True) -> List[BrandMention]:
    return mention_extractor.extract_mentions(text, use_fuzzy)