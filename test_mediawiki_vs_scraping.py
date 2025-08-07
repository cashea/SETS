#!/usr/bin/env python3
"""
Comparison Test: MediaWiki API vs Web Scraping

This script demonstrates the advantages of using the MediaWiki API
over web scraping for accessing stowiki.net data.
"""

import time
import json
from src.mediawiki_api import CachedMediaWikiAPI
from src.wiki_scraper import WikiScraper


def test_mediawiki_api():
    """Test the MediaWiki API approach."""
    print("=== Testing MediaWiki API ===")
    
    start_time = time.time()
    
    # Initialize API client
    api = CachedMediaWikiAPI(cache_dir="test_cache_api")
    
    # Get ship data using API
    print("Fetching ship data via API...")
    ships = api.get_ships_data()
    print(f"Found {len(ships)} ships")
    
    # Get specific ship types
    print("Fetching Raider ships...")
    raider_ships = api.get_ships_data(ship_type="Raider")
    print(f"Found {len(raider_ships)} Raider ships")
    
    # Get equipment data
    print("Fetching equipment data...")
    equipment = api.get_equipment_data()
    print(f"Found {len(equipment)} equipment items")
    
    # Get ship types and factions
    ship_types = api.get_all_ship_types()
    factions = api.get_all_factions()
    tiers = api.get_all_tiers()
    
    print(f"Available ship types: {len(ship_types)}")
    print(f"Available factions: {len(factions)}")
    print(f"Available tiers: {len(tiers)}")
    
    api_time = time.time() - start_time
    print(f"MediaWiki API test completed in {api_time:.2f} seconds")
    
    return {
        'ships': len(ships),
        'raider_ships': len(raider_ships),
        'equipment': len(equipment),
        'ship_types': len(ship_types),
        'factions': len(factions),
        'tiers': len(tiers),
        'time': api_time
    }


def test_web_scraping():
    """Test the web scraping approach."""
    print("\n=== Testing Web Scraping ===")
    
    start_time = time.time()
    
    # Initialize scraper
    scraper = WikiScraper(cache_dir="test_cache_scraping")
    
    # Scrape Raider ships
    print("Scraping Raider ships...")
    raider_ships = scraper.scrape_raider_page()
    print(f"Found {len(raider_ships)} Raider ships")
    
    # Download icons
    print("Downloading icons...")
    icon_paths = scraper.download_all_icons(raider_ships)
    print(f"Downloaded {len(icon_paths)} icons")
    
    # Test specific ship scraping
    print("Scraping specific ship page...")
    bird_of_prey_ships = scraper.scrape_ship_page("Bird_of_Prey")
    print(f"Found {len(bird_of_prey_ships)} Bird of Prey ships")
    
    scraping_time = time.time() - start_time
    print(f"Web scraping test completed in {scraping_time:.2f} seconds")
    
    return {
        'raider_ships': len(raider_ships),
        'bird_of_prey_ships': len(bird_of_prey_ships),
        'icons_downloaded': len(icon_paths),
        'time': scraping_time
    }


def compare_approaches():
    """Compare the two approaches."""
    print("=== Comparison: MediaWiki API vs Web Scraping ===\n")
    
    # Run tests
    api_results = test_mediawiki_api()
    scraping_results = test_web_scraping()
    
    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    
    print(f"\nData Retrieved:")
    print(f"  MediaWiki API:")
    print(f"    - Total ships: {api_results['ships']}")
    print(f"    - Raider ships: {api_results['raider_ships']}")
    print(f"    - Equipment items: {api_results['equipment']}")
    print(f"    - Ship types: {api_results['ship_types']}")
    print(f"    - Factions: {api_results['factions']}")
    print(f"    - Tiers: {api_results['tiers']}")
    
    print(f"\n  Web Scraping:")
    print(f"    - Raider ships: {scraping_results['raider_ships']}")
    print(f"    - Bird of Prey ships: {scraping_results['bird_of_prey_ships']}")
    print(f"    - Icons downloaded: {scraping_results['icons_downloaded']}")
    
    print(f"\nPerformance:")
    print(f"  MediaWiki API: {api_results['time']:.2f} seconds")
    print(f"  Web Scraping: {scraping_results['time']:.2f} seconds")
    
    if api_results['time'] < scraping_results['time']:
        speedup = scraping_results['time'] / api_results['time']
        print(f"  API is {speedup:.1f}x faster")
    else:
        slowdown = api_results['time'] / scraping_results['time']
        print(f"  API is {slowdown:.1f}x slower")
    
    print(f"\nAdvantages of MediaWiki API:")
    print(f"  ✓ More reliable (uses structured data)")
    print(f"  ✓ Faster data retrieval")
    print(f"  ✓ Better error handling")
    print(f"  ✓ Built-in filtering and querying")
    print(f"  ✓ Respects server resources")
    print(f"  ✓ Caching support")
    print(f"  ✓ Structured data format")
    
    print(f"\nAdvantages of Web Scraping:")
    print(f"  ✓ Can extract visual elements (icons)")
    print(f"  ✓ Works with any HTML structure")
    print(f"  ✓ Can handle dynamic content")
    print(f"  ✓ More flexible for custom parsing")
    
    return api_results, scraping_results


def test_api_features():
    """Test additional MediaWiki API features."""
    print("\n=== Testing Additional API Features ===")
    
    api = CachedMediaWikiAPI(cache_dir="test_cache_api")
    
    # Test search functionality
    print("Testing search functionality...")
    search_results = api.search_pages("Raider", limit=10)
    print(f"Found {len(search_results)} pages matching 'Raider'")
    
    # Test page content retrieval
    if search_results:
        first_result = search_results[0]['title']
        print(f"Getting content for: {first_result}")
        content = api.get_page_content(first_result)
        if content:
            print(f"Content length: {len(content)} characters")
        else:
            print("No content retrieved")
    
    # Test file info retrieval
    print("Testing file info retrieval...")
    file_info = api.get_file_info("Faction_FED25.png")
    if file_info:
        print(f"File URL: {file_info.get('url', 'N/A')}")
        print(f"File size: {file_info.get('size', 'N/A')} bytes")
    else:
        print("File info not available")
    
    # Test filtering
    print("Testing data filtering...")
    fed_ships = api.get_ships_data(faction="Federation")
    print(f"Found {len(fed_ships)} Federation ships")
    
    t6_ships = api.get_ships_data(tier="6")
    print(f"Found {len(t6_ships)} T6 ships")
    
    cruiser_ships = api.get_ships_data(ship_type="Cruiser")
    print(f"Found {len(cruiser_ships)} Cruiser ships")


def main():
    """Run all tests."""
    print("MediaWiki API vs Web Scraping Comparison")
    print("=" * 60)
    
    try:
        # Compare approaches
        api_results, scraping_results = compare_approaches()
        
        # Test additional API features
        test_api_features()
        
        print("\n" + "=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        print("For SETS application, use MediaWiki API because:")
        print("1. It's more efficient and reliable")
        print("2. It provides structured data directly")
        print("3. It has better error handling")
        print("4. It respects server resources")
        print("5. It supports caching for better performance")
        print("6. It can be easily integrated with existing SETS code")
        
        # Save results for reference
        results = {
            'api_results': api_results,
            'scraping_results': scraping_results,
            'recommendation': 'Use MediaWiki API for better performance and reliability'
        }
        
        with open('comparison_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to comparison_results.json")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
