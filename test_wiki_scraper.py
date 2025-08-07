#!/usr/bin/env python3
"""
Test script for the Wiki Scraper module.

This script demonstrates how to use the wiki scraper to extract ship data and icons
from stowiki.net.
"""

import asyncio
import json
import os
from src.wiki_scraper import WikiScraper, AsyncWikiScraper


def test_sync_scraper():
    """Test the synchronous scraper."""
    print("=== Testing Synchronous Scraper ===")
    
    # Initialize scraper
    scraper = WikiScraper(cache_dir="test_cache")
    
    # Scrape Raider ships
    print("Scraping Raider ships...")
    raider_ships = scraper.scrape_raider_page()
    
    print(f"Found {len(raider_ships)} Raider ships")
    
    # Print first few ships for inspection
    for i, ship in enumerate(raider_ships[:3]):
        print(f"\nShip {i+1}:")
        for key, value in ship.items():
            if key != 'icons':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {len(value)} icon columns")
    
    # Download icons
    print("\nDownloading icons...")
    icon_paths = scraper.download_all_icons(raider_ships)
    print(f"Downloaded {len(icon_paths)} icons")
    
    # Save data to JSON for inspection
    output_file = "raider_ships.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(raider_ships, f, indent=2, ensure_ascii=False)
    print(f"Saved ship data to {output_file}")
    
    return raider_ships


def test_async_scraper():
    """Test the asynchronous scraper."""
    print("\n=== Testing Asynchronous Scraper ===")
    
    async def run_async_test():
        # Initialize async scraper
        async_scraper = AsyncWikiScraper(cache_dir="test_cache")
        
        # List of ships to scrape
        ship_names = ["Raider", "Escort", "Cruiser"]
        
        print(f"Scraping {len(ship_names)} ship types asynchronously...")
        results = await async_scraper.scrape_ships_async(ship_names)
        
        # Print results
        for ship_name, ships in results.items():
            print(f"{ship_name}: {len(ships)} ships found")
        
        # Save results to JSON
        output_file = "async_ships.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Saved async results to {output_file}")
        
        return results
    
    # Run async test
    return asyncio.run(run_async_test())


def test_specific_ship():
    """Test scraping a specific ship page."""
    print("\n=== Testing Specific Ship Scraping ===")
    
    scraper = WikiScraper(cache_dir="test_cache")
    
    # Test with a specific ship
    ship_name = "Bird_of_Prey"
    print(f"Scraping {ship_name}...")
    
    ships = scraper.scrape_ship_page(ship_name)
    print(f"Found {len(ships)} ships on {ship_name} page")
    
    if ships:
        print("First ship data:")
        ship = ships[0]
        for key, value in ship.items():
            if key != 'icons':
                print(f"  {key}: {value}")
    
    return ships


def main():
    """Run all tests."""
    print("Wiki Scraper Test Suite")
    print("=" * 50)
    
    try:
        # Test synchronous scraper
        sync_results = test_sync_scraper()
        
        # Test asynchronous scraper
        async_results = test_async_scraper()
        
        # Test specific ship
        specific_results = test_specific_ship()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print(f"Sync results: {len(sync_results)} ships")
        print(f"Async results: {sum(len(ships) for ships in async_results.values())} total ships")
        print(f"Specific ship results: {len(specific_results)} ships")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
