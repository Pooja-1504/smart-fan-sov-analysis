from typing import Dict, List, Any, Tuple
from collections import defaultdict
import pandas as pd
from datetime import datetime

from ..storage.schemas import SovSummary, PlatformSummary
from ..scoring.scoring import sov_calculator
from ..nlp.brand_lexicon import get_target_brand, get_all_brands


class CrossPlatformAnalyzer:

    def __init__(self):
        self.target_brand = get_target_brand()
        self.all_brands = get_all_brands()
    
    def aggregate_platform_results(
        self, 
        sov_summaries: List[SovSummary]
    ) -> Dict[str, PlatformSummary]:
       
        platform_data = defaultdict(list)
        
        # Group by platform
        for summary in sov_summaries:
            platform_data[summary.platform].append(summary)
        
        platform_summaries = {}
        
        for platform, summaries in platform_data.items():
            # Get unique keywords and brands
            keywords = sorted(list(set(s.keyword for s in summaries)))
            brands_found = len(set(s.brand for s in summaries))
            total_docs = len(summaries)  # Each summary represents brand mentions across docs
            
            # Create platform summary
            platform_summary = PlatformSummary(
                platform=platform,
                keywords_analyzed=keywords,
                brand_summaries=summaries,
                total_documents=total_docs,
                total_brands_found=brands_found
            )
            
            platform_summaries[platform] = platform_summary
        
        return platform_summaries
    
    def calculate_cross_platform_sov(
        self, 
        platform_summaries: Dict[str, PlatformSummary]
    ) -> Dict[str, Dict[str, float]]:
        
        brand_metrics = defaultdict(lambda: {
            'platforms': [],
            'total_sov': 0,
            'total_sopv': 0,
            'total_mentions': 0,
            'avg_sentiment': 0,
            'avg_rank': 0,
            'keyword_performance': defaultdict(list)
        })
        
        # Collect data from all platforms
        for platform, summary in platform_summaries.items():
            for brand_summary in summary.brand_summaries:
                brand = brand_summary.brand
                
                brand_metrics[brand]['platforms'].append(platform)
                brand_metrics[brand]['total_sov'] += brand_summary.share_of_voice
                brand_metrics[brand]['total_sopv'] += brand_summary.share_of_positive_voice
                brand_metrics[brand]['total_mentions'] += brand_summary.mention_count
                brand_metrics[brand]['avg_sentiment'] += brand_summary.average_sentiment
                brand_metrics[brand]['avg_rank'] += brand_summary.average_rank
                
                # Track per-keyword performance
                keyword = brand_summary.keyword
                brand_metrics[brand]['keyword_performance'][keyword].append({
                    'platform': platform,
                    'sov': brand_summary.share_of_voice,
                    'sopv': brand_summary.share_of_positive_voice,
                    'rank': brand_summary.average_rank
                })
        
        # Calculate averages
        final_metrics = {}
        for brand, metrics in brand_metrics.items():
            platform_count = len(set(metrics['platforms']))
            total_entries = len(metrics['platforms'])
            
            final_metrics[brand] = {
                'platforms_present': list(set(metrics['platforms'])),
                'platform_count': platform_count,
                'average_sov': metrics['total_sov'] / total_entries if total_entries > 0 else 0,
                'average_sopv': metrics['total_sopv'] / total_entries if total_entries > 0 else 0,
                'total_mentions': metrics['total_mentions'],
                'average_sentiment': metrics['avg_sentiment'] / total_entries if total_entries > 0 else 0,
                'average_rank': metrics['avg_rank'] / total_entries if total_entries > 0 else 0,
                'keyword_performance': dict(metrics['keyword_performance'])
            }
        
        return final_metrics
    
    def identify_platform_strengths(
        self, 
        cross_platform_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, Any]]:
       
        brand_platform_analysis = {}
        
        for brand, metrics in cross_platform_metrics.items():
            keyword_perf = metrics.get('keyword_performance', {})
            
            # Aggregate by platform across all keywords
            platform_performance = defaultdict(list)
            
            for keyword, keyword_data in keyword_perf.items():
                for entry in keyword_data:
                    platform = entry['platform']
                    platform_performance[platform].append({
                        'sov': entry['sov'],
                        'sopv': entry['sopv'],
                        'rank': entry['rank']
                    })
            
            # Calculate platform averages
            platform_averages = {}
            for platform, entries in platform_performance.items():
                if entries:
                    avg_sov = sum(e['sov'] for e in entries) / len(entries)
                    avg_sopv = sum(e['sopv'] for e in entries) / len(entries)
                    avg_rank = sum(e['rank'] for e in entries) / len(entries)
                    
                    platform_averages[platform] = {
                        'avg_sov': avg_sov,
                        'avg_sopv': avg_sopv,
                        'avg_rank': avg_rank,
                        'keyword_count': len(entries)
                    }
            
            # Identify best and worst platforms
            if platform_averages:
                best_platform = max(platform_averages.keys(), 
                                  key=lambda p: platform_averages[p]['avg_sov'])
                worst_platform = min(platform_averages.keys(), 
                                   key=lambda p: platform_averages[p]['avg_sov'])
                
                brand_platform_analysis[brand] = {
                    'platform_performance': platform_averages,
                    'best_platform': {
                        'name': best_platform,
                        'sov': platform_averages[best_platform]['avg_sov'],
                        'sopv': platform_averages[best_platform]['avg_sopv']
                    },
                    'worst_platform': {
                        'name': worst_platform,
                        'sov': platform_averages[worst_platform]['avg_sov'],
                        'sopv': platform_averages[worst_platform]['avg_sopv']
                    } if best_platform != worst_platform else None
                }
        
        return brand_platform_analysis


