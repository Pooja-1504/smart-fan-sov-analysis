from typing import List, Dict, Tuple
from collections import defaultdict
import pandas as pd
from datetime import datetime

from .weights import WeightCalculator, calculate_percentiles
from ..storage.schemas import (
    EnrichedDocument, BrandMention, ScoredMention, 
    WeightComponents, SovSummary
)
from ..nlp.brand_lexicon import get_all_brands, get_target_brand


class SovCalculator:    
    def __init__(self):
        self.weight_calculator = WeightCalculator()
    
    def score_documents(
        self, 
        documents: List[EnrichedDocument],
        platform: str,
        keyword: str
    ) -> List[ScoredMention]:
        if not documents:
            return []
        
        # Calculate percentiles for engagement normalization
        percentiles = calculate_percentiles(documents, platform)
        self.weight_calculator.percentile_context = percentiles
        
        scored_mentions = []
        
        for document in documents:
            # Process each brand mentioned in this document
            for mention in document.brands_mentioned:
                try:
                    # Calculate all weight components
                    weights = self.weight_calculator.calculate_all_weights(
                        document, mention.brand, mention.count
                    )
                    
                    # Calculate total score
                    total_score = (
                        weights['rank_weight'] *
                        weights['engagement_weight'] *
                        weights['mention_weight'] *
                        weights['sentiment_weight']
                    )
                    
                    # Create weight components object
                    weight_components = WeightComponents(
                        rank_weight=weights['rank_weight'],
                        engagement_weight=weights['engagement_weight'],
                        mention_weight=weights['mention_weight'],
                        sentiment_weight=weights['sentiment_weight']
                    )
                    
                    # Create scored mention
                    scored_mention = ScoredMention(
                        document_id=document.id,
                        brand=mention.brand,
                        platform=platform,
                        keyword=keyword,
                        rank=document.rank,
                        mention_count=mention.count,
                        sentiment_score=document.sentiment_score,
                        engagement_raw=document.engagement_metrics,
                        weights=weight_components,
                        total_score=total_score
                    )
                    
                    scored_mentions.append(scored_mention)
                    
                except Exception as e:
                    print(f"Warning: Failed to score mention for {mention.brand} in document {document.id}: {e}")
                    continue
        
        return scored_mentions
    
    def calculate_sov(
        self, 
        scored_mentions: List[ScoredMention],
        platform: str,
        keyword: str
    ) -> List[SovSummary]:
        if not scored_mentions:
            return []
        
        # Group by brand
        brand_scores = defaultdict(list)
        for mention in scored_mentions:
            brand_scores[mention.brand].append(mention)
        
        # Calculate total score across all brands for normalization
        total_all_brands = sum(mention.total_score for mention in scored_mentions)
        
        # Calculate positive sentiment total (for SoPV)
        positive_mentions = [m for m in scored_mentions if m.sentiment_score > 0.2]
        total_positive = sum(mention.total_score for mention in positive_mentions)
        
        sov_summaries = []
        
        for brand, mentions in brand_scores.items():
            try:
                # Calculate brand totals
                brand_total_score = sum(m.total_score for m in mentions)
                brand_positive_mentions = [m for m in mentions if m.sentiment_score > 0.2]
                brand_positive_score = sum(m.total_score for m in brand_positive_mentions)
                
                # Calculate SoV and SoPV percentages
                share_of_voice = (brand_total_score / total_all_brands * 100) if total_all_brands > 0 else 0
                share_of_positive_voice = (brand_positive_score / total_positive * 100) if total_positive > 0 else 0
                
                # Calculate supporting metrics
                total_mentions = sum(m.mention_count for m in mentions)
                positive_mention_count = len(brand_positive_mentions)
                average_rank = sum(m.rank for m in mentions) / len(mentions)
                average_sentiment = sum(m.sentiment_score for m in mentions) / len(mentions)
                
                # Create summary
                sov_summary = SovSummary(
                    brand=brand,
                    platform=platform,
                    keyword=keyword,
                    total_score=brand_total_score,
                    share_of_voice=share_of_voice,
                    share_of_positive_voice=share_of_positive_voice,
                    mention_count=total_mentions,
                    positive_mentions=positive_mention_count,
                    average_rank=average_rank,
                    average_sentiment=average_sentiment
                )
                
                sov_summaries.append(sov_summary)
                
            except Exception as e:
                print(f"Warning: Failed to calculate SoV for {brand}: {e}")
                continue
        
        # Sort by Share of Voice (descending)
        sov_summaries.sort(key=lambda x: x.share_of_voice, reverse=True)
        
        return sov_summaries
    
    def calculate_cross_keyword_sov(
        self, 
        sov_summaries: List[SovSummary],
        platform: str
    ) -> Dict[str, Dict[str, float]]:
        if not sov_summaries:
            return {}
        
        # Group by brand
        brand_data = defaultdict(list)
        for summary in sov_summaries:
            if summary.platform == platform:
                brand_data[summary.brand].append(summary)
        
        aggregated_results = {}
        
        for brand, summaries in brand_data.items():
            # Calculate macro-averages (equal weight per keyword)
            avg_sov = sum(s.share_of_voice for s in summaries) / len(summaries)
            avg_sopv = sum(s.share_of_positive_voice for s in summaries) / len(summaries)
            avg_rank = sum(s.average_rank for s in summaries) / len(summaries)
            avg_sentiment = sum(s.average_sentiment for s in summaries) / len(summaries)
            
            # Sum totals
            total_mentions = sum(s.mention_count for s in summaries)
            total_positive_mentions = sum(s.positive_mentions for s in summaries)
            
            aggregated_results[brand] = {
                'average_sov': avg_sov,
                'average_sopv': avg_sopv,
                'average_rank': avg_rank,
                'average_sentiment': avg_sentiment,
                'total_mentions': total_mentions,
                'total_positive_mentions': total_positive_mentions,
                'keywords_count': len(summaries),
                'keywords': [s.keyword for s in summaries]
            }
        
        return aggregated_results


