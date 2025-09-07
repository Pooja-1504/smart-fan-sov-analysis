import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union, Type, TypeVar
import pandas as pd
from pydantic import BaseModel

from .schemas import (
    SearchResult, VideoResult, EnrichedDocument, 
    ScoredMention, SovSummary, PlatformSummary
)
from ..config.settings import settings

T = TypeVar('T', bound=BaseModel)


class DataIO:
    
    @staticmethod
    def ensure_dir(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_timestamp_filename(prefix: str, extension: str = "csv") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
    
    @staticmethod
    def save_models_to_csv(
        models: List[BaseModel], 
        filepath: str,
        ensure_directory: bool = True
    ) -> None:
        if ensure_directory:
            DataIO.ensure_dir(os.path.dirname(filepath))
        
        if not models:
            # Create empty file with headers
            pd.DataFrame().to_csv(filepath, index=False)
            return
        
        # Convert models to dictionaries
        data = [model.model_dump() for model in models]
        df = pd.DataFrame(data)
        
        # Handle datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to identify datetime columns
                sample_val = df[col].iloc[0] if len(df) > 0 else None
                if isinstance(sample_val, datetime):
                    df[col] = pd.to_datetime(df[col])
        
        df.to_csv(filepath, index=False)
    
    @staticmethod
    def save_models_to_parquet(
        models: List[BaseModel], 
        filepath: str,
        ensure_directory: bool = True
    ) -> None:
        if ensure_directory:
            DataIO.ensure_dir(os.path.dirname(filepath))
        
        if not models:
            # Create empty file
            pd.DataFrame().to_parquet(filepath, index=False)
            return
        
        data = [model.model_dump() for model in models]
        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False)
    
    @staticmethod
    def load_models_from_csv(
        filepath: str, 
        model_class: Type[T]
    ) -> List[T]:
        if not os.path.exists(filepath):
            return []
        
        df = pd.read_csv(filepath)
        if df.empty:
            return []
        
        # Convert DataFrame rows to model instances
        models = []
        for _, row in df.iterrows():
            # Convert row to dict, handling NaN values
            data = row.to_dict()
            # Replace NaN with None for proper Pydantic handling
            data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
            
            try:
                model = model_class(**data)
                models.append(model)
            except Exception as e:
                print(f"Warning: Failed to parse row as {model_class.__name__}: {e}")
                continue
        
        return models
    
    @staticmethod
    def load_models_from_parquet(
        filepath: str, 
        model_class: Type[T]
    ) -> List[T]:
        if not os.path.exists(filepath):
            return []
        
        df = pd.read_parquet(filepath)
        if df.empty:
            return []
        
        models = []
        for _, row in df.iterrows():
            data = row.to_dict()
            data = {k: (None if pd.isna(v) else v) for k, v in data.items()}
            
            try:
                model = model_class(**data)
                models.append(model)
            except Exception as e:
                print(f"Warning: Failed to parse row as {model_class.__name__}: {e}")
                continue
        
        return models
    
    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str) -> None:
        DataIO.ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


class DataPaths:
    
    @staticmethod
    def raw_search_results(keyword: str, platform: str) -> str:
        safe_keyword = keyword.replace(" ", "_").replace("/", "_")
        filename = f"{platform}_{safe_keyword}_{datetime.now().strftime('%Y%m%d')}.csv"
        return os.path.join(settings.DATA_RAW_PATH, filename)
    
    @staticmethod
    def enriched_documents(date_str: str = None) -> str:
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        filename = f"enriched_{date_str}.csv"
        return os.path.join(settings.DATA_PROCESSED_PATH, filename)
    
    @staticmethod
    def scored_mentions(date_str: str = None) -> str:
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        filename = f"scored_{date_str}.csv"
        return os.path.join(settings.DATA_REPORTS_PATH, filename)
    
    @staticmethod
    def sov_summary(date_str: str = None) -> str:
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        filename = f"sov_summary_{date_str}.csv"
        return os.path.join(settings.DATA_REPORTS_PATH, filename)
    
    @staticmethod
    def platform_summary(platform: str, date_str: str = None) -> str:
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{platform}_summary_{date_str}.json"
        return os.path.join(settings.DATA_REPORTS_PATH, filename)


# Convenience functions for common operations
def save_search_results(results: List[Union[SearchResult, VideoResult]], 
                       keyword: str, platform: str) -> str:
    filepath = DataPaths.raw_search_results(keyword, platform)
    DataIO.save_models_to_csv(results, filepath)
    return filepath


def load_enriched_documents(date_str: str = None) -> List[EnrichedDocument]:
    filepath = DataPaths.enriched_documents(date_str)
    return DataIO.load_models_from_csv(filepath, EnrichedDocument)


def save_scored_mentions(mentions: List[ScoredMention], date_str: str = None) -> str:
    filepath = DataPaths.scored_mentions(date_str)
    DataIO.save_models_to_csv(mentions, filepath)
    return filepath


def save_sov_summary(summaries: List[SovSummary], date_str: str = None) -> str:
    filepath = DataPaths.sov_summary(date_str)
    DataIO.save_models_to_csv(summaries, filepath)
    return filepath