from typing import Dict, List, Any, Tuple
from datetime import datetime
import statistics

from ..storage.schemas import SovSummary
from ..nlp.brand_lexicon import get_target_brand, get_competitor_brands


class InsightGenerator:
    
    def __init__(self):
        self.target_brand = get_target_brand()
        self.competitors = get_competitor_brands()
    
    def generate_executive_summary(
        self, 
        cross_platform_analysis: Dict[str, Any],
        keyword_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        cross_platform_metrics = cross_platform_analysis.get('cross_platform_metrics', {})
        target_metrics = cross_platform_metrics.get(self.target_brand, {})
        
        # Key performance indicators
        overall_sov = target_metrics.get('average_sov', 0)
        overall_sopv = target_metrics.get('average_sopv', 0)
        avg_rank = target_metrics.get('average_rank', 0)
        total_mentions = target_metrics.get('total_mentions', 0)
        
        # Competitive position
        brand_rankings = self._calculate_brand_rankings(cross_platform_metrics)
        target_position = brand_rankings.get('position', len(cross_platform_metrics))
        
        # Platform performance
        platform_strengths = cross_platform_analysis.get('platform_strengths', {})
        target_platform_perf = platform_strengths.get(self.target_brand, {})
        
        # Keyword opportunities
        keyword_recs = keyword_analysis.get('keyword_recommendations', [])
        high_priority_keywords = [k for k in keyword_recs if k.get('priority') == 'high']
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'target_brand': self.target_brand,
            'key_metrics': {
                'overall_sov': round(overall_sov, 1),
                'overall_sopv': round(overall_sopv, 1),
                'average_search_rank': round(avg_rank, 1),
                'total_brand_mentions': total_mentions,
                'competitive_position': f"{target_position} of {len(cross_platform_metrics)} brands"
            },
            'performance_summary': self._generate_performance_summary(
                overall_sov, overall_sopv, avg_rank, target_position
            ),
            'top_opportunities': [k['keyword'] for k in high_priority_keywords[:3]],
            'best_platform': target_platform_perf.get('best_platform', {}).get('name', 'Unknown'),
            'key_recommendations': self._generate_key_recommendations(
                target_metrics, platform_strengths, keyword_recs, 
                cross_platform_analysis.get('cross_platform_metrics', {}).get(self.target_brand, {})
            )
        }
    
    def generate_content_recommendations(
        self, 
        keyword_analysis: Dict[str, Any],
        platform_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Keyword-based content recommendations
        keyword_performance = keyword_analysis.get('keyword_performance', {})
        keyword_recs = keyword_analysis.get('keyword_recommendations', [])
        
        for keyword_rec in keyword_recs[:5]:  # Top 5 opportunities
            keyword = keyword_rec['keyword']
            keyword_data = keyword_performance.get(keyword, {})
            
            content_rec = self._generate_keyword_content_strategy(
                keyword, keyword_rec, keyword_data
            )
            recommendations.append(content_rec)
        
        # Platform-specific recommendations
        platform_strengths = platform_analysis.get('platform_strengths', {})
        target_platform_data = platform_strengths.get(self.target_brand, {})
        
        if target_platform_data:
            platform_rec = self._generate_platform_content_strategy(target_platform_data)
            recommendations.extend(platform_rec)
        
        return recommendations
    
    def generate_seo_recommendations(
        self, 
        keyword_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        seo_recommendations = []
        keyword_performance = keyword_analysis.get('keyword_performance', {})
        
        for keyword, data in keyword_performance.items():
            target_perf = data.get('target_performance')
            if not target_perf:
                continue
            
            current_rank = target_perf.get('avg_rank', 10)
            current_sov = target_perf.get('avg_sov', 0)
            
            if current_rank > 5:  # Not in top 5
                seo_recommendations.append({
                    'type': 'ranking_improvement',
                    'keyword': keyword,
                    'current_rank': current_rank,
                    'target_rank': min(3, current_rank - 2),
                    'priority': 'high' if current_rank > 8 else 'medium',
                    'recommendations': [
                        f"Optimize page titles and meta descriptions for '{keyword}'",
                        f"Create high-quality content targeting '{keyword}'",
                        f"Build backlinks from authoritative sites in the fan/appliance industry",
                        f"Improve page load speed and mobile optimization"
                    ]
                })
            
            elif current_sov < 15:  # Low share of voice despite good ranking
                seo_recommendations.append({
                    'type': 'content_optimization',
                    'keyword': keyword,
                    'current_sov': current_sov,
                    'priority': 'medium',
                    'recommendations': [
                        f"Expand content depth for '{keyword}' to increase relevance",
                        f"Add FAQ sections addressing common questions about {keyword}",
                        f"Include user-generated content and reviews",
                        f"Optimize for featured snippets and rich results"
                    ]
                })
        
        return seo_recommendations
    
    def generate_competitive_strategy(
        self, 
        cross_platform_analysis: Dict[str, Any],
        keyword_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        cross_platform_metrics = cross_platform_analysis.get('cross_platform_metrics', {})
        
        # Identify main competitors
        competitor_metrics = {
            brand: metrics for brand, metrics in cross_platform_metrics.items()
            if brand != self.target_brand
        }
        
        # Sort by average SoV
        top_competitors = sorted(
            competitor_metrics.items(),
            key=lambda x: x[1].get('average_sov', 0),
            reverse=True
        )[:3]
        
        # Analyze competitive gaps
        target_metrics = cross_platform_metrics.get(self.target_brand, {})
        competitive_analysis = []
        
        for competitor, metrics in top_competitors:
            gap_analysis = self._analyze_competitor_gap(
                target_metrics, metrics, competitor, keyword_analysis
            )
            competitive_analysis.append(gap_analysis)
        
        return {
            'target_brand': self.target_brand,
            'main_competitors': [comp[0] for comp in top_competitors],
            'competitive_gaps': competitive_analysis,
            'strategic_recommendations': self._generate_competitive_strategies(
                target_metrics, top_competitors, keyword_analysis
            )
        }
    
    def _generate_performance_summary(
        self, 
        sov: float, 
        sopv: float, 
        avg_rank: float, 
        position: int
    ) -> str:
        """Generate human-readable performance summary."""
        if sov >= 30:
            sov_status = "strong"
        elif sov >= 15:
            sov_status = "moderate"
        else:
            sov_status = "low"
        
        if sopv >= sov * 0.9:
            sentiment_status = "positive sentiment is strong"
        elif sopv >= sov * 0.7:
            sentiment_status = "sentiment is generally positive"
        else:
            sentiment_status = "sentiment needs improvement"
        
        rank_status = "excellent" if avg_rank <= 3 else "good" if avg_rank <= 5 else "needs improvement"
        
        return f"{self.target_brand} has {sov_status} Share of Voice ({sov:.1f}%) and {sentiment_status} ({sopv:.1f}% positive SoV). Search ranking is {rank_status} (avg rank {avg_rank:.1f}). Currently ranked #{position} among competitors."
    
    def _generate_key_recommendations(
        self, 
        target_metrics: Dict[str, Any],
        platform_strengths: Dict[str, Any],
        keyword_recs: List[Dict[str, Any]],
        platform_data: Dict[str, Any] = None
    ) -> List[str]:
        recommendations = []
        
        target_platform_data = platform_strengths.get(self.target_brand, {})
        avg_sov = target_metrics.get('average_sov', 0)
        avg_sopv = target_metrics.get('average_sopv', 0)
        avg_rank = target_metrics.get('average_rank', 0)
        
        # Platform-specific recommendations
        platform_recs = self._generate_platform_specific_recommendations(
            platform_data, target_metrics
        )
        recommendations.extend(platform_recs)
        
        # SoV improvement
        if avg_sov < 20:
            recommendations.append(
                "Increase content creation and marketing efforts to improve overall Share of Voice"
            )
        
        # Sentiment improvement
        if avg_sopv < avg_sov * 0.8:
            recommendations.append(
                "Focus on improving brand sentiment through customer experience and positive content"
            )
        
        # Platform optimization
        if target_platform_data.get('best_platform'):
            best_platform = target_platform_data['best_platform']['name']
            recommendations.append(
                f"Double down on {best_platform} where you perform best"
            )
        
        # Keyword opportunities
        high_priority = [k for k in keyword_recs if k.get('priority') == 'high']
        if high_priority:
            top_keyword = high_priority[0]['keyword']
            recommendations.append(
                f"Prioritize content creation for high-opportunity keyword: '{top_keyword}'"
            )
        
        # SEO improvement
        if avg_rank > 5:
            recommendations.append(
                "Improve SEO to achieve higher search rankings across key terms"
            )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_platform_specific_recommendations(
        self, 
        platform_data: Dict[str, Any],
        target_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate platform-specific recommendations based on performance data"""
        recommendations = []
        
        if not platform_data:
            return recommendations
            
        # Extract platform performance from keyword_performance
        keyword_performance = platform_data.get('keyword_performance', {})
        platforms_present = platform_data.get('platforms_present', [])
        
        platform_metrics = {}
        
        # Aggregate platform performance across keywords
        for keyword, performances in keyword_performance.items():
            for perf in performances:
                platform = perf['platform']
                if platform not in platform_metrics:
                    platform_metrics[platform] = {
                        'sov_scores': [],
                        'ranks': [],
                        'total_mentions': 0
                    }
                platform_metrics[platform]['sov_scores'].append(perf['sov'])
                platform_metrics[platform]['ranks'].append(perf['rank'])
        
        # Calculate averages for each platform
        for platform in platform_metrics:
            scores = platform_metrics[platform]['sov_scores']
            ranks = platform_metrics[platform]['ranks']
            platform_metrics[platform]['avg_sov'] = sum(scores) / len(scores) if scores else 0
            platform_metrics[platform]['avg_rank'] = sum(ranks) / len(ranks) if ranks else 0
        
        # Generate Google-specific recommendations
        if 'google' in platform_metrics:
            google_data = platform_metrics['google']
            google_sov = google_data['avg_sov']
            google_rank = google_data['avg_rank']
            
            if google_rank > 3:
                recommendations.append(
                    " Google SEO: Optimize website content and technical SEO to improve search rankings"
                )
            elif google_sov < 25:
                recommendations.append(
                    " Google Content: Create more comprehensive, authoritative content to capture more search traffic"
                )
            else:
                recommendations.append(
                    " Google Advantage: Leverage your strong Google presence with more branded content"
                )
        
        # Generate YouTube-specific recommendations  
        if 'youtube' in platform_metrics:
            youtube_data = platform_metrics['youtube']
            youtube_sov = youtube_data['avg_sov']
            youtube_rank = youtube_data['avg_rank']
            
            if youtube_sov < 30:
                recommendations.append(
                    " YouTube Growth: Increase video content production and optimize for YouTube SEO"
                )
            elif youtube_rank > 5:
                recommendations.append(
                    " YouTube Ranking: Focus on better video titles, descriptions, and engagement to improve rankings"
                )
            else:
                recommendations.append(
                    " YouTube Success: Scale your successful YouTube strategy with more frequent uploads and series"
                )
        
        # Cross-platform insights
        if len(platform_metrics) > 1:
            google_sov = platform_metrics.get('google', {}).get('avg_sov', 0)
            youtube_sov = platform_metrics.get('youtube', {}).get('avg_sov', 0)
            
            if google_sov > youtube_sov + 15:
                recommendations.append(
                    " Cross-platform: Promote your strong web presence through YouTube video content"
                )
            elif youtube_sov > google_sov + 15:
                recommendations.append(
                    " Cross-platform: Drive YouTube traffic to your website for better search presence"
                )
            else:
                recommendations.append(
                    " Balanced Strategy: Maintain consistent messaging across both Google and YouTube channels"
                )
        
        # Platform gap analysis
        if 'google' not in platforms_present:
            recommendations.append(
                " Missing Platform: Consider expanding to Google Ads and SEO to capture search traffic"
            )
        if 'youtube' not in platforms_present:
            recommendations.append(
                " Missing Platform: Develop video content strategy for YouTube to reach visual learners"
            )
        
        return recommendations
    
    def _generate_keyword_content_strategy(
        self, 
        keyword: str, 
        keyword_rec: Dict[str, Any],
        keyword_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        priority = keyword_rec.get('priority', 'medium')
        opportunity_score = keyword_rec.get('opportunity_score', 0)
        current_rank = keyword_rec.get('current_rank', 10)
        
        # Content type recommendations based on keyword
        content_types = []
        if 'smart' in keyword.lower():
            content_types.extend(['product demos', 'IoT integration guides', 'smart home content'])
        if 'energy' in keyword.lower():
            content_types.extend(['efficiency comparisons', 'cost savings calculators', 'eco-friendly content'])
        if 'best' in keyword.lower():
            content_types.extend(['comparison reviews', 'buying guides', 'expert recommendations'])
        
        if not content_types:
            content_types = ['product reviews', 'how-to guides', 'feature explanations']
        
        return {
            'keyword': keyword,
            'priority': priority,
            'opportunity_score': opportunity_score,
            'current_rank': current_rank,
            'content_types': content_types[:3],
            'recommended_actions': [
                f"Create 2-3 high-quality pieces of content targeting '{keyword}'",
                f"Optimize existing content to better target '{keyword}'",
                f"Consider paid promotion for '{keyword}' content"
            ]
        }
    
    def _generate_platform_content_strategy(
        self, 
        platform_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        strategies = []
        
        best_platform_info = platform_data.get('best_platform', {})
        worst_platform_info = platform_data.get('worst_platform', {})
        
        if best_platform_info:
            best_platform = best_platform_info['name']
            strategies.append({
                'type': 'platform_optimization',
                'platform': best_platform,
                'recommendation': f"Increase content volume on {best_platform} where you perform best",
                'priority': 'high',
                'actions': [
                    f"Create more {best_platform}-specific content",
                    f"Increase posting frequency on {best_platform}",
                    f"Engage more actively with {best_platform} community"
                ]
            })
        
        if worst_platform_info:
            worst_platform = worst_platform_info['name']
            strategies.append({
                'type': 'platform_improvement',
                'platform': worst_platform,
                'recommendation': f"Improve content strategy for {worst_platform}",
                'priority': 'medium',
                'actions': [
                    f"Analyze competitor content on {worst_platform}",
                    f"Adapt content format for {worst_platform} audience",
                    f"Consider influencer partnerships on {worst_platform}"
                ]
            })
        
        return strategies
    
    def _analyze_competitor_gap(
        self, 
        target_metrics: Dict[str, Any],
        competitor_metrics: Dict[str, Any],
        competitor_name: str,
        keyword_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
    
        sov_gap = competitor_metrics.get('average_sov', 0) - target_metrics.get('average_sov', 0)
        sopv_gap = competitor_metrics.get('average_sopv', 0) - target_metrics.get('average_sopv', 0)
        rank_gap = target_metrics.get('average_rank', 10) - competitor_metrics.get('average_rank', 10)
        
        # Find keywords where competitor dominates
        keyword_performance = keyword_analysis.get('keyword_performance', {})
        competitor_strong_keywords = []
        
        for keyword, data in keyword_performance.items():
            target_perf = data.get('target_performance', {})
            competitors = data.get('top_competitors', [])
            
            competitor_perf = next(
                (c for c in competitors if c['brand'] == competitor_name), None
            )
            
            if competitor_perf and target_perf:
                if competitor_perf['avg_sov'] > target_perf['avg_sov'] + 10:
                    competitor_strong_keywords.append({
                        'keyword': keyword,
                        'competitor_sov': competitor_perf['avg_sov'],
                        'target_sov': target_perf['avg_sov'],
                        'gap': competitor_perf['avg_sov'] - target_perf['avg_sov']
                    })
        
        return {
            'competitor': competitor_name,
            'sov_gap': round(sov_gap, 1),
            'sopv_gap': round(sopv_gap, 1),
            'rank_advantage': round(rank_gap, 1),  # Positive = we rank better
            'competitor_strong_keywords': sorted(
                competitor_strong_keywords, 
                key=lambda x: x['gap'], 
                reverse=True
            )[:3]
        }
    
    def _generate_competitive_strategies(
        self, 
        target_metrics: Dict[str, Any],
        top_competitors: List[Tuple[str, Dict[str, Any]]],
        keyword_analysis: Dict[str, Any]
    ) -> List[str]:
        strategies = []
        
        if top_competitors:
            leader = top_competitors[0]
            leader_sov = leader[1].get('average_sov', 0)
            target_sov = target_metrics.get('average_sov', 0)
            
            if leader_sov > target_sov + 15:
                strategies.append(
                    f"Close the gap with market leader {leader[0]} by focusing on their successful keywords and content formats"
                )
        
        # Find common competitor strengths
        keyword_performance = keyword_analysis.get('keyword_performance', {})
        competitor_dominated_keywords = []
        
        for keyword, data in keyword_performance.items():
            market_leader = data.get('market_leader', {})
            if market_leader and market_leader.get('avg_sov', 0) > 25:
                competitor_dominated_keywords.append(keyword)
        
        if competitor_dominated_keywords:
            strategies.append(
                f"Target competitor-dominated keywords: {', '.join(competitor_dominated_keywords[:3])}"
            )
        
        strategies.append(
            "Monitor competitor content strategies and identify content gaps to exploit"
        )
        
        return strategies

    def _calculate_brand_rankings(self, cross_platform_metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    
        brand_sov = {
            brand: metrics.get('average_sov', 0) 
            for brand, metrics in cross_platform_metrics.items()
        }
        
        sorted_brands = sorted(brand_sov.items(), key=lambda x: x[1], reverse=True)
        
        target_position = next(
            (i + 1 for i, (brand, _) in enumerate(sorted_brands) if brand == self.target_brand),
            len(sorted_brands)
        )
        
        return {
            'rankings': sorted_brands,
            'position': target_position,
            'total_brands': len(sorted_brands)
        }


# Global instance
insight_generator = InsightGenerator()


# Convenience functions
def generate_marketing_insights(
    cross_platform_analysis: Dict[str, Any],
    keyword_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        'executive_summary': insight_generator.generate_executive_summary(
            cross_platform_analysis, keyword_analysis
        ),
        'content_recommendations': insight_generator.generate_content_recommendations(
            keyword_analysis, cross_platform_analysis
        ),
        'seo_recommendations': insight_generator.generate_seo_recommendations(
            keyword_analysis
        ),
        'competitive_strategy': insight_generator.generate_competitive_strategy(
            cross_platform_analysis, keyword_analysis
        )
    }