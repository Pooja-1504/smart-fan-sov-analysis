from typing import Dict, List, Set
from ..config.settings import settings


class BrandLexicon:
    
    def __init__(self):
        self.target_brand = settings.TARGET_BRAND
        self.competitor_brands = settings.COMPETITOR_BRANDS
        
        # Brand variants and common misspellings
        self.brand_variants = self._build_brand_variants()
        
        # Exclusion patterns to avoid false positives
        self.exclusions = self._build_exclusions()
    
    def _build_brand_variants(self) -> Dict[str, Set[str]]:
        variants = {}
        
        # Atomberg variants
        variants["Atomberg"] = {
            "atomberg", "atom berg", "atomburg", "atemberg",
            "atomberg renesa", "atomberg efficio", "atomberg studio",
            "atomberg fans", "atomberg fan"
        }
        
        # Havells variants
        variants["Havells"] = {
            "havells", "havell", "havel", "havels",
            "havells india", "havells fan", "havells fans"
        }
        
        # Crompton variants
        variants["Crompton"] = {
            "crompton", "crompton greaves", "crompton fans",
            "crompton fan", "crompton india"
        }
        
        # Orient variants
        variants["Orient Electric"] = {
            "orient electric", "orient", "orient fan", "orient fans",
            "orient ceiling fan", "orient electric fan"
        }
        
        # Usha variants
        variants["Usha"] = {
            "usha", "usha fan", "usha fans", "usha international",
            "usha ceiling fan"
        }
        
        # Bajaj variants
        variants["Bajaj"] = {
            "bajaj", "bajaj fan", "bajaj fans", "bajaj electricals",
            "bajaj ceiling fan"
        }
        
        # Panasonic variants
        variants["Panasonic"] = {
            "panasonic", "panasonic fan", "panasonic fans",
            "panasonic india", "panasonic ceiling fan"
        }
        
        # Syska variants
        variants["Syska"] = {
            "syska", "syska fan", "syska fans", "syska led"
        }
        
        # Polycab variants
        variants["Polycab"] = {
            "polycab", "polycab fan", "polycab fans", "polycab india"
        }
        
        # Luminous variants
        variants["Luminous"] = {
            "luminous", "luminous fan", "luminous fans", "luminous power"
        }
        
        return variants
    
    def _build_exclusions(self) -> Dict[str, Set[str]]:
        return {
            "Orient Electric": {
                "orientation", "oriental", "orientate", "disoriented"
            },
            "Usha": {
                "usher", "rush", "crush", "bush"
            }
        }
    
    def get_all_brands(self) -> List[str]:
        return [self.target_brand] + self.competitor_brands
    
    def get_brand_variants(self, brand: str) -> Set[str]:
        return self.brand_variants.get(brand, {brand.lower()})
    
    def get_canonical_brand(self, variant: str) -> str:
        variant_lower = variant.lower().strip()
        
        for brand, variants in self.brand_variants.items():
            if variant_lower in variants:
                return brand
        
        # Fallback: exact match with original brand list
        for brand in self.get_all_brands():
            if variant_lower == brand.lower():
                return brand
        
        return variant  # Return as-is if not found
    
    def should_exclude(self, text: str, brand: str) -> bool:
        text_lower = text.lower()
        exclusions = self.exclusions.get(brand, set())
        
        for exclusion in exclusions:
            if exclusion in text_lower:
                return True
        
        return False
    
    def get_search_patterns(self) -> Dict[str, List[str]]:
        patterns = {}
        
        for brand in self.get_all_brands():
            variants = self.get_brand_variants(brand)
            # Sort by length (longest first) for better matching
            sorted_variants = sorted(variants, key=len, reverse=True)
            patterns[brand] = sorted_variants
        
        return patterns


# Global instance
brand_lexicon = BrandLexicon()


# Utility functions for quick access
def get_target_brand() -> str:
    return brand_lexicon.target_brand


def get_competitor_brands() -> List[str]:
    return brand_lexicon.competitor_brands


def get_all_brands() -> List[str]:
    return brand_lexicon.get_all_brands()


def get_brand_variants(brand: str) -> Set[str]:
    return brand_lexicon.get_brand_variants(brand)


def normalize_brand_name(variant: str) -> str:
    return brand_lexicon.get_canonical_brand(variant)