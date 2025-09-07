import argparse
import sys
from datetime import datetime
from typing import List, Dict, Any
import json

from .collectors.google_collector import search_google
from .collectors.youtube_collector import search_youtube
from .nlp.mention_extractor import extract_brand_mentions
from .nlp.sentiment import analyze_sentiment
from .scoring.scoring import calculate_brand_sov
from .analytics.aggregate import analyze_cross_platform_performance, analyze_keyword_opportunities
from .analytics.insights import generate_marketing_insights
from .storage.io import (
    save_search_results, save_scored_mentions, save_sov_summary,
    DataIO, DataPaths
)
from .storage.schemas import EnrichedDocument, BrandMention
from .config.settings import settings


class SovAnalysisPipeline:
    
    def __init__(self):
        """Initialize the analysis pipeline."""
        self.results = {
            'raw_data': {},
            'enriched_documents': [],
            'scored_mentions': [],
            'sov_summaries': [],
            'insights': {}
        }
    
    def run_full_analysis(
        self, 
        keywords: List[str] = None,
        platforms: List[str] = None,
        max_results: int = None
    ) -> Dict[str, Any]:

        # Set defaults
        keywords = keywords or settings.PRIMARY_KEYWORDS
        platforms = platforms or ['google', 'youtube']
        max_results = max_results or settings.GOOGLE_RESULTS_COUNT
        
        print(f"Starting Share of Voice analysis...")
        print(f"Keywords: {keywords}")
        print(f"Platforms: {platforms}")
        print(f"Max results per keyword: {max_results}")
        
        # Step 1: Data Collection
        print("\nStep 1: Collecting data from search platforms...")
        self._collect_data(keywords, platforms, max_results)
        
        # Step 2: Data Enrichment
        print("\nStep 2: Enriching data with NLP analysis...")
        self._enrich_data()
        
        # Step 3: Scoring
        print("\nStep 3: Calculating Share of Voice scores...")
        self._calculate_scores()
        
        # Step 4: Analysis
        print("\nStep 4: Generating insights and recommendations...")
        self._generate_insights()
        
        # Step 5: Save Results
        print("\nStep 5: Saving results...")
        self._save_results()
        
        print("\nAnalysis complete!")
        return self.results
    
    def _collect_data(self, keywords: List[str], platforms: List[str], max_results: int):
        for platform in platforms:
            self.results['raw_data'][platform] = {}
            
            for keyword in keywords:
                print(f"  Collecting {platform} data for '{keyword}'...")
                
                try:
                    if platform == 'google':
                        search_results = search_google(keyword, max_results)
                        self.results['raw_data'][platform][keyword] = search_results
                        
                        # Save raw data
                        filepath = save_search_results(search_results, keyword, platform)
                        print(f"    Saved {len(search_results)} Google results to {filepath}")
                        
                    elif platform == 'youtube':
                        video_results = search_youtube(keyword, max_results)
                        self.results['raw_data'][platform][keyword] = video_results
                        
                        # Save raw data
                        filepath = save_search_results(video_results, keyword, platform)
                        print(f"    Saved {len(video_results)} YouTube results to {filepath}")
                        
                except Exception as e:
                    print(f"    Error collecting {platform} data for '{keyword}': {e}")
                    self.results['raw_data'][platform][keyword] = []
    
    def _enrich_data(self):
        enriched_docs = []
        
        for platform, platform_data in self.results['raw_data'].items():
            for keyword, results in platform_data.items():
                print(f"  Processing {platform} results for '{keyword}'...")
                
                for result in results:
                    try:
                        # Extract text content
                        if hasattr(result, 'title') and hasattr(result, 'snippet'):
                            # Google search result
                            text = f"{result.title} {result.snippet}"
                            engagement_metrics = {
                                'result_type': getattr(result, 'result_type', 'organic'),
                                'domain': result.domain
                            }
                        elif hasattr(result, 'title') and hasattr(result, 'description'):
                            # YouTube video result
                            text = f"{result.title} {result.description}"
                            engagement_metrics = {
                                'views': result.views,
                                'likes': result.likes,
                                'comments': result.comments,
                                'duration_seconds': self._parse_duration(getattr(result, 'duration', ''))
                            }
                        else:
                            continue
                        
                        # Extract brand mentions
                        brand_mentions = extract_brand_mentions(text, use_fuzzy=True)
                        
                        # Analyze sentiment
                        sentiment_score, sentiment_label = analyze_sentiment(text)
                        
                        # Create enriched document
                        enriched_doc = EnrichedDocument(
                            id=result.id if hasattr(result, 'id') else f"{platform}_{keyword}_{result.rank}",
                            platform=platform,
                            keyword=keyword,
                            rank=result.rank,
                            url=result.url,
                            title=result.title,
                            text=text,
                            brands_mentioned=brand_mentions,
                            sentiment_score=sentiment_score,
                            sentiment_label=sentiment_label,
                            engagement_metrics=engagement_metrics,
                            collected_at=result.collected_at
                        )
                        
                        enriched_docs.append(enriched_doc)
                        
                    except Exception as e:
                        print(f"    Warning: Failed to enrich result {getattr(result, 'rank', '?')}: {e}")
                        continue
        
        self.results['enriched_documents'] = enriched_docs
        print(f"  Enriched {len(enriched_docs)} documents")
    
    def _calculate_scores(self):
        all_scored_mentions = []
        all_sov_summaries = []
        
        # Group documents by platform and keyword
        platform_keyword_docs = {}
        for doc in self.results['enriched_documents']:
            key = (doc.platform, doc.keyword)
            if key not in platform_keyword_docs:
                platform_keyword_docs[key] = []
            platform_keyword_docs[key].append(doc)
        
        # Calculate SoV for each platform/keyword combination
        for (platform, keyword), docs in platform_keyword_docs.items():
            print(f"  Calculating SoV for {platform} / '{keyword}'...")
            
            try:
                scored_mentions, sov_summaries = calculate_brand_sov(docs, platform, keyword)
                all_scored_mentions.extend(scored_mentions)
                all_sov_summaries.extend(sov_summaries)
                
                print(f"    Found {len(scored_mentions)} scored mentions, {len(sov_summaries)} brand summaries")
                
            except Exception as e:
                print(f"    Error calculating SoV for {platform}/{keyword}: {e}")
        
        self.results['scored_mentions'] = all_scored_mentions
        self.results['sov_summaries'] = all_sov_summaries
        print(f"  Calculated scores for {len(all_sov_summaries)} brand/platform/keyword combinations")
    
    def _generate_insights(self):
        sov_summaries = self.results['sov_summaries']
        
        if not sov_summaries:
            print("  No SoV summaries available for analysis")
            return
        
        try:
            # Cross-platform analysis
            cross_platform_analysis = analyze_cross_platform_performance(sov_summaries)
            
            # Keyword analysis
            keyword_analysis = analyze_keyword_opportunities(sov_summaries)
            
            # Generate marketing insights
            marketing_insights = generate_marketing_insights(
                cross_platform_analysis, keyword_analysis
            )
            
            self.results['insights'] = {
                'cross_platform_analysis': cross_platform_analysis,
                'keyword_analysis': keyword_analysis,
                'marketing_insights': marketing_insights
            }
            
            print(f"  Generated comprehensive insights and recommendations")
            
        except Exception as e:
            print(f"   Error generating insights: {e}")
            self.results['insights'] = {}
    
    def _save_results(self):
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Save enriched documents
            enriched_path = DataPaths.enriched_documents(date_str)
            DataIO.save_models_to_csv(self.results['enriched_documents'], enriched_path)
            print(f"  Saved enriched documents to {enriched_path}")
            
            # Save scored mentions
            if self.results['scored_mentions']:
                scored_path = save_scored_mentions(self.results['scored_mentions'], date_str)
                print(f"  Saved scored mentions to {scored_path}")
            
            # Save SoV summaries
            if self.results['sov_summaries']:
                sov_path = save_sov_summary(self.results['sov_summaries'], date_str)
                print(f"  Saved SoV summaries to {sov_path}")
            
            # Save insights as JSON
            if self.results['insights']:
                insights_path = f"data/reports/insights_{date_str}.json"
                DataIO.save_json(self.results['insights'], insights_path)
                print(f"  Saved insights to {insights_path}")
                
        except Exception as e:
            print(f"  Error saving results: {e}")
    
    def _parse_duration(self, duration_str: str) -> int:
        try:
            # YouTube duration format: PT4M13S or PT1H2M30S
            if not duration_str.startswith('PT'):
                return 0
            
            duration_str = duration_str[2:]  # Remove 'PT'
            seconds = 0
            
            if 'H' in duration_str:
                hours, duration_str = duration_str.split('H')
                seconds += int(hours) * 3600
            
            if 'M' in duration_str:
                minutes, duration_str = duration_str.split('M')
                seconds += int(minutes) * 60
            
            if 'S' in duration_str:
                secs = duration_str.replace('S', '')
                if secs:
                    seconds += int(secs)
            
            return seconds
        except:
            return 0