class CompetitiveAnalysis:
    
    def __init__(self):
        self.target_brand = get_target_brand()
        self.all_brands = get_all_brands()
    
    def analyze_competitive_position(
        self, 
        sov_summaries: List[SovSummary]
    ) -> Dict[str, any]:
        if not sov_summaries:
            return {}
        
        # Find target brand data
        target_data = None
        competitor_data = []
        
        for summary in sov_summaries:
            if summary.brand == self.target_brand:
                target_data = summary
            else:
                competitor_data.append(summary)
        
        if not target_data:
            return {'error': f'Target brand {self.target_brand} not found in results'}
        
        # Sort competitors by SoV
        competitor_data.sort(key=lambda x: x.share_of_voice, reverse=True)
        
        # Calculate insights
        total_brands = len(sov_summaries)
        target_rank = next((i + 1 for i, s in enumerate(sov_summaries) if s.brand == self.target_brand), total_brands)
        
        # Top competitors
        top_competitors = competitor_data[:3]
        
        # Calculate gaps
        sov_gap_to_leader = competitor_data[0].share_of_voice - target_data.share_of_voice if competitor_data else 0
        sopv_gap_to_leader = competitor_data[0].share_of_positive_voice - target_data.share_of_positive_voice if competitor_data else 0
        
        return {
            'target_brand': self.target_brand,
            'target_sov': target_data.share_of_voice,
            'target_sopv': target_data.share_of_positive_voice,
            'target_rank': target_rank,
            'total_brands': total_brands,
            'sov_gap_to_leader': sov_gap_to_leader,
            'sopv_gap_to_leader': sopv_gap_to_leader,
            'top_competitors': [
                {
                    'brand': comp.brand,
                    'sov': comp.share_of_voice,
                    'sopv': comp.share_of_positive_voice,
                    'avg_rank': comp.average_rank
                } for comp in top_competitors
            ],
            'sentiment_vs_competition': {
                'target_sentiment': target_data.average_sentiment,
                'competitor_avg_sentiment': sum(c.average_sentiment for c in competitor_data) / len(competitor_data) if competitor_data else 0
            }
        }
    
    def identify_opportunities(
        self, 
        cross_keyword_results: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, any]]:
        opportunities = []
        
        target_data = cross_keyword_results.get(self.target_brand, {})
        if not target_data:
            return opportunities
        
        # Opportunity 1: Keywords where target brand is underperforming
        target_keywords = target_data.get('keywords', [])
        low_performance_keywords = []
        
        # This would need keyword-level data to identify specific underperforming keywords
        # For now, provide general insights
        
        if target_data.get('average_sov', 0) < 20:
            opportunities.append({
                'type': 'low_overall_sov',
                'description': f'{self.target_brand} has low overall Share of Voice ({target_data.get("average_sov", 0):.1f}%)',
                'recommendation': 'Increase content creation and SEO efforts across all keywords',
                'priority': 'high'
            })
        
        if target_data.get('average_sopv', 0) < target_data.get('average_sov', 0) * 0.8:
            opportunities.append({
                'type': 'sentiment_gap',
                'description': f'Share of Positive Voice ({target_data.get("average_sopv", 0):.1f}%) is lower than overall SoV',
                'recommendation': 'Focus on improving brand sentiment through better customer experience and positive content',
                'priority': 'medium'
            })
        
        if target_data.get('average_rank', 100) > 5:
            opportunities.append({
                'type': 'poor_ranking',
                'description': f'Average search ranking is {target_data.get("average_rank", 0):.1f}',
                'recommendation': 'Improve SEO and search optimization to rank higher in results',
                'priority': 'high'
            })
        
        return opportunities


# Global instances
sov_calculator = SovCalculator()
competitive_analyzer = CompetitiveAnalysis()


# Convenience functions
def calculate_brand_sov(
    documents: List[EnrichedDocument], 
    platform: str, 
    keyword: str
) -> Tuple[List[ScoredMention], List[SovSummary]]:
    scored_mentions = sov_calculator.score_documents(documents, platform, keyword)
    sov_summaries = sov_calculator.calculate_sov(scored_mentions, platform, keyword)
    return scored_mentions, sov_summaries


def get_competitive_insights(sov_summaries: List[SovSummary]) -> Dict[str, any]:
    return competitive_analyzer.analyze_competitive_position(sov_summaries)