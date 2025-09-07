import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from serpapi import GoogleSearch

from .types import (
    GoogleSearchParams, RawGoogleResult, CollectionMetadata, 
    CollectionResult, APIError
)
from ..config.settings import settings
from ..storage.schemas import SearchResult


class GoogleCollector:    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key."""
        self.api_key = api_key or settings.SERPAPI_API_KEY
        if not self.api_key:
            raise ValueError("SerpAPI key is required")
        
        self.base_delay = 1.0  # Base delay between requests
        self.max_retries = 3
    
    def search(
        self, 
        keyword: str, 
        max_results: int = 30,
        region: str = "in",
        language: str = "en"
    ) -> CollectionResult:
        started_at = datetime.now()
        errors = []
        warnings = []
        
        try:
            # Calculate how many pages we need
            results_per_page = 10
            pages_needed = (max_results + results_per_page - 1) // results_per_page
            
            all_results = []
            api_calls = 0
            
            for page in range(pages_needed):
                start_index = page * results_per_page
                remaining_results = max_results - len(all_results)
                
                if remaining_results <= 0:
                    break
                
                # Prepare search parameters
                params = GoogleSearchParams(
                    q=keyword,
                    gl=region,
                    hl=language,
                    num=min(results_per_page, remaining_results),
                    start=start_index
                )
                
                # Make API call
                try:
                    page_results = self._fetch_page(params)
                    all_results.extend(page_results)
                    api_calls += 1
                    
                    # Rate limiting
                    if page < pages_needed - 1:  # Don't delay after last page
                        time.sleep(self.base_delay)
                        
                except Exception as e:
                    error_msg = f"Failed to fetch page {page + 1}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Warning: {error_msg}")
                    
                    # Continue with next page unless it's a critical error
                    if "quota" in str(e).lower() or "forbidden" in str(e).lower():
                        break
            
            # Create metadata
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            metadata = CollectionMetadata(
                keyword=keyword,
                platform="google",
                total_results=len(all_results),
                pages_fetched=min(api_calls, pages_needed),
                api_calls_made=api_calls,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                search_params=params,
                errors_encountered=errors,
                warnings=warnings
            )
            
            return CollectionResult(
                metadata=metadata,
                google_results=all_results
            )
            
        except Exception as e:
            # Critical error
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            error_msg = f"Critical error in Google search: {str(e)}"
            errors.append(error_msg)
            
            metadata = CollectionMetadata(
                keyword=keyword,
                platform="google",
                total_results=0,
                pages_fetched=0,
                api_calls_made=0,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                search_params=GoogleSearchParams(q=keyword),
                errors_encountered=errors,
                warnings=warnings
            )
            
            return CollectionResult(
                metadata=metadata,
                google_results=[]
            )
    
    def _fetch_page(self, params: GoogleSearchParams) -> List[RawGoogleResult]:
        search_params = {
            "engine": "google",
            "api_key": self.api_key,
            **params.model_dump()
        }
        
        search = GoogleSearch(search_params)
        result = search.get_dict()
        
        # Check for errors
        if "error" in result:
            raise Exception(f"SerpAPI error: {result['error']}")
        
        # Extract organic results
        organic_results = result.get("organic_results", [])
        
        raw_results = []
        for i, item in enumerate(organic_results):
            try:
                raw_result = RawGoogleResult(
                    position=item.get("position", params.start + i + 1),
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    displayed_link=item.get("displayed_link", ""),
                    source=item.get("source", ""),
                    sitelinks=item.get("sitelinks"),
                    rich_snippet=item.get("rich_snippet"),
                    thumbnail=item.get("thumbnail"),
                    cached_page_link=item.get("cached_page_link")
                )
                raw_results.append(raw_result)
            except Exception as e:
                print(f"Warning: Failed to parse result {i}: {e}")
                continue
        
        return raw_results
    
    def to_search_results(self, collection_result: CollectionResult) -> List[SearchResult]:
        search_results = []
        keyword = collection_result.metadata.keyword
        collected_at = collection_result.metadata.started_at
        
        for raw_result in collection_result.google_results:
            try:
                # Extract domain from link
                domain = self._extract_domain(raw_result.link)
                
                # Determine result type
                result_type = self._classify_result_type(raw_result)
                
                search_result = SearchResult(
                    id=f"google_{keyword}_{raw_result.position}_{int(collected_at.timestamp())}",
                    url=raw_result.link,
                    title=raw_result.title,
                    snippet=raw_result.snippet,
                    domain=domain,
                    rank=raw_result.position,
                    keyword=keyword,
                    platform="google",
                    result_type=result_type,
                    collected_at=collected_at
                )
                search_results.append(search_result)
            except Exception as e:
                print(f"Warning: Failed to convert result {raw_result.position}: {e}")
                continue
        
        return search_results
    
    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return ""
    
    def _classify_result_type(self, raw_result: RawGoogleResult) -> str:
        # Check for rich snippets or special result types
        if raw_result.rich_snippet:
            return "rich_snippet"
        
        # Check URL patterns
        url_lower = raw_result.link.lower()
        if "youtube.com" in url_lower:
            return "video"
        elif any(shop in url_lower for shop in ["amazon", "flipkart", "myntra", "shopify"]):
            return "product"
        elif any(news in url_lower for news in ["news", "times", "hindu", "indian", "ndtv"]):
            return "news"
        elif raw_result.sitelinks:
            return "sitelinks"
        else:
            return "organic"


# Global instance
google_collector = GoogleCollector()


# Convenience function
def search_google(keyword: str, max_results: int = 30) -> List[SearchResult]:
    collection_result = google_collector.search(keyword, max_results)
    return google_collector.to_search_results(collection_result)