def create_cli():
    parser = argparse.ArgumentParser(
        description="Share of Voice Analysis Tool for Smart Fan Market"
    )
    
    parser.add_argument(
        'command',
        choices=['analyze', 'collect', 'score', 'insights'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='Keywords to analyze (space-separated)'
    )
    
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['google', 'youtube'],
        default=['google', 'youtube'],
        help='Platforms to analyze'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        help='Maximum results per keyword per platform'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Check configuration and API keys'
    )
    
    return parser


def main():
    parser = create_cli()
    args = parser.parse_args()
    
    # Configuration check
    if args.config_check or not settings.validate():
        print("🔧 Configuration Check:")
        print(f"SerpAPI Key: {'Present' if settings.SERPAPI_API_KEY else ' Missing'}")
        print(f"YouTube API Key: {'Present' if settings.YOUTUBE_API_KEY else 'Missing'}")
        print(f"Target Brand: {settings.TARGET_BRAND}")
        print(f"Competitors: {settings.COMPETITOR_BRANDS}")
        print(f"Keywords: {settings.PRIMARY_KEYWORDS}")
        
        if not settings.validate():
            print("\nConfiguration invalid. Please check your .env file.")
            sys.exit(1)
        else:
            print("\n Configuration valid!")
            if args.config_check:
                sys.exit(0)
    
    # Initialize pipeline
    pipeline = SovAnalysisPipeline()
    
    try:
        if args.command == 'analyze':
            # Full analysis pipeline
            results = pipeline.run_full_analysis(
                keywords=args.keywords,
                platforms=args.platforms,
                max_results=args.max_results
            )
            
            # Print summary
            insights = results.get('insights', {})
            marketing_insights = insights.get('marketing_insights', {})
            exec_summary = marketing_insights.get('executive_summary', {})
            
            if exec_summary:
                print("\n" + "="*60)
                print(" EXECUTIVE SUMMARY")
                print("="*60)
                print(f"Target Brand: {exec_summary.get('target_brand', 'Unknown')}")
                print(f"Overall Share of Voice: {exec_summary.get('key_metrics', {}).get('overall_sov', 0):.1f}%")
                print(f"Share of Positive Voice: {exec_summary.get('key_metrics', {}).get('overall_sopv', 0):.1f}%")
                print(f"Average Search Rank: {exec_summary.get('key_metrics', {}).get('average_search_rank', 0):.1f}")
                print(f"Competitive Position: {exec_summary.get('key_metrics', {}).get('competitive_position', 'Unknown')}")
                
                print(f"\nTop Opportunities: {', '.join(exec_summary.get('top_opportunities', []))}")
                print(f"Best Platform: {exec_summary.get('best_platform', 'Unknown')}")
                
                print("\nKey Recommendations:")
                for i, rec in enumerate(exec_summary.get('key_recommendations', []), 1):
                    print(f"  {i}. {rec}")
            
        elif args.command == 'collect':
            print("Collection-only mode not implemented. Use 'analyze' for full pipeline.")
            
        elif args.command == 'score':
            print("Scoring-only mode not implemented. Use 'analyze' for full pipeline.")
            
        elif args.command == 'insights':
            print("Insights-only mode not implemented. Use 'analyze' for full pipeline.")
            
    except KeyboardInterrupt:
        print("\n\n Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error during analysis: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()