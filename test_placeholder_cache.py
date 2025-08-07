#!/usr/bin/env python3
"""
Test script for placeholder caching system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.placeholder_resolver import PlaceholderResolver
from src.widgets import Cache

def test_placeholder_cache():
    """Test the placeholder caching functionality."""
    
    print("Testing Placeholder Cache System")
    print("=" * 40)
    
    # Create a cache instance
    cache = Cache()
    
    # Create a placeholder resolver
    resolver = PlaceholderResolver(cache)
    
    # Test data
    test_items = [
        {
            'name': 'Console - Engineering - RCS Accelerator',
            'placeholder': '+__% Flight Turn Rate',
            'rarity': 'Very Rare'
        },
        {
            'name': 'Console - Engineering - RCS Accelerator',
            'placeholder': '+__% Flight Turn Rate',
            'rarity': 'Common'
        },
        {
            'name': 'Combat Impulse Engines',
            'placeholder': '+__ Flight Speed',
            'rarity': 'Common'
        }
    ]
    
    print("Initial cache stats:")
    stats = resolver.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nTesting placeholder resolution:")
    
    for i, item in enumerate(test_items, 1):
        print(f"\nTest {i}: {item['name']} ({item['rarity']})")
        print(f"  Placeholder: {item['placeholder']}")
        
        # Resolve the placeholder
        resolved = resolver.resolve_placeholder(
            item['name'], 
            item['placeholder'], 
            item['rarity']
        )
        
        print(f"  Resolved: {resolved}")
        
        # Show cache stats after each resolution
        stats = resolver.get_cache_stats()
        print(f"  Cache hits: {stats['hits']}, misses: {stats['misses']}, scrapes: {stats['scrapes']}")
    
    print("\nFinal cache stats:")
    stats = resolver.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nCached items: {stats['cached_items']}")
    print(f"Failed items: {stats['failed_items']}")
    
    # Test cache invalidation
    print("\nTesting cache invalidation:")
    resolver.invalidate_item('Console - Engineering - RCS Accelerator')
    
    stats = resolver.get_cache_stats()
    print(f"After invalidation - cached items: {stats['cached_items']}")
    
    # Test cache clearing
    print("\nTesting cache clearing:")
    resolver.clear_cache()
    
    stats = resolver.get_cache_stats()
    print(f"After clearing - cached items: {stats['cached_items']}")
    print(f"After clearing - failed items: {stats['failed_items']}")
    
    print("\nPlaceholder cache test completed!")

if __name__ == "__main__":
    test_placeholder_cache()