class KeywordAnalyzer:

    def __init__(self):
        self.target_brand = get_target_brand()
    
    def analyze_keyword_performance(
        self, 
        sov_summaries: List[SovSummary]
    ) -> Dict[str, Dict[str, Any]]:
        keyword_data = defaultdict(lambda: defaultdict(list))
        
        # Group by keyword and brand
        for summary in sov_summaries:
            keyword_data[summary.keyword][summary.brand].append(summary)
        
        keyword_analysis = {}
        
        for keyword, brand_data in keyword_data.items():
            # Calculate keyword-level metrics
            total_brands = len(brand_data)
            
            # Find target brand performance
            target_performance = None
            competitor_performance = []
            
            for brand, summaries in brand_data.items():
                # Average across platforms for this keyword
                avg_sov = sum(s.share_of_voice for s in summaries) / len(summaries)
                avg_sopv = sum(s.share_of_positive_voice for s in summaries) / len(summaries)
                avg_rank = sum(s.average_rank for s in summaries) / len(summaries)
                avg_sentiment = sum(s.average_sentiment for s in summaries) / len(summaries)
                
                performance = {
                    'brand': brand,
                    'avg_sov': avg_sov,
                    'avg_sopv': avg_sopv,
                    'avg_rank': avg_rank,
                    'avg_sentiment': avg_sentiment,
                    'platform_count': len(summaries)
                }
                
                if brand == self.target_brand:
                    target_performance = performance
                else:
                    competitor_performance.append(performance)
            
            # Sort competitors by SoV
            competitor_performance.sort(key=lambda x: x['avg_sov'], reverse=True)
            
            # Calculate keyword difficulty (how competitive it is)
            if competitor_performance:
                top_competitor_sov = competitor_performance[0]['avg_sov']
                avg_competitor_sov = sum(c['avg_sov'] for c in competitor_performance) / len(competitor_performance)
                keyword_difficulty = (top_competitor_sov + avg_competitor_sov) / 2
            else:
                keyword_difficulty = 0
            
            keyword_analysis[keyword] = {
                'total_brands': total_brands,
                'keyword_difficulty': keyword_difficulty,
                'target_performance': target_performance,
                'top_competitors': competitor_performance[:3],
                'market_leader': competitor_performance[0] if competitor_performance else None,
                'opportunity_score': self._calculate_opportunity_score(
                    target_performance, competitor_performance, keyword_difficulty
                )
            }
        
        return keyword_analysis
    
    def _calculate_opportunity_score(
        self, 
        target_performance: Dict[str, Any], 
        competitors: List[Dict[str, Any]], 
        difficulty: float
    ) -> float:
        if not target_performance or not competitors:
            return 50  # Neutral score
        
        target_sov = target_performance['avg_sov']
        target_rank = target_performance['avg_rank']
        
        # Factors that increase opportunity score:
        # 1. Low current performance (room for improvement)
        # 2. Good average rank (easier to improve)
        # 3. Lower keyword difficulty
        
        # Performance gap factor (0-40 points)
        max_competitor_sov = max(c['avg_sov'] for c in competitors) if competitors else 0
        performance_gap = max_competitor_sov - target_sov
        gap_score = min(40, performance_gap * 2)  # 20% gap = 40 points
        
        # Rank factor (0-30 points)
        rank_score = max(0, 30 - target_rank * 3)  # Rank 1 = 27 points, Rank 10 = 0 points
        
        # Difficulty factor (0-30 points)
        difficulty_score = max(0, 30 - difficulty * 0.6)  # Lower difficulty = higher score
        
        total_score = gap_score + rank_score + difficulty_score
        return min(100, max(0, total_score))
    
    def recommend_keyword_priorities(
        self, 
        keyword_analysis: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        for keyword, analysis in keyword_analysis.items():
            opportunity_score = analysis.get('opportunity_score', 0)
            target_perf = analysis.get('target_performance')
            
            if target_perf:
                priority = 'high' if opportunity_score > 70 else 'medium' if opportunity_score > 40 else 'low'
                
                recommendation = {
                    'keyword': keyword,
                    'opportunity_score': opportunity_score,
                    'priority': priority,
                    'current_sov': target_perf['avg_sov'],
                    'current_rank': target_perf['avg_rank'],
                    'difficulty': analysis.get('keyword_difficulty', 0),
                    'recommendation': self._generate_keyword_recommendation(keyword, analysis)
                }
                
                recommendations.append(recommendation)
        
        # Sort by opportunity score (descending)
        recommendations.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return recommendations
    
    def _generate_keyword_recommendation(
        self, 
        keyword: str, 
        analysis: Dict[str, Any]
    ) -> str:
        target_perf = analysis.get('target_performance', {})
        opportunity = analysis.get('opportunity_score', 0)
        difficulty = analysis.get('keyword_difficulty', 0)
        
        if opportunity > 70:
            return f"High opportunity keyword. Focus content creation and SEO efforts on '{keyword}'"
        elif opportunity > 40:
            return f"Moderate opportunity. Consider increasing content volume for '{keyword}'"
        elif target_perf.get('avg_rank', 10) > 5:
            return f"Improve search ranking for '{keyword}' through better SEO"
        else:
            return f"Maintain current position for '{keyword}' while focusing on higher-opportunity keywords"


# Global instances
cross_platform_analyzer = CrossPlatformAnalyzer()
keyword_analyzer = KeywordAnalyzer()


# Convenience functions
def analyze_cross_platform_performance(sov_summaries: List[SovSummary]) -> Dict[str, Any]:
    platform_summaries = cross_platform_analyzer.aggregate_platform_results(sov_summaries)
    cross_platform_metrics = cross_platform_analyzer.calculate_cross_platform_sov(platform_summaries)
    platform_strengths = cross_platform_analyzer.identify_platform_strengths(cross_platform_metrics)
    
    return {
        'platform_summaries': platform_summaries,
        'cross_platform_metrics': cross_platform_metrics,
        'platform_strengths': platform_strengths
    }


def analyze_keyword_opportunities(sov_summaries: List[SovSummary]) -> Dict[str, Any]:
    keyword_performance = keyword_analyzer.analyze_keyword_performance(sov_summaries)
    keyword_recommendations = keyword_analyzer.recommend_keyword_priorities(keyword_performance)
    
    return {
        'keyword_performance': keyword_performance,
        'keyword_recommendations': keyword_recommendations
    }