from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class GoogleSearchParams(BaseModel):
    q: str = Field(..., description="Search query")
    gl: str = Field(default="in", description="Geolocation (country)")
    hl: str = Field(default="en", description="Interface language")
    num: int = Field(default=10, description="Number of results per page")
    start: int = Field(default=0, description="Starting result index")
    device: str = Field(default="desktop", description="Device type")


class YouTubeSearchParams(BaseModel):
    q: str = Field(..., description="Search query")
    part: str = Field(default="snippet", description="API response parts")
    type: str = Field(default="video", description="Resource type")
    order: str = Field(default="relevance", description="Sort order")
    regionCode: str = Field(default="IN", description="Region code")
    maxResults: int = Field(default=50, description="Max results per request")
    publishedAfter: Optional[str] = Field(None, description="ISO date filter")


class RawGoogleResult(BaseModel):
    position: int = Field(..., description="Result position")
    title: str = Field(..., description="Result title")
    link: str = Field(..., description="Result URL")
    snippet: str = Field(default="", description="Result snippet")
    displayed_link: str = Field(default="", description="Displayed domain")
    source: str = Field(default="", description="Source attribution")
    
    # Rich results
    sitelinks: Optional[List[Dict[str, Any]]] = Field(None, description="Sitelinks")
    rich_snippet: Optional[Dict[str, Any]] = Field(None, description="Rich snippet data")
    
    # Metadata
    thumbnail: Optional[str] = Field(None, description="Result thumbnail")
    cached_page_link: Optional[str] = Field(None, description="Cached page URL")


class RawYouTubeSearchResult(BaseModel):
    kind: str = Field(..., description="Resource type")
    etag: str = Field(..., description="ETag")
    id: Dict[str, str] = Field(..., description="Resource ID")
    snippet: Dict[str, Any] = Field(..., description="Video snippet data")


class RawYouTubeVideoDetails(BaseModel):
    kind: str = Field(..., description="Resource type")
    etag: str = Field(..., description="ETag")
    id: str = Field(..., description="Video ID")
    snippet: Dict[str, Any] = Field(..., description="Video snippet")
    statistics: Dict[str, str] = Field(default_factory=dict, description="Video stats")
    contentDetails: Dict[str, Any] = Field(default_factory=dict, description="Content details")


class CollectionMetadata(BaseModel):
    keyword: str = Field(..., description="Search keyword used")
    platform: str = Field(..., description="Platform (google/youtube)")
    total_results: int = Field(..., description="Total results collected")
    pages_fetched: int = Field(default=1, description="Number of API pages fetched")
    
    # API usage
    api_calls_made: int = Field(..., description="Number of API calls")
    quota_used: Optional[int] = Field(None, description="API quota consumed")
    
    # Timing
    started_at: datetime = Field(..., description="Collection start time")
    completed_at: datetime = Field(..., description="Collection end time")
    duration_seconds: float = Field(..., description="Total duration")
    
    # Parameters used
    search_params: Union[GoogleSearchParams, YouTubeSearchParams] = Field(..., description="Search parameters")
    
    # Error tracking
    errors_encountered: List[str] = Field(default_factory=list, description="Errors during collection")
    warnings: List[str] = Field(default_factory=list, description="Warnings during collection")


class CollectionResult(BaseModel):
    metadata: CollectionMetadata = Field(..., description="Collection metadata")
    
    # Raw results (one of these will be populated)
    google_results: List[RawGoogleResult] = Field(default_factory=list)
    youtube_search_results: List[RawYouTubeSearchResult] = Field(default_factory=list)
    youtube_video_details: List[RawYouTubeVideoDetails] = Field(default_factory=list)
    
    # Processing status
    processed: bool = Field(default=False, description="Whether results have been processed")
    enriched: bool = Field(default=False, description="Whether results have been enriched")


class APIError(BaseModel):
    platform: str = Field(..., description="Platform where error occurred")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="API error code")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Context
    keyword: Optional[str] = Field(None, description="Search keyword when error occurred")
    request_params: Optional[Dict[str, Any]] = Field(None, description="Request parameters")


class RateLimitInfo(BaseModel):
    platform: str = Field(..., description="Platform")
    requests_made: int = Field(..., description="Requests made in current window")
    requests_limit: int = Field(..., description="Request limit per window")
    window_reset_time: datetime = Field(..., description="When the window resets")
    
    # Quota information (mainly for YouTube)
    quota_used: int = Field(default=0, description="Quota units used")
    daily_quota_limit: int = Field(default=10000, description="Daily quota limit")


class BatchCollectionRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to search")
    platforms: List[str] = Field(..., description="Platforms to search on")
    max_results_per_keyword: int = Field(default=30, description="Max results per keyword")
    
    # Scheduling
    delay_between_requests: float = Field(default=1.0, description="Delay between API calls")
    batch_size: int = Field(default=5, description="Batch size for parallel requests")
    
    # Filtering
    date_filter: Optional[str] = Field(None, description="Date filter (ISO string)")
    region: str = Field(default="IN", description="Geographic region")
    language: str = Field(default="en", description="Language preference")


class BatchCollectionResult(BaseModel):
    request: BatchCollectionRequest = Field(..., description="Original request")
    
    # Results per platform/keyword
    results: Dict[str, Dict[str, CollectionResult]] = Field(
        default_factory=dict, 
        description="Results indexed by platform -> keyword"
    )
    
    # Summary
    total_results_collected: int = Field(..., description="Total results across all searches")
    successful_collections: int = Field(..., description="Number of successful collections")
    failed_collections: int = Field(..., description="Number of failed collections")
    
    # Timing
    started_at: datetime = Field(..., description="Batch start time")
    completed_at: datetime = Field(..., description="Batch completion time")
    
    # Errors
    errors: List[APIError] = Field(default_factory=list, description="Errors encountered")