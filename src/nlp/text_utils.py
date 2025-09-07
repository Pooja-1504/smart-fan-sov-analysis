import re
from typing import List, Optional


def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_sentences(text: str) -> List[str]:
    if not text:
        return []
    
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def truncate_text(text: str, max_length: int = 500) -> str:
    if not text or len(text) <= max_length:
        return text
    
    # Find last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    if not text:
        return []
    
    # Remove punctuation and split
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter by length and common stop words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
    
    return keywords


def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    
    # Simple heuristic: count English words
    english_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must'}
    
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return "unknown"
    
    english_count = sum(1 for word in words if word in english_words)
    english_ratio = english_count / len(words)
    
    return "english" if english_ratio > 0.1 else "other"


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    return text.strip()