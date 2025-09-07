import math
from typing import Dict, Any, List
import numpy as np
from ..storage.schemas import EnrichedDocument


def rank_weight(rank: int) -> float:
    if rank <= 0:
        return 0.0
    
    # Logarithmic decay: w = 1 / log2(rank + 1)
    weight = 1.0 / math.log2(rank + 1)
    
    # Normalize to reasonable range (top result gets ~1.0, rank 10 gets ~0.3)
    return min(1.0, weight)


def engagement_weight_youtube(
    views: int, 
    likes: int, 
    comments: int,
    duration_seconds: int = 0,
    percentile_context: Dict[str, float] = None
) -> float:
    if not percentile_context:
        # Default percentiles if not provided
        percentile_context = {
            'views_p95': max(10000, views * 2),
            'interactions_p95': max(100, (likes + 2 * comments) * 2)
        }
    
    # Normalize metrics
    views_norm = min(1.5, views / percentile_context['views_p95'])
    
    # Weight comments more heavily (more engaged audience)
    interaction_score = likes + 2 * comments
    interaction_norm = min(1.5, interaction_score / percentile_context['interactions_p95'])
    
    # Combine with 70% views, 30% interactions
    base_weight = 0.7 * views_norm + 0.3 * interaction_norm
    
    # Bonus for longer videos (indicates more substantial content)
    duration_bonus = 1.0
    if duration_seconds > 0:
        # Slight bonus for videos > 3 minutes (more substantial content)
        if duration_seconds > 180:
            duration_bonus = 1.1
        # Small penalty for very short videos (likely low-quality)
        elif duration_seconds < 60:
            duration_bonus = 0.9
    
    # Ensure reasonable range
    final_weight = max(0.1, min(2.0, base_weight * duration_bonus))
    
    return final_weight


def engagement_weight_google(
    domain: str,
    result_type: str,
    snippet_length: int = 0,
    has_rich_snippet: bool = False
) -> float:
    base_weight = 1.0
    
    # Domain authority heuristics
    domain_lower = domain.lower()
    
    # High authority domains
    if any(site in domain_lower for site in [
        'youtube.com', 'amazon.', 'flipkart.', 'myntra.',
        'times', 'hindu', 'ndtv', 'news', 'wikipedia'
    ]):
        base_weight *= 1.2
    
    # Medium authority domains  
    elif any(site in domain_lower for site in [
        'quora.', 'reddit.', 'medium.', 'linkedin.'
    ]):
        base_weight *= 1.1
    
    # E-commerce sites (high engagement)
    elif any(shop in domain_lower for shop in [
        'shop', 'store', 'buy', 'price', 'review'
    ]):
        base_weight *= 1.15
    
    # Result type bonuses
    type_multipliers = {
        'video': 1.3,        # Videos typically have high engagement
        'product': 1.25,     # Product pages indicate purchase intent
        'news': 1.15,        # News articles get good engagement
        'rich_snippet': 1.2, # Rich snippets get more clicks
        'sitelinks': 1.1,    # Sitelinks indicate authority
        'organic': 1.0       # Baseline
    }
    
    base_weight *= type_multipliers.get(result_type, 1.0)
    
    # Rich snippet bonus
    if has_rich_snippet:
        base_weight *= 1.1
    
    # Snippet length bonus (longer = more informative)
    if snippet_length > 150:
        base_weight *= 1.05
    elif snippet_length < 50:
        base_weight *= 0.95
    
    # Keep in reasonable range
    return max(0.5, min(1.5, base_weight))


def mention_weight(mention_count: int) -> float:
    if mention_count <= 0:
        return 0.0
    
    # Logarithmic increase with diminishing returns
    # Base of 0.5, increases by 0.1 per mention, capped at 1.0
    weight = 0.5 + 0.1 * mention_count
    
    return min(1.0, weight)


def sentiment_weight(sentiment_score: float) -> float:
    # Map sentiment [-1, 1] to weight [0.3, 1.0]
    # Negative sentiment still counts but with reduced weight
    weight = 0.65 + 0.35 * sentiment_score
    
    # Ensure bounds
    return max(0.3, min(1.0, weight))


def calculate_percentiles(documents: List[EnrichedDocument], platform: str) -> Dict[str, float]:
    if not documents:
        return {}
    
    if platform == 'youtube':
        views = []
        interactions = []
        
        for doc in documents:
            metrics = doc.engagement_metrics
            views.append(metrics.get('views', 0))
            likes = metrics.get('likes', 0)
            comments = metrics.get('comments', 0)
            interactions.append(likes + 2 * comments)
        
        if views and interactions:
            return {
                'views_p95': np.percentile(views, 95) if views else 1000,
                'interactions_p95': np.percentile(interactions, 95) if interactions else 100
            }
    
    elif platform == 'google':
        snippet_lengths = []
        
        for doc in documents:
            snippet_lengths.append(len(doc.text))
        
        if snippet_lengths:
            return {
                'snippet_length_p95': np.percentile(snippet_lengths, 95)
            }
    
    return {}


class WeightCalculator:
    
    def __init__(self, percentile_context: Dict[str, float] = None):
        self.percentile_context = percentile_context or {}
    
    def calculate_all_weights(
        self, 
        document: EnrichedDocument,
        brand: str,
        mention_count: int
    ) -> Dict[str, float]:
        # Rank weight
        rank_w = rank_weight(document.rank)
        
        # Engagement weight (platform-specific)
        if document.platform == 'youtube':
            metrics = document.engagement_metrics
            eng_w = engagement_weight_youtube(
                views=metrics.get('views', 0),
                likes=metrics.get('likes', 0),
                comments=metrics.get('comments', 0),
                duration_seconds=metrics.get('duration_seconds', 0),
                percentile_context=self.percentile_context
            )
        else:  # Google
            eng_w = engagement_weight_google(
                domain=document.url.split('/')[2] if '/' in document.url else '',
                result_type=document.engagement_metrics.get('result_type', 'organic'),
                snippet_length=len(document.text),
                has_rich_snippet=document.engagement_metrics.get('has_rich_snippet', False)
            )
        
        # Mention weight
        mention_w = mention_weight(mention_count)
        
        # Sentiment weight
        sentiment_w = sentiment_weight(document.sentiment_score)
        
        return {
            'rank_weight': rank_w,
            'engagement_weight': eng_w,
            'mention_weight': mention_w,
            'sentiment_weight': sentiment_w
        }
    
    def calculate_total_score(
        self,
        document: EnrichedDocument,
        brand: str,
        mention_count: int
    ) -> float:
        weights = self.calculate_all_weights(document, brand, mention_count)
        
        # Multiply all weights together
        total_score = (
            weights['rank_weight'] *
            weights['engagement_weight'] *
            weights['mention_weight'] *
            weights['sentiment_weight']
        )
        
        return total_score


# Global instance
weight_calculator = WeightCalculator()


# Convenience functions
def calculate_document_score(document: EnrichedDocument, brand: str, mention_count: int) -> float:
    return weight_calculator.calculate_total_score(document, brand, mention_count)


def get_weight_breakdown(document: EnrichedDocument, brand: str, mention_count: int) -> Dict[str, float]:
    return weight_calculator.calculate_all_weights(document, brand, mention_count)