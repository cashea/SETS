"""
MediaWiki API Module for STO Wiki - READ ONLY

This module provides READ-ONLY access to stowiki.net data using the MediaWiki API
and Cargo extension, which is much more efficient than web scraping.

IMPORTANT: This module is designed to be READ-ONLY and will never attempt to
write, edit, or modify anything on stowiki.net. It only retrieves data for
display and caching purposes.
"""

import json
import os
import time
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode, quote_plus
import requests
from requests.exceptions import RequestException


class MediaWikiAPI:
    """
    A READ-ONLY MediaWiki API client for stowiki.net that uses the Cargo extension
    for efficient data retrieval. This client is designed to only READ data and
    never attempts to write or modify anything on the wiki.
    """
    
    def __init__(self, base_url: str = "https://stowiki.net", cache_dir: str = "cache"):
        """
        Initialize the READ-ONLY MediaWiki API client.
        
        Args:
            base_url: Base URL for the wiki
            cache_dir: Directory to cache downloaded data
        """
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SETS/1.0 (Star Trek Online Build Tool - Read Only)'
        })
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, "api_data"), exist_ok=True)
        
        # Ensure this is a read-only client
        self._read_only = True
    
    def get_cargo_data(self, table: str, fields: List[str], 
                        where: Optional[str] = None, 
                        limit: int = 2500,
                        offset: int = 0,
                        format: str = "json") -> List[Dict[str, Any]]:
        """
        Get data from a Cargo table using the CargoExport API (READ-ONLY).
        
        Args:
            table: Name of the Cargo table
            fields: List of fields to retrieve
            where: WHERE clause for filtering (optional)
            limit: Maximum number of results
            offset: Number of results to skip
            format: Output format (json, csv, etc.)
            
        Returns:
            List of dictionaries containing the data
        """
        # Safety check - ensure this is read-only
        if not self._read_only:
            raise RuntimeError("This API client is read-only and cannot perform write operations")
        
        # Build the CargoExport URL (READ-ONLY endpoint)
        params = {
            'tables': table,
            'fields': ','.join(fields),
            'limit': limit,
            'offset': offset,
            'format': format
        }
        
        if where:
            params['where'] = where
        
        url = f"{self.base_url}/wiki/Special:CargoExport"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            if format == "json":
                return response.json()
            else:
                # Handle other formats as needed
                return response.text
            
        except RequestException as e:
            print(f"Error fetching cargo data from {table}: {e}")
            return []
    
    def get_ships_data(self, ship_type: Optional[str] = None, 
                       faction: Optional[str] = None,
                       tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ship data from the Ships Cargo table.
        
        Args:
            ship_type: Filter by ship type (optional)
            faction: Filter by faction (optional)
            tier: Filter by tier (optional)
            
        Returns:
            List of ship data dictionaries
        """
        fields = [
            '_pageName=Page',
            'name',
            'image',
            'fc',
            'tier',
            'type',
            'hull',
            'hullmod',
            'shieldmod',
            'turnrate',
            'impulse',
            'inertia',
            'powerall',
            'powerweapons',
            'powershields',
            'powerengines',
            'powerauxiliary',
            'powerboost',
            'boffs',
            'fore',
            'aft',
            'equipcannons',
            'devices',
            'consolestac',
            'consoleseng',
            'consolessci',
            'uniconsole',
            't5uconsole',
            'experimental',
            'secdeflector',
            'hangars',
            'abilities',
            'displayprefix',
            'displayclass',
            'displaytype',
            'factionlede'
        ]
        
        where_conditions = []
        if ship_type:
            where_conditions.append(f"type='{ship_type}'")
        if faction:
            where_conditions.append(f"fc='{faction}'")
        if tier:
            where_conditions.append(f"tier='{tier}'")
        
        where_clause = None
        if where_conditions:
            where_clause = ' AND '.join(where_conditions)
        
        return self.get_cargo_data('Ships', fields, where_clause)
    
    def get_equipment_data(self, equipment_type: Optional[str] = None,
                          rarity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get equipment data from the Infobox Cargo table.
        
        Args:
            equipment_type: Filter by equipment type (optional)
            rarity: Filter by rarity (optional)
            
        Returns:
            List of equipment data dictionaries
        """
        fields = [
            '_pageName=Page',
            'name',
            'rarity',
            'type',
            'boundto',
            'boundwhen',
            'who',
            'head1', 'head2', 'head3', 'head4', 'head5',
            'head6', 'head7', 'head8', 'head9',
            'subhead1', 'subhead2', 'subhead3', 'subhead4', 'subhead5',
            'subhead6', 'subhead7', 'subhead8', 'subhead9',
            'text1', 'text2', 'text3', 'text4', 'text5',
            'text6', 'text7', 'text8', 'text9'
        ]
        
        where_conditions = []
        if equipment_type:
            where_conditions.append(f"type='{equipment_type}'")
        if rarity:
            where_conditions.append(f"rarity='{rarity}'")
        
        where_clause = None
        if where_conditions:
            where_clause = ' AND '.join(where_conditions)
        
        return self.get_cargo_data('Infobox', fields, where_clause, limit=5000)
    
    def get_traits_data(self, trait_type: Optional[str] = None,
                       environment: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trait data from the Traits Cargo table.
        
        Args:
            trait_type: Filter by trait type (optional)
            environment: Filter by environment (space/ground) (optional)
            
        Returns:
            List of trait data dictionaries
        """
        fields = [
            '_pageName=Page',
            'name',
            'chartype',
            'environment',
            'type',
            'isunique',
            'description'
        ]
        
        where_conditions = []
        if trait_type:
            where_conditions.append(f"type='{trait_type}'")
        if environment:
            where_conditions.append(f"environment='{environment}'")
        
        where_clause = None
        if where_conditions:
            where_clause = ' AND '.join(where_conditions)
        
        return self.get_cargo_data('Traits', fields, where_clause)
    
    def get_starship_traits_data(self) -> List[Dict[str, Any]]:
        """
        Get starship trait data from the StarshipTraits Cargo table.
        
        Returns:
            List of starship trait data dictionaries
        """
        fields = [
            '_pageName=Page',
            'name',
            'short',
            'type',
            'detailed',
            'obtained',
            'basic'
        ]
        
        where_clause = "name IS NOT NULL"
        
        return self.get_cargo_data('StarshipTraits', fields, where_clause)
    
    def get_doff_data(self) -> List[Dict[str, Any]]:
        """
        Get duty officer data from the Specializations Cargo table.
        
        Returns:
            List of duty officer data dictionaries
        """
        fields = [
            'name=spec',
            '_pageName',
            'shipdutytype',
            'department',
            'description',
            'white',
            'green',
            'blue',
            'purple',
            'violet',
            'gold'
        ]
        
        return self.get_cargo_data('Specializations', fields)
    
    def get_modifiers_data(self) -> List[Dict[str, Any]]:
        """
        Get modifier data from the Modifiers Cargo table.
        
        Returns:
            List of modifier data dictionaries
        """
        fields = [
            '_pageName',
            'modifier',
            'type',
            'stats',
            'available',
            'isunique',
            'isepic',
            'info'
        ]
        
        return self.get_cargo_data('Modifiers', fields)
    
    def search_pages(self, query: str, namespace: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for pages using the MediaWiki API.
        
        Args:
            query: Search query
            namespace: Namespace to search in (0 for main namespace)
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srnamespace': namespace,
            'srlimit': limit,
            'format': 'json'
        }
        
        url = f"{self.base_url}/api.php"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('query', {}).get('search', [])
            
        except RequestException as e:
            print(f"Error searching pages: {e}")
            return []
    
    def get_page_content(self, page_title: str) -> Optional[str]:
        """
        Get the content of a wiki page.
        
        Args:
            page_title: Title of the page
            
        Returns:
            Page content as string or None if failed
        """
        params = {
            'action': 'query',
            'prop': 'revisions',
            'titles': page_title,
            'rvprop': 'content',
            'format': 'json'
        }
        
        url = f"{self.base_url}/api.php"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if 'revisions' in page_data:
                    return page_data['revisions'][0]['*']
            
            return None
            
        except RequestException as e:
            print(f"Error getting page content for {page_title}: {e}")
            return None
    
    def get_page_info(self, page_title: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a wiki page.
        
        Args:
            page_title: Title of the page
            
        Returns:
            Page information dictionary or None if failed
        """
        params = {
            'action': 'query',
            'prop': 'info|revisions',
            'titles': page_title,
            'inprop': 'url|displaytitle',
            'rvprop': 'timestamp|user|comment',
            'rvlimit': 1,
            'format': 'json'
        }
        
        url = f"{self.base_url}/api.php"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if 'missing' not in page_data:
                    return page_data
            
            return None
            
        except RequestException as e:
            print(f"Error getting page info for {page_title}: {e}")
            return None
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file (image).
        
        Args:
            filename: Name of the file
            
        Returns:
            File information dictionary or None if failed
        """
        params = {
            'action': 'query',
            'prop': 'imageinfo',
            'titles': f"File:{filename}",
            'iiprop': 'url|size|mime|timestamp|user',
            'format': 'json'
        }
        
        url = f"{self.base_url}/api.php"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if 'imageinfo' in page_data:
                    return page_data['imageinfo'][0]
            
            return None
            
        except RequestException as e:
            print(f"Error getting file info for {filename}: {e}")
            return None
    
    def download_file(self, filename: str, save_path: str) -> bool:
        """
        Download a file from the wiki.
        
        Args:
            filename: Name of the file to download
            save_path: Path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        file_info = self.get_file_info(filename)
        if not file_info:
            return False
        
        try:
            response = self.session.get(file_info['url'], timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except RequestException as e:
            print(f"Error downloading file {filename}: {e}")
            return False
    
    def get_all_ship_types(self) -> List[str]:
        """
        Get all available ship types from the Ships table.
        
        Returns:
            List of unique ship types
        """
        ships_data = self.get_ships_data()
        ship_types = set()
        
        for ship in ships_data:
            if 'type' in ship and ship['type']:
                ship_types.add(ship['type'])
        
        return sorted(list(ship_types))
    
    def get_all_factions(self) -> List[str]:
        """
        Get all available factions from the Ships table.
        
        Returns:
            List of unique factions
        """
        ships_data = self.get_ships_data()
        factions = set()
        
        for ship in ships_data:
            if 'fc' in ship and ship['fc']:
                factions.add(ship['fc'])
        
        return sorted(list(factions))
    
    def get_all_tiers(self) -> List[str]:
        """
        Get all available tiers from the Ships table.
        
        Returns:
            List of unique tiers
        """
        ships_data = self.get_ships_data()
        tiers = set()
        
        for ship in ships_data:
            if 'tier' in ship and ship['tier']:
                tiers.add(ship['tier'])
        
        return sorted(list(tiers), key=lambda x: int(x) if x.isdigit() else 0)


class CachedMediaWikiAPI(MediaWikiAPI):
    """
    A cached version of MediaWikiAPI that stores results locally.
    """
    
    def __init__(self, base_url: str = "https://stowiki.net", cache_dir: str = "cache", 
                 cache_duration: int = 86400):  # 24 hours default
        """
        Initialize the cached MediaWiki API client.
        
        Args:
            base_url: Base URL for the wiki
            cache_dir: Directory to cache downloaded data
            cache_duration: Cache duration in seconds
        """
        super().__init__(base_url, cache_dir)
        self.cache_duration = cache_duration
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the cache file path for a given key."""
        return os.path.join(self.cache_dir, "api_data", f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file is still valid."""
        if not os.path.exists(cache_path):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_path)
        return file_age < self.cache_duration
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(cache_key)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """Load data from cache."""
        cache_path = self._get_cache_path(cache_key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return None
    
    def get_ships_data(self, ship_type: Optional[str] = None, 
                       faction: Optional[str] = None,
                       tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """Cached version of get_ships_data."""
        cache_key = f"ships_{ship_type or 'all'}_{faction or 'all'}_{tier or 'all'}"
        
        # Try to load from cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        data = super().get_ships_data(ship_type, faction, tier)
        
        # Save to cache
        self._save_to_cache(cache_key, data)
        
        return data
    
    def get_equipment_data(self, equipment_type: Optional[str] = None,
                          rarity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Cached version of get_equipment_data."""
        cache_key = f"equipment_{equipment_type or 'all'}_{rarity or 'all'}"
        
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = super().get_equipment_data(equipment_type, rarity)
        self._save_to_cache(cache_key, data)
        
        return data
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        cache_dir = os.path.join(self.cache_dir, "api_data")
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(cache_dir, file))
        print("Cleared API cache")


def main():
    """
    Example usage of the MediaWiki API client.
    """
    # Initialize API client
    api = CachedMediaWikiAPI()
    
    print("=== MediaWiki API Test ===")
    
    # Get ship data
    print("Fetching ship data...")
    ships = api.get_ships_data()
    print(f"Found {len(ships)} ships")
    
    # Get equipment data
    print("Fetching equipment data...")
    equipment = api.get_equipment_data()
    print(f"Found {len(equipment)} equipment items")
    
    # Get ship types
    print("Getting ship types...")
    ship_types = api.get_all_ship_types()
    print(f"Available ship types: {ship_types}")
    
    # Get factions
    print("Getting factions...")
    factions = api.get_all_factions()
    print(f"Available factions: {factions}")
    
    # Search for pages
    print("Searching for 'Raider'...")
    search_results = api.search_pages("Raider")
    print(f"Found {len(search_results)} pages matching 'Raider'")


if __name__ == "__main__":
    main()
