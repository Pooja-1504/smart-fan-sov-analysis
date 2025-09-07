from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
 
    id: str = Field(..., description="Unique identifier for the result")
    url: str = Field(..., description="URL of the search result")
    title: str = Field(..., description="Title of the search result")
    snippet: str = Field(..., description="Description/snippet from search")
    domain: str = Field(..., description="Domain of the result")
    rank: int = Field(..., description="Position in search results (1-based)")
    keyword: str = Field(..., description="Search keyword used")
    platform: str = Field(default="google", description="Platform (google)")
    result_type: str = Field(default="organic", description="Type of result")
    collected_at: datetime = Field(default_factory=datetime.now)


class VideoResult(BaseModel):
  
    video_id: str = Field(..., description="YouTube video ID")
    url: str = Field(..., description="YouTube video URL")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    channel_title: str = Field(..., description="Channel name")
    published_at: datetime = Field(..., description="Video publish date")
    duration: Optional[str] = Field(None, description="Video duration (ISO 8601)")
    views: int = Field(default=0, description="View count")
    likes: int = Field(default=0, description="Like count")
    comments: int = Field(default=0, description="Comment count")
    rank: int = Field(..., description="Position in search results (1-based)")
    keyword: str = Field(..., description="Search keyword used")
    platform: str = Field(default="youtube", description="Platform (youtube)")
    collected_at: datetime = Field(default_factory=datetime.now)


class BrandMention(BaseModel):
    
    brand: str = Field(..., description="Brand name")
    count: int = Field(..., description="Number of mentions")
    confidence: float = Field(default=1.0, description="Confidence score (0-1)")


class EnrichedDocument(BaseModel):

    id: str = Field(..., description="Unique document identifier")
    platform: str = Field(..., description="Source platform")
    keyword: str = Field(..., description="Search keyword")
    rank: int = Field(..., description="Search result rank")
    url: str = Field(..., description="Document URL")
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Full text content")
    
    # Enrichment data
    brands_mentioned: List[BrandMention] = Field(default_factory=list)
    sentiment_score: float = Field(default=0.0, description="Sentiment (-1 to 1)")
    sentiment_label: str = Field(default="neutral", description="positive/neutral/negative")
    
    # Engagement metrics (platform-specific)
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    processed_at: datetime = Field(default_factory=datetime.now)
    collected_at: datetime = Field(..., description="Original collection time")


class WeightComponents(BaseModel):
   
    rank_weight: float = Field(..., description="Weight based on search rank")
    engagement_weight: float = Field(..., description="Weight based on engagement")
    mention_weight: float = Field(..., description="Weight based on mention count")
    sentiment_weight: float = Field(..., description="Weight based on sentiment")


class ScoredMention(BaseModel):
 
    document_id: str = Field(..., description="Reference to source document")
    brand: str = Field(..., description="Brand name")
    platform: str = Field(..., description="Source platform")
    keyword: str = Field(..., description="Search keyword")
    
    # Raw data
    rank: int = Field(..., description="Search result rank")
    mention_count: int = Field(..., description="Number of brand mentions")
    sentiment_score: float = Field(..., description="Document sentiment")
    engagement_raw: Dict[str, Any] = Field(default_factory=dict)
    
    # Weights
    weights: WeightComponents = Field(..., description="Individual weight components")
    
    # Final score
    total_score: float = Field(..., description="Final weighted score")
    
    # Metadata
    scored_at: datetime = Field(default_factory=datetime.now)


class SovSummary(BaseModel):
    brand: str = Field(..., description="Brand name")
    platform: str = Field(..., description="Platform")
    keyword: str = Field(..., description="Keyword")
    
    # SoV metrics
    total_score: float = Field(..., description="Total weighted score")
    share_of_voice: float = Field(..., description="SoV percentage (0-100)")
    share_of_positive_voice: float = Field(..., description="SoPV percentage (0-100)")
    
    # Supporting data
    mention_count: int = Field(..., description="Total mentions")
    positive_mentions: int = Field(..., description="Positive sentiment mentions")
    average_rank: float = Field(..., description="Average search rank")
    average_sentiment: float = Field(..., description="Average sentiment score")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now)


class PlatformSummary(BaseModel):
    
    platform: str = Field(..., description="Platform name")
    keywords_analyzed: List[str] = Field(..., description="Keywords included")
    brand_summaries: List[SovSummary] = Field(..., description="Per-brand SoV data")
    
    # Aggregate metrics
    total_documents: int = Field(..., description="Total documents analyzed")
    total_brands_found: int = Field(..., description="Unique brands mentioned")
    
    generated_at: datetime = Field(default_factory=datetime.now)