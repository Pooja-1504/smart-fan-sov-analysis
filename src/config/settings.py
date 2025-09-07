import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    
    # API Keys
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # Search Configuration
    REGION: str = os.getenv("REGION", "IN")
    LANGUAGE: str = os.getenv("LANGUAGE", "en")
    GOOGLE_RESULTS_COUNT: int = int(os.getenv("GOOGLE_RESULTS_COUNT", "30"))
    YOUTUBE_RESULTS_COUNT: int = int(os.getenv("YOUTUBE_RESULTS_COUNT", "40"))
    
    # Keywords
    PRIMARY_KEYWORDS: List[str] = [
        keyword.strip() 
        for keyword in os.getenv("PRIMARY_KEYWORDS", "smart fan,BLDC fan").split(",")
    ]
    
    # Brand Configuration
    TARGET_BRAND: str = "Atomberg"
    COMPETITOR_BRANDS: List[str] = [
        "Havells", "Crompton", "Orient Electric", "Orient", 
        "Usha", "Bajaj", "Panasonic", "Syska", "Polycab", "Luminous"
    ]
    
    # Output Settings
    OUTPUT_FORMAT: str = os.getenv("OUTPUT_FORMAT", "csv")
    INCLUDE_CHARTS: bool = os.getenv("INCLUDE_CHARTS", "true").lower() == "true"
    
    # Rate Limiting
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "60"))
    
    # Data Paths
    DATA_RAW_PATH: str = "data/raw"
    DATA_PROCESSED_PATH: str = "data/processed"
    DATA_REPORTS_PATH: str = "data/reports"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required API keys are present."""
        missing = []
        if not cls.SERPAPI_API_KEY:
            missing.append("SERPAPI_API_KEY")
        if not cls.YOUTUBE_API_KEY:
            missing.append("YOUTUBE_API_KEY")
        
        if missing:
            print(f"Missing required environment variables: {', '.join(missing)}")
            return False
        return True

# Global settings instance
settings = Settings()