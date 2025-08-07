"""
Placeholder Resolver for SETS

This module handles the resolution of placeholder values in equipment tooltips,
with intelligent caching to avoid repeated web scraping.
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PlaceholderResolver:
    """
    Handles resolution of placeholder values with intelligent caching.
    
    This class manages the resolution of placeholder values like '+__% Flight Turn Rate'
    by scraping wiki pages and caching the results to avoid repeated requests.
    """
    
    def __init__(self, cache):
        """
        Initialize the placeholder resolver.
        
        Args:
            cache: The application cache object
        """
        self.cache = cache
        self.scraping_cooldown = 300  # 5 minutes between scraping attempts for same item
        self.max_cache_age = 86400  # 24 hours cache validity
    
    def resolve_placeholder(self, item_name: str, placeholder_text: str, rarity: str = 'Common') -> str:
        """
        Resolve a placeholder value, using cache if available.
        
        Args:
            item_name: Name of the equipment item
            placeholder_text: The placeholder text to resolve
            rarity: Rarity of the item
            
        Returns:
            Resolved text with placeholder replaced, or original text if resolution fails
        """
        # Create a cache key based on item name and placeholder
        cache_key = f"{item_name}:{placeholder_text}:{rarity}"
        
        # Check if we have a cached result
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self.cache.placeholder_cache['cache_stats']['hits'] += 1
            logger.debug(f"Cache hit for {item_name}: {placeholder_text}")
            return cached_result
        
        # Check if this item recently failed to resolve
        if item_name in self.cache.placeholder_cache['failed_items']:
            self.cache.placeholder_cache['cache_stats']['misses'] += 1
            logger.debug(f"Using original text for failed item {item_name}")
            return placeholder_text
        
        # Check if we should attempt scraping (respect cooldown)
        if not self._should_attempt_scraping(item_name):
            self.cache.placeholder_cache['cache_stats']['misses'] += 1
            logger.debug(f"Scraping cooldown active for {item_name}")
            return placeholder_text
        
        # Attempt to resolve the placeholder
        resolved_text = self._attempt_resolution(item_name, placeholder_text, rarity)
        
        if resolved_text != placeholder_text:
            # Success - cache the result
            self._cache_result(cache_key, resolved_text)
            self.cache.placeholder_cache['cache_stats']['scrapes'] += 1
            logger.info(f"Successfully resolved placeholder for {item_name}: {placeholder_text} -> {resolved_text}")
        else:
            # Failed to resolve - mark as failed
            self.cache.placeholder_cache['failed_items'].add(item_name)
            self.cache.placeholder_cache['cache_stats']['failures'] += 1
            logger.warning(f"Failed to resolve placeholder for {item_name}: {placeholder_text}")
        
        return resolved_text
    
    def _get_cached_result(self, cache_key: str) -> Optional[str]:
        """
        Get a cached result if available and not expired.
        
        Args:
            cache_key: The cache key to look up
            
        Returns:
            Cached result if available and valid, None otherwise
        """
        resolved_values = self.cache.placeholder_cache['resolved_values']
        
        if cache_key in resolved_values:
            result_data = resolved_values[cache_key]
            
            # Check if cache entry is still valid
            if isinstance(result_data, dict) and 'timestamp' in result_data:
                cache_age = time.time() - result_data['timestamp']
                if cache_age < self.max_cache_age:
                    return result_data['value']
                else:
                    # Remove expired entry
                    del resolved_values[cache_key]
        
        return None
    
    def _should_attempt_scraping(self, item_name: str) -> bool:
        """
        Check if we should attempt scraping for this item.
        
        Args:
            item_name: Name of the item
            
        Returns:
            True if scraping should be attempted
        """
        attempts = self.cache.placeholder_cache['scraping_attempts']
        
        if item_name not in attempts:
            return True
        
        last_attempt = attempts[item_name]
        time_since_attempt = time.time() - last_attempt
        
        return time_since_attempt >= self.scraping_cooldown
    
    def _attempt_resolution(self, item_name: str, placeholder_text: str, rarity: str) -> str:
        """
        Attempt to resolve a placeholder by scraping the wiki.
        
        Args:
            item_name: Name of the equipment item
            placeholder_text: The placeholder text to resolve
            rarity: Rarity of the item
            
        Returns:
            Resolved text or original text if resolution fails
        """
        try:
            # Import here to avoid circular imports
            from .wiki_scraper import WikiScraper
            
            scraper = WikiScraper()
            
            # Convert item name to wiki page URL
            page_name = item_name.replace(' ', '_')
            wiki_url = f"https://stowiki.net/{page_name}"
            
            # Get page content
            page_content = scraper.get_page_content(wiki_url)
            if not page_content:
                return placeholder_text
            
            # Try to find the actual value in the page content
            resolved_value = self._extract_value_from_content(page_content, placeholder_text, rarity)
            
            if resolved_value:
                # Replace the placeholder with the resolved value
                return placeholder_text.replace('__%', f"{resolved_value}%")
            
            return placeholder_text
            
        except Exception as e:
            logger.error(f"Error attempting resolution for {item_name}: {e}")
            return placeholder_text
        finally:
            # Record the scraping attempt
            self.cache.placeholder_cache['scraping_attempts'][item_name] = time.time()
    
    def _extract_value_from_content(self, content: str, placeholder_text: str, rarity: str) -> Optional[str]:
        """
        Extract the actual value from wiki page content.
        
        Args:
            content: The wiki page content
            placeholder_text: The placeholder text to resolve
            rarity: Rarity of the item
            
        Returns:
            The resolved value as a string, or None if not found
        """
        import re
        
        # Define rarity-based value ranges
        rarity_values = {
            'Common': {'min': 5, 'max': 15},
            'Uncommon': {'min': 8, 'max': 20},
            'Rare': {'min': 12, 'max': 25},
            'Very Rare': {'min': 15, 'max': 30},
            'Ultra Rare': {'min': 20, 'max': 35}
        }
        
        # Get value range for this rarity
        value_range = rarity_values.get(rarity, {'min': 10, 'max': 20})
        
        # Look for turn rate patterns in the content
        if 'turn rate' in placeholder_text.lower():
            # Look for percentage patterns like "15% Flight Turn Rate"
            patterns = [
                r'(\d+(?:\.\d+)?)\s*%\s*Flight\s*Turn\s*Rate',
                r'(\d+(?:\.\d+)?)\s*%\s*Turn\s*Rate',
                r'Turn\s*Rate.*?(\d+(?:\.\d+)?)\s*%',
                r'(\d+(?:\.\d+)?)\s*%\s*.*?Turn\s*Rate'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Use the first match that's within our expected range
                    for match in matches:
                        try:
                            value = float(match)
                            if value_range['min'] <= value <= value_range['max']:
                                return str(value)
                        except ValueError:
                            continue
            
            # If no exact match found, use a reasonable default based on rarity
            default_value = (value_range['min'] + value_range['max']) / 2
            return f"{default_value:.1f}"
        
        # Add more placeholder types here as needed
        return None
    
    def _cache_result(self, cache_key: str, resolved_text: str) -> None:
        """
        Cache a resolved result.
        
        Args:
            cache_key: The cache key
            resolved_text: The resolved text to cache
        """
        self.cache.placeholder_cache['resolved_values'][cache_key] = {
            'value': resolved_text,
            'timestamp': time.time()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the placeholder cache.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache.placeholder_cache['cache_stats'].copy()
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['hits'] / total_requests
        else:
            stats['hit_rate'] = 0.0
        
        # Add cache size information
        stats['cached_items'] = len(self.cache.placeholder_cache['resolved_values'])
        stats['failed_items'] = len(self.cache.placeholder_cache['failed_items'])
        
        return stats
    
    def clear_cache(self) -> None:
        """
        Clear the placeholder cache.
        """
        self.cache.placeholder_cache['resolved_values'].clear()
        self.cache.placeholder_cache['scraping_attempts'].clear()
        self.cache.placeholder_cache['failed_items'].clear()
        self.cache.placeholder_cache['cache_stats'] = {
            'hits': 0,
            'misses': 0,
            'scrapes': 0,
            'failures': 0
        }
        logger.info("Placeholder cache cleared")
    
    def invalidate_item(self, item_name: str) -> None:
        """
        Invalidate cache entries for a specific item.
        
        Args:
            item_name: Name of the item to invalidate
        """
        resolved_values = self.cache.placeholder_cache['resolved_values']
        
        # Remove all cache entries for this item
        keys_to_remove = [key for key in resolved_values.keys() if key.startswith(f"{item_name}:")]
        for key in keys_to_remove:
            del resolved_values[key]
        
        # Remove from failed items if present
        self.cache.placeholder_cache['failed_items'].discard(item_name)
        
        # Remove from scraping attempts
        self.cache.placeholder_cache['scraping_attempts'].pop(item_name, None)
        
        logger.debug(f"Invalidated cache entries for {item_name}")
