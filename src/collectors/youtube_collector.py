import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .types import (
    YouTubeSearchParams, RawYouTubeSearchResult, RawYouTubeVideoDetails,
    CollectionMetadata, CollectionResult, APIError
)
from ..config.settings import settings
from ..storage.schemas import VideoResult


class YouTubeCollector:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.base_delay = 1.0  # Base delay between requests
        self.max_retries = 3
        
        # YouTube API quota costs
        self.quota_costs = {
            'search': 100,  # search.list
            'videos': 1     # videos.list (per video)
        }
    
    def search(
        self, 
        keyword: str, 
        max_results: int = 40,
        region: str = "IN",
        days_back: Optional[int] = 365
    ) -> CollectionResult:
        started_at = datetime.now()
        errors = []
        warnings = []
        quota_used = 0
        
        try:
            # Prepare search parameters
            params = YouTubeSearchParams(
                q=keyword,
                regionCode=region,
                maxResults=min(50, max_results)  # API limit is 50 per request
            )
            
            # Add date filter if specified
            if days_back:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                params.publishedAfter = cutoff_date.isoformat() + "Z"
            
            # Step 1: Search for videos
            print(f"Searching YouTube for: {keyword}")
            search_results, search_quota = self._search_videos(params, max_results)
            quota_used += search_quota
            
            if not search_results:
                warnings.append("No search results found")
            
            # Step 2: Get detailed video information
            video_ids = [result.id.get('videoId') for result in search_results 
                        if result.id.get('kind') == 'youtube#video']
            
            video_details = []
            if video_ids:
                print(f"Fetching details for {len(video_ids)} videos")
                video_details, videos_quota = self._get_video_details(video_ids)
                quota_used += videos_quota
            
            # Create metadata
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            metadata = CollectionMetadata(
                keyword=keyword,
                platform="youtube",
                total_results=len(video_details),
                pages_fetched=1,  # YouTube search is typically single page for our use
                api_calls_made=2 if video_ids else 1,  # search + videos (if any videos)
                quota_used=quota_used,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                search_params=params,
                errors_encountered=errors,
                warnings=warnings
            )
            
            return CollectionResult(
                metadata=metadata,
                youtube_search_results=search_results,
                youtube_video_details=video_details
            )
            
        except Exception as e:
            # Critical error
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            error_msg = f"Critical error in YouTube search: {str(e)}"
            errors.append(error_msg)
            
            metadata = CollectionMetadata(
                keyword=keyword,
                platform="youtube",
                total_results=0,
                pages_fetched=0,
                api_calls_made=0,
                quota_used=quota_used,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                search_params=YouTubeSearchParams(q=keyword),
                errors_encountered=errors,
                warnings=warnings
            )
            
            return CollectionResult(
                metadata=metadata,
                youtube_search_results=[],
                youtube_video_details=[]
            )
    
    def _search_videos(
        self, 
        params: YouTubeSearchParams, 
        max_results: int
    ) -> tuple[List[RawYouTubeSearchResult], int]:
        try:
            # Prepare API request
            search_params = {
                'part': params.part,
                'q': params.q,
                'type': params.type,
                'order': params.order,
                'regionCode': params.regionCode,
                'maxResults': min(params.maxResults, max_results)
            }
            
            if params.publishedAfter:
                search_params['publishedAfter'] = params.publishedAfter
            
            # Make API call
            response = self.youtube.search().list(**search_params).execute()
            
            # Convert to our models
            search_results = []
            for item in response.get('items', []):
                try:
                    result = RawYouTubeSearchResult(
                        kind=item['kind'],
                        etag=item['etag'],
                        id=item['id'],
                        snippet=item['snippet']
                    )
                    search_results.append(result)
                except Exception as e:
                    print(f"Warning: Failed to parse search result: {e}")
                    continue
            
            quota_used = self.quota_costs['search']
            return search_results, quota_used
            
        except HttpError as e:
            raise Exception(f"YouTube API error: {e}")
    
    def _get_video_details(
        self, 
        video_ids: List[str]
    ) -> tuple[List[RawYouTubeVideoDetails], int]:
        if not video_ids:
            return [], 0
        
        try:
            # YouTube API allows up to 50 IDs per request
            batch_size = 50
            all_details = []
            total_quota = 0
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch_ids)
                ).execute()
                
                # Convert to our models
                for item in response.get('items', []):
                    try:
                        details = RawYouTubeVideoDetails(
                            kind=item['kind'],
                            etag=item['etag'],
                            id=item['id'],
                            snippet=item.get('snippet', {}),
                            statistics=item.get('statistics', {}),
                            contentDetails=item.get('contentDetails', {})
                        )
                        all_details.append(details)
                    except Exception as e:
                        print(f"Warning: Failed to parse video details: {e}")
                        continue
                
                # Calculate quota (1 unit per video)
                total_quota += len(batch_ids) * self.quota_costs['videos']
                
                # Rate limiting between batches
                if i + batch_size < len(video_ids):
                    time.sleep(self.base_delay)
            
            return all_details, total_quota
            
        except HttpError as e:
            raise Exception(f"YouTube API error in video details: {e}")
    
    def to_video_results(self, collection_result: CollectionResult) -> List[VideoResult]:
        video_results = []
        keyword = collection_result.metadata.keyword
        collected_at = collection_result.metadata.started_at
        
        # Create lookup for search results to preserve ranking
        search_lookup = {}
        for i, search_result in enumerate(collection_result.youtube_search_results):
            video_id = search_result.id.get('videoId')
            if video_id:
                search_lookup[video_id] = i + 1  # 1-based ranking
        
        for video_detail in collection_result.youtube_video_details:
            try:
                video_id = video_detail.id
                snippet = video_detail.snippet
                stats = video_detail.statistics
                content = video_detail.contentDetails
                
                # Get ranking from search results
                rank = search_lookup.get(video_id, 999)
                
                # Parse publish date
                published_at = self._parse_youtube_date(snippet.get('publishedAt', ''))
                
                # Create video result
                video_result = VideoResult(
                    video_id=video_id,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    title=snippet.get('title', ''),
                    description=snippet.get('description', ''),
                    channel_title=snippet.get('channelTitle', ''),
                    published_at=published_at,
                    duration=content.get('duration', ''),
                    views=int(stats.get('viewCount', 0)),
                    likes=int(stats.get('likeCount', 0)),
                    comments=int(stats.get('commentCount', 0)),
                    rank=rank,
                    keyword=keyword,
                    platform="youtube",
                    collected_at=collected_at
                )
                video_results.append(video_result)
                
            except Exception as e:
                print(f"Warning: Failed to convert video {video_detail.id}: {e}")
                continue
        
        # Sort by rank to maintain search order
        video_results.sort(key=lambda x: x.rank)
        
        return video_results
    
    def _parse_youtube_date(self, date_str: str) -> datetime:
        try:
            # YouTube returns dates like "2023-01-15T10:30:00Z"
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    def get_quota_status(self) -> Dict[str, Any]:
        # This is a simple estimate - YouTube doesn't provide real-time quota info
        return {
            'daily_limit': 10000,
            'estimated_used': 0,  # Would need to track this in a real implementation
            'search_cost': self.quota_costs['search'],
            'video_detail_cost': self.quota_costs['videos']
        }


