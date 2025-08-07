"""
Ship Data Manager for SETS

This module integrates the wiki scraper with the SETS application to provide
ship data and icons for the ship selector and other components.
"""

import json
import os
from typing import Dict, List, Optional, Union
from .wiki_scraper import WikiScraper, AsyncWikiScraper


class ShipDataManager:
    """
    Manages ship data and icons for the SETS application.
    
    This class provides an interface between the wiki scraper and the SETS
    application, handling data caching, icon management, and ship information
    retrieval.
    """
    
    def __init__(self, cache_dir: str = "cache", data_file: str = "ship_data.json"):
        """
        Initialize the ShipDataManager.
        
        Args:
            cache_dir: Directory for caching scraped data and icons
            data_file: JSON file to store processed ship data
        """
        self.cache_dir = cache_dir
        self.data_file = os.path.join(cache_dir, data_file)
        self.scraper = WikiScraper(cache_dir=cache_dir)
        self.ship_data = {}
        self.load_cached_data()
    
    def load_cached_data(self):
        """Load cached ship data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.ship_data = json.load(f)
                print(f"Loaded {len(self.ship_data)} cached ship entries")
        except Exception as e:
            print(f"Error loading cached data: {e}")
            self.ship_data = {}
    
    def save_cached_data(self):
        """Save ship data to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.ship_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.ship_data)} ship entries to cache")
        except Exception as e:
            print(f"Error saving cached data: {e}")
    
    def update_ship_data(self, ship_types: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Update ship data from the wiki.
        
        Args:
            ship_types: List of ship types to update. If None, uses default list.
            
        Returns:
            Dictionary mapping ship types to their data
        """
        if ship_types is None:
            ship_types = self.scraper.get_ship_list()
        
        print(f"Updating ship data for {len(ship_types)} ship types...")
        
        # Scrape ship data
        results = self.scraper.scrape_multiple_ships(ship_types)
        
        # Process and store the data
        for ship_type, ships in results.items():
            for ship in ships:
                # Create a unique key for each ship
                ship_key = self._create_ship_key(ship)
                self.ship_data[ship_key] = {
                    'type': ship_type,
                    'data': ship,
                    'cached_icons': self._get_cached_icon_paths(ship)
                }
        
        # Save updated data
        self.save_cached_data()
        
        return results
    
    def _create_ship_key(self, ship: Dict) -> str:
        """
        Create a unique key for a ship based on its data.
        
        Args:
            ship: Ship data dictionary
            
        Returns:
            Unique string key for the ship
        """
        # Use ship name and rank as the key
        ship_name = ship.get('Ship', 'Unknown')
        rank = ship.get('Rank', 'Unknown')
        return f"{ship_name}_{rank}".replace(' ', '_')
    
    def _get_cached_icon_paths(self, ship: Dict) -> Dict[str, List[str]]:
        """
        Get cached icon paths for a ship.
        
        Args:
            ship: Ship data dictionary
            
        Returns:
            Dictionary mapping column names to cached icon paths
        """
        cached_icons = {}
        
        if 'icons' in ship:
            for column, icons in ship['icons'].items():
                cached_paths = []
                for icon in icons:
                    if isinstance(icon, dict) and 'src' in icon:
                        local_path = self.scraper.download_icon(icon)
                        if local_path:
                            cached_paths.append(local_path)
                
                if cached_paths:
                    cached_icons[column] = cached_paths
        
        return cached_icons
    
    def get_ship_list(self, ship_type: Optional[str] = None) -> List[str]:
        """
        Get a list of available ships.
        
        Args:
            ship_type: Optional filter for specific ship type
            
        Returns:
            List of ship names
        """
        if ship_type:
            return [key for key, data in self.ship_data.items() 
                   if data.get('type') == ship_type]
        else:
            return list(self.ship_data.keys())
    
    def get_ship_data(self, ship_key: str) -> Optional[Dict]:
        """
        Get data for a specific ship.
        
        Args:
            ship_key: Unique key for the ship
            
        Returns:
            Ship data dictionary or None if not found
        """
        return self.ship_data.get(ship_key)
    
    def get_ship_icons(self, ship_key: str) -> Dict[str, List[str]]:
        """
        Get cached icon paths for a ship.
        
        Args:
            ship_key: Unique key for the ship
            
        Returns:
            Dictionary mapping column names to icon paths
        """
        ship_data = self.ship_data.get(ship_key)
        if ship_data:
            return ship_data.get('cached_icons', {})
        return {}
    
    def search_ships(self, query: str, ship_type: Optional[str] = None) -> List[str]:
        """
        Search for ships by name or rank.
        
        Args:
            query: Search query string
            ship_type: Optional filter for specific ship type
            
        Returns:
            List of matching ship keys
        """
        query_lower = query.lower()
        results = []
        
        for key, data in self.ship_data.items():
            if ship_type and data.get('type') != ship_type:
                continue
            
            ship_info = data.get('data', {})
            ship_name = ship_info.get('Ship', '').lower()
            rank = ship_info.get('Rank', '').lower()
            
            if query_lower in ship_name or query_lower in rank:
                results.append(key)
        
        return results
    
    def get_ship_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the cached ship data.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_ships': len(self.ship_data),
            'ship_types': {},
            'factions': {},
            'tiers': {}
        }
        
        for key, data in self.ship_data.items():
            ship_info = data.get('data', {})
            
            # Count by ship type
            ship_type = data.get('type', 'Unknown')
            stats['ship_types'][ship_type] = stats['ship_types'].get(ship_type, 0) + 1
            
            # Count by faction (if available)
            faction = ship_info.get('Faction', 'Unknown')
            stats['factions'][faction] = stats['factions'].get(faction, 0) + 1
            
            # Count by tier (if available)
            tier = ship_info.get('Tier', 'Unknown')
            stats['tiers'][tier] = stats['tiers'].get(tier, 0) + 1
        
        return stats
    
    def clear_cache(self):
        """Clear all cached data."""
        self.ship_data = {}
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
        print("Cleared ship data cache")
    
    def export_ship_data(self, output_file: str):
        """
        Export ship data to a JSON file.
        
        Args:
            output_file: Path to output JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.ship_data, f, indent=2, ensure_ascii=False)
            print(f"Exported ship data to {output_file}")
        except Exception as e:
            print(f"Error exporting ship data: {e}")


