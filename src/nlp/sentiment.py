from typing import Tuple, Optional
import re
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Ensure VADER lexicon is available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    print("Downloading VADER lexicon...")
    nltk.download('vader_lexicon', quiet=True)


class SentimentAnalyzer:
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Custom adjustments for fan/appliance domain
        self.domain_adjustments = {
            # Positive indicators
            'energy saving': 0.3,
            'energy efficient': 0.3,
            'quiet': 0.2,
            'silent': 0.2,
            'powerful': 0.2,
            'stylish': 0.2,
            'premium': 0.2,
            'remote control': 0.1,
            'smart': 0.1,
            'iot': 0.1,
            'wifi': 0.1,
            'alexa': 0.1,
            'best': 0.3,
            'excellent': 0.4,
            'amazing': 0.4,
            'love': 0.3,
            'recommend': 0.3,
            
            # Negative indicators
            'noisy': -0.3,
            'loud': -0.3,
            'cheap': -0.2,
            'plastic': -0.1,
            'slow': -0.2,
            'weak': -0.3,
            'poor quality': -0.4,
            'waste': -0.3,
            'regret': -0.4,
            'disappointed': -0.3,
            'defective': -0.4,
            'broken': -0.3,
            'faulty': -0.4,
        }
    
    def analyze(self, text: str) -> Tuple[float, str]:
        if not text or not text.strip():
            return 0.0, 'neutral'
        
        # Clean text
        clean_text = self._preprocess_text(text)
        
        # Get VADER scores
        scores = self.analyzer.polarity_scores(clean_text)
        base_score = scores['compound']
        
        # Apply domain-specific adjustments
        domain_adjustment = self._calculate_domain_adjustment(clean_text)
        final_score = base_score + domain_adjustment
        
        # Clamp to [-1, 1] range
        final_score = max(-1.0, min(1.0, final_score))
        
        # Determine label
        label = self._score_to_label(final_score)
        
        return final_score, label
    
    def _preprocess_text(self, text: str) -> str:
        # Convert to lowercase for consistency
        text = text.lower()
        
        # Handle negations better
        text = re.sub(r'\bnot\s+', 'not_', text)
        text = re.sub(r'\bno\s+', 'no_', text)
        text = re.sub(r'\bnever\s+', 'never_', text)
        
        # Handle brand mentions in context
        text = re.sub(r'\bvs\b', ' versus ', text)
        text = re.sub(r'\bv/s\b', ' versus ', text)
        
        # Normalize punctuation
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        
        return text
    
    def _calculate_domain_adjustment(self, text: str) -> float:
        adjustment = 0.0
        text_lower = text.lower()
        
        for phrase, weight in self.domain_adjustments.items():
            if phrase in text_lower:
                adjustment += weight
        
        # Normalize adjustment to reasonable range
        return max(-0.3, min(0.3, adjustment))
    
    def _score_to_label(self, score: float) -> str:
        if score >= 0.1:
            return 'positive'
        elif score <= -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_with_confidence(self, text: str) -> Tuple[float, str, float]:
        if not text or not text.strip():
            return 0.0, 'neutral', 0.0
        
        clean_text = self._preprocess_text(text)
        scores = self.analyzer.polarity_scores(clean_text)
        
        # Calculate confidence based on score magnitude and text length
        base_score = scores['compound']
        confidence = abs(base_score)
        
        # Adjust confidence based on text length (longer text = more reliable)
        word_count = len(clean_text.split())
        length_factor = min(1.0, word_count / 10.0)  # Normalize to 10 words
        confidence = confidence * (0.5 + 0.5 * length_factor)
        
        # Apply domain adjustment
        domain_adjustment = self._calculate_domain_adjustment(clean_text)
        final_score = base_score + domain_adjustment
        final_score = max(-1.0, min(1.0, final_score))
        
        label = self._score_to_label(final_score)
        
        return final_score, label, confidence


class BrandSpecificSentiment:
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
    
    def analyze_brand_sentiment(self, text: str, brand: str) -> Tuple[float, str]:
        if not text or not brand:
            return 0.0, 'neutral'
        
        # Find sentences containing the brand
        brand_sentences = self._extract_brand_sentences(text, brand)
        
        if not brand_sentences:
            # Fallback to overall text sentiment
            return self.analyzer.analyze(text)
        
        # Analyze sentiment of brand-specific sentences
        scores = []
        for sentence in brand_sentences:
            score, _ = self.analyzer.analyze(sentence)
            scores.append(score)
        
        # Average the scores
        avg_score = sum(scores) / len(scores)
        label = self.analyzer._score_to_label(avg_score)
        
        return avg_score, label
    
    def _extract_brand_sentences(self, text: str, brand: str) -> list:
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        brand_sentences = []
        brand_lower = brand.lower()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and brand_lower in sentence.lower():
                brand_sentences.append(sentence)
        
        return brand_sentences


# Global instances
sentiment_analyzer = SentimentAnalyzer()
brand_sentiment_analyzer = BrandSpecificSentiment()


# Convenience functions
def analyze_sentiment(text: str) -> Tuple[float, str]:
    return sentiment_analyzer.analyze(text)


def analyze_brand_sentiment(text: str, brand: str) -> Tuple[float, str]:
    return brand_sentiment_analyzer.analyze_brand_sentiment(text, brand)


def get_sentiment_score(text: str) -> float:
    score, _ = sentiment_analyzer.analyze(text)
    return score


def get_sentiment_label(text: str) -> str:
    _, label = sentiment_analyzer.analyze(text)
    return label