class YouTubeBatchCollector:
    
    def __init__(self, api_key: Optional[str] = None):
        self.collector = YouTubeCollector(api_key)
        self.daily_quota_used = 0
        self.daily_quota_limit = 10000
    
    def search_multiple_keywords(
        self, 
        keywords: List[str], 
        max_results_per_keyword: int = 40
    ) -> Dict[str, CollectionResult]:
        results = {}
        
        for i, keyword in enumerate(keywords):
            print(f"Processing keyword {i+1}/{len(keywords)}: {keyword}")
            
            # Check quota before proceeding
            estimated_cost = 100 + max_results_per_keyword  # search + video details
            if self.daily_quota_used + estimated_cost > self.daily_quota_limit:
                print(f"Warning: Approaching daily quota limit. Skipping remaining keywords.")
                break
            
            try:
                result = self.collector.search(keyword, max_results_per_keyword)
                results[keyword] = result
                
                # Update quota tracking
                if result.metadata.quota_used:
                    self.daily_quota_used += result.metadata.quota_used
                
                # Rate limiting between keywords
                if i < len(keywords) - 1:
                    time.sleep(2.0)  # 2 second delay between keywords
                    
            except Exception as e:
                print(f"Error processing keyword '{keyword}': {e}")
                continue
        
        return results


# Global instances
youtube_collector = YouTubeCollector()
youtube_batch_collector = YouTubeBatchCollector()


# Convenience functions
def search_youtube(keyword: str, max_results: int = 40) -> List[VideoResult]:
    collection_result = youtube_collector.search(keyword, max_results)
    return youtube_collector.to_video_results(collection_result)


def search_youtube_batch(keywords: List[str], max_results_per_keyword: int = 40) -> Dict[str, List[VideoResult]]:
    collection_results = youtube_batch_collector.search_multiple_keywords(keywords, max_results_per_keyword)
    
    processed_results = {}
    for keyword, collection_result in collection_results.items():
        video_results = youtube_collector.to_video_results(collection_result)
        processed_results[keyword] = video_results
    
    return processed_results