# Example usage and integration with SETS
def create_ship_data_manager() -> ShipDataManager:
    """
    Create a ship data manager instance for use in SETS.
    
    Returns:
        Configured ShipDataManager instance
    """
    return ShipDataManager(cache_dir="cache", data_file="sets_ship_data.json")


def update_sets_ship_database():
    """
    Update the SETS ship database from the wiki.
    
    This function can be called periodically to keep the ship data up to date.
    """
    manager = create_ship_data_manager()
    
    # Update ship data
    results = manager.update_ship_data()
    
    # Print statistics
    stats = manager.get_ship_statistics()
    print(f"Updated ship database:")
    print(f"  Total ships: {stats['total_ships']}")
    print(f"  Ship types: {len(stats['ship_types'])}")
    print(f"  Factions: {len(stats['factions'])}")
    
    return manager


if __name__ == "__main__":
    # Example usage
    manager = create_ship_data_manager()
    
    # Update ship data
    print("Updating ship database...")
    manager.update_ship_data()
    
    # Print statistics
    stats = manager.get_ship_statistics()
    print(f"\nShip Database Statistics:")
    print(f"  Total ships: {stats['total_ships']}")
    print(f"  Ship types: {stats['ship_types']}")
    print(f"  Factions: {stats['factions']}")
    
    # Example search
    print(f"\nSearching for 'Raider' ships:")
    raider_ships = manager.search_ships('Raider')
    print(f"  Found {len(raider_ships)} Raider ships")
    
    for ship_key in raider_ships[:3]:  # Show first 3
        ship_data = manager.get_ship_data(ship_key)
        if ship_data:
            ship_info = ship_data['data']
            print(f"    {ship_info.get('Ship', 'Unknown')} - {ship_info.get('Rank', 'Unknown')}")
