"""
Wiki Scraper Module for STO Wiki

This module provides functionality to scrape ship tables and icons from stowiki.net.
It can parse various ship tables and extract structured data including icons.
"""

import asyncio
import os
import re
import time
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
import aiohttp
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession


class WikiScraper:
    """
    A web scraper for stowiki.net that can extract ship table data and icons.
    """
    
    def __init__(self, base_url: str = "https://stowiki.net", cache_dir: str = "cache"):
        """
        Initialize the WikiScraper.
        
        Args:
            base_url: Base URL for the wiki
            cache_dir: Directory to cache downloaded images
        """
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, "icons"), exist_ok=True)
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def find_ship_tables(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """
        Find all ship tables on a page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of table elements
        """
        # Look for tables that might contain ship data
        # Common patterns for ship tables
        ship_table_selectors = [
            'table.wikitable',
            'table.sortable',
            'table[class*="ship"]',
            'table[class*="vessel"]',
            'table[class*="starship"]'
        ]
        
        tables = []
        for selector in ship_table_selectors:
            found_tables = soup.select(selector)
            tables.extend(found_tables)
        
        # Also look for tables with ship-related headers
        all_tables = soup.find_all('table')
        for table in all_tables:
            headers = table.find_all(['th', 'td'])
            header_text = ' '.join([h.get_text().lower() for h in headers[:5]])
            if any(keyword in header_text for keyword in ['ship', 'vessel', 'class', 'faction', 'tier']):
                if table not in tables:
                    tables.append(table)
        
        return tables
    
    def extract_table_data(self, table: BeautifulSoup) -> List[Dict[str, Union[str, Dict]]]:
        """
        Extract structured data from a ship table.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            List of dictionaries containing ship data
        """
        ships = []
        
        # Find headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                header_text = th.get_text(strip=True)
                if header_text:
                    headers.append(header_text)
        
        # Process data rows
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:  # Skip rows with insufficient data
                continue
            
            ship_data = {}
            icons = {}
            
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    break
                
                header = headers[i] if i < len(headers) else f"column_{i}"
                
                # Extract text content
                text_content = cell.get_text(strip=True)
                if text_content:
                    ship_data[header] = text_content
                
                # Extract icons/images
                images = cell.find_all('img')
                if images:
                    icon_data = []
                    for img in images:
                        icon_info = self.extract_image_info(img)
                        if icon_info:
                            icon_data.append(icon_info)
                    
                    if icon_data:
                        icons[header] = icon_data
            
            # Add icons to ship data
            if icons:
                ship_data['icons'] = icons
            
            if ship_data:  # Only add if we have some data
                ships.append(ship_data)
        
        return ships
    
    def extract_image_info(self, img: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Extract information from an image element.
        
        Args:
            img: BeautifulSoup img element
            
        Returns:
            Dictionary with image information
        """
        src = img.get('src', '')
        alt = img.get('alt', '')
        title = img.get('title', '')
        
        if not src:
            return None
        
        # Make URL absolute if it's relative
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = urljoin(self.base_url, src)
        elif not src.startswith('http'):
            src = urljoin(self.base_url, src)
        
        return {
            'src': src,
            'alt': alt,
            'title': title,
            'filename': os.path.basename(urlparse(src).path)
        }
    
    def download_icon(self, icon_info: Dict[str, str]) -> Optional[str]:
        """
        Download an icon and save it to cache.
        
        Args:
            icon_info: Dictionary containing icon information
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            src = icon_info['src']
            filename = icon_info['filename']
            
            # Create a unique filename if needed
            if not filename or '.' not in filename:
                filename = f"icon_{hash(src)}.png"
            
            cache_path = os.path.join(self.cache_dir, "icons", filename)
            
            # Skip if already cached
            if os.path.exists(cache_path):
                return cache_path
            
            # Download the image
            response = self.session.get(src, timeout=30)
            response.raise_for_status()
            
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            return cache_path
            
        except Exception as e:
            print(f"Error downloading icon {icon_info.get('src', 'unknown')}: {e}")
            return None
    
    def scrape_raider_page(self) -> List[Dict[str, Union[str, Dict]]]:
        """
        Scrape the Raider ship table from stowiki.net.
        
        Returns:
            List of dictionaries containing Raider ship data
        """
        url = f"{self.base_url}/wiki/Raider"
        soup = self.get_page_content(url)
        
        if not soup:
            return []
        
        tables = self.find_ship_tables(soup)
        all_ships = []
        
        for table in tables:
            ships = self.extract_table_data(table)
            all_ships.extend(ships)
        
        return all_ships
    
    def scrape_ship_page(self, ship_name: str) -> List[Dict[str, Union[str, Dict]]]:
        """
        Scrape a specific ship page.
        
        Args:
            ship_name: Name of the ship to scrape
            
        Returns:
            List of dictionaries containing ship data
        """
        # Convert ship name to URL format
        url_safe_name = ship_name.replace(' ', '_')
        url = f"{self.base_url}/wiki/{url_safe_name}"
        
        soup = self.get_page_content(url)
        
        if not soup:
            return []
        
        tables = self.find_ship_tables(soup)
        all_ships = []
        
        for table in tables:
            ships = self.extract_table_data(table)
            all_ships.extend(ships)
        
        return all_ships
    
    def download_all_icons(self, ships_data: List[Dict[str, Union[str, Dict]]]) -> Dict[str, str]:
        """
        Download all icons from ship data.
        
        Args:
            ships_data: List of ship data dictionaries
            
        Returns:
            Dictionary mapping icon URLs to local file paths
        """
        icon_paths = {}
        
        for ship in ships_data:
            if 'icons' in ship:
                for column, icons in ship['icons'].items():
                    for icon in icons:
                        if isinstance(icon, dict) and 'src' in icon:
                            local_path = self.download_icon(icon)
                            if local_path:
                                icon_paths[icon['src']] = local_path
        
        return icon_paths
    
    def get_ship_list(self) -> List[str]:
        """
        Get a list of available ships from the wiki.
        
        Returns:
            List of ship names
        """
        # This would need to be implemented based on the wiki structure
        # For now, return some common ship types
        common_ships = [
            "Raider",
            "Escort", 
            "Cruiser",
            "Science_Vessel",
            "Carrier",
            "Dreadnought",
            "Warbird",
            "Bird_of_Prey",
            "Battlecruiser"
        ]
        
        return common_ships
    
    def scrape_multiple_ships(self, ship_names: List[str]) -> Dict[str, List[Dict]]:
        """
        Scrape multiple ship pages.
        
        Args:
            ship_names: List of ship names to scrape
            
        Returns:
            Dictionary mapping ship names to their data
        """
        results = {}
        
        for ship_name in ship_names:
            print(f"Scraping {ship_name}...")
            ship_data = self.scrape_ship_page(ship_name)
            if ship_data:
                results[ship_name] = ship_data
                # Download icons for this ship
                self.download_all_icons(ship_data)
            
            # Be respectful to the server
            time.sleep(1)
        
        return results


class AsyncWikiScraper:
    """
    Asynchronous version of WikiScraper for better performance.
    """
    
    def __init__(self, base_url: str = "https://stowiki.net", cache_dir: str = "cache"):
        """
        Initialize the AsyncWikiScraper.
        
        Args:
            base_url: Base URL for the wiki
            cache_dir: Directory to cache downloaded images
        """
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, "icons"), exist_ok=True)
    
    async def get_page_content(self, session: aiohttp.ClientSession, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page asynchronously.
        
        Args:
            session: aiohttp session
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()
                    return BeautifulSoup(content, 'html.parser')
                else:
                    print(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    async def download_icon_async(self, session: aiohttp.ClientSession, icon_info: Dict[str, str]) -> Optional[str]:
        """
        Download an icon asynchronously.
        
        Args:
            session: aiohttp session
            icon_info: Dictionary containing icon information
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            src = icon_info['src']
            filename = icon_info['filename']
            
            # Create a unique filename if needed
            if not filename or '.' not in filename:
                filename = f"icon_{hash(src)}.png"
            
            cache_path = os.path.join(self.cache_dir, "icons", filename)
            
            # Skip if already cached
            if os.path.exists(cache_path):
                return cache_path
            
            # Download the image
            async with session.get(src, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(cache_path, 'wb') as f:
                        f.write(content)
                    return cache_path
                else:
                    print(f"HTTP {response.status} for icon {src}")
                    return None
                    
        except Exception as e:
            print(f"Error downloading icon {icon_info.get('src', 'unknown')}: {e}")
            return None
    
    async def scrape_ships_async(self, ship_names: List[str]) -> Dict[str, List[Dict]]:
        """
        Scrape multiple ship pages asynchronously.
        
        Args:
            ship_names: List of ship names to scrape
            
        Returns:
            Dictionary mapping ship names to their data
        """
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for ship_name in ship_names:
                task = self.scrape_single_ship_async(session, ship_name)
                tasks.append(task)
            
            # Execute all tasks concurrently
            ship_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ship_name, ship_data in zip(ship_names, ship_results):
                if isinstance(ship_data, Exception):
                    print(f"Error scraping {ship_name}: {ship_data}")
                elif ship_data:
                    results[ship_name] = ship_data
        
        return results
    
    async def scrape_single_ship_async(self, session: aiohttp.ClientSession, ship_name: str) -> List[Dict]:
        """
        Scrape a single ship page asynchronously.
        
        Args:
            session: aiohttp session
            ship_name: Name of the ship to scrape
            
        Returns:
            List of dictionaries containing ship data
        """
        url_safe_name = ship_name.replace(' ', '_')
        url = f"{self.base_url}/wiki/{url_safe_name}"
        
        soup = await self.get_page_content(session, url)
        
        if not soup:
            return []
        
        # Use the same table finding and data extraction logic as the sync version
        scraper = WikiScraper(self.base_url, self.cache_dir)
        tables = scraper.find_ship_tables(soup)
        all_ships = []
        
        for table in tables:
            ships = scraper.extract_table_data(table)
            all_ships.extend(ships)
        
        return all_ships


def main():
    """
    Example usage of the WikiScraper.
    """
    # Synchronous example
    scraper = WikiScraper()
    
    print("Scraping Raider ships...")
    raider_ships = scraper.scrape_raider_page()
    print(f"Found {len(raider_ships)} Raider ships")
    
    # Download icons
    icon_paths = scraper.download_all_icons(raider_ships)
    print(f"Downloaded {len(icon_paths)} icons")
    
    # Asynchronous example
    async def async_example():
        async_scraper = AsyncWikiScraper()
        ship_names = ["Raider", "Escort", "Cruiser"]
        
        print("Scraping multiple ships asynchronously...")
        results = await async_scraper.scrape_ships_async(ship_names)
        
        for ship_name, ships in results.items():
            print(f"{ship_name}: {len(ships)} ships found")
    
    # Run async example
    asyncio.run(async_example())


if __name__ == "__main__":
    main()
