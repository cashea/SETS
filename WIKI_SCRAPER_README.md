# Wiki Scraper Module

This module provides functionality to scrape ship tables and icons from stowiki.net. It can parse various ship tables and extract structured data including icons.

## Features

- **Ship Table Parsing**: Automatically detects and extracts ship data from wiki tables
- **Icon Scraping**: Downloads and caches ship icons and images
- **Synchronous & Asynchronous**: Both sync and async versions for different use cases
- **Caching**: Automatically caches downloaded images to avoid re-downloading
- **Flexible**: Can scrape any ship page on stowiki.net
- **Error Handling**: Robust error handling for network issues and parsing problems

## Installation

The module uses the following dependencies (already included in the project):
- `requests` - For HTTP requests
- `aiohttp` - For async HTTP requests
- `beautifulsoup4` - For HTML parsing
- `requests_html` - For additional HTML parsing capabilities

## Usage

### Basic Usage

```python
from src.wiki_scraper import WikiScraper

# Initialize scraper
scraper = WikiScraper(cache_dir="cache")

# Scrape Raider ships
raider_ships = scraper.scrape_raider_page()
print(f"Found {len(raider_ships)} Raider ships")

# Download icons
icon_paths = scraper.download_all_icons(raider_ships)
print(f"Downloaded {len(icon_paths)} icons")
```

### Scraping Specific Ships

```python
# Scrape a specific ship page
ships = scraper.scrape_ship_page("Bird_of_Prey")
print(f"Found {len(ships)} ships")

# Scrape multiple ships
ship_names = ["Raider", "Escort", "Cruiser"]
results = scraper.scrape_multiple_ships(ship_names)

for ship_name, ships in results.items():
    print(f"{ship_name}: {len(ships)} ships")
```

### Asynchronous Usage

```python
import asyncio
from src.wiki_scraper import AsyncWikiScraper

async def scrape_ships():
    async_scraper = AsyncWikiScraper(cache_dir="cache")
    
    ship_names = ["Raider", "Escort", "Cruiser"]
    results = await async_scraper.scrape_ships_async(ship_names)
    
    return results

# Run async scraper
results = asyncio.run(scrape_ships())
```

## Data Structure

The scraper returns ship data in the following format:

```python
[
    {
        "Ship Name": "Example Ship",
        "Faction": "Federation",
        "Tier": "T6",
        "icons": {
            "Ship Name": [
                {
                    "src": "https://stowiki.net/images/icon.png",
                    "alt": "Ship Icon",
                    "title": "Ship Icon",
                    "filename": "icon.png"
                }
            ]
        }
    }
]
```

## Configuration

### Cache Directory

The scraper automatically creates a cache directory structure:
```
cache/
├── icons/          # Downloaded ship icons
└── ...             # Other cached data
```

### User Agent

The scraper uses a realistic user agent to avoid being blocked:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
```

## Error Handling

The module includes comprehensive error handling:

- **Network Errors**: Graceful handling of connection timeouts and HTTP errors
- **Parsing Errors**: Robust HTML parsing with fallback strategies
- **File System Errors**: Safe file operations with proper error reporting
- **Rate Limiting**: Built-in delays to be respectful to the server

## Testing

Run the test script to verify functionality:

```bash
python test_wiki_scraper.py
```

This will:
1. Test the synchronous scraper
2. Test the asynchronous scraper
3. Test specific ship scraping
4. Save results to JSON files for inspection

## Integration with SETS

The wiki scraper can be integrated into the SETS application to:

1. **Populate Ship Database**: Automatically scrape ship data for the ship selector
2. **Update Icons**: Download and cache ship icons for the UI
3. **Data Validation**: Verify ship information against the wiki
4. **Auto-Updates**: Periodically update ship data from the wiki

### Example Integration

```python
# In your SETS application
from src.wiki_scraper import WikiScraper

class ShipDataManager:
    def __init__(self):
        self.scraper = WikiScraper(cache_dir="cache")
    
    def update_ship_data(self):
        """Update ship data from wiki"""
        ships = self.scraper.scrape_raider_page()
        # Process and store ship data
        return ships
    
    def get_ship_icons(self, ship_name):
        """Get cached icon for a ship"""
        # Implementation to retrieve cached icons
        pass
```

## Limitations

- **Wiki Structure**: The scraper relies on consistent wiki table structure
- **Rate Limiting**: Respects server resources with built-in delays
- **Image Formats**: Supports common web image formats (PNG, JPG, GIF, SVG)
- **Network Dependency**: Requires internet connection for scraping

## Contributing

To extend the scraper:

1. **Add New Ship Types**: Update the `get_ship_list()` method
2. **Improve Table Detection**: Enhance the `find_ship_tables()` method
3. **Add Data Processing**: Extend the `extract_table_data()` method
4. **Optimize Performance**: Improve async handling and caching

## License

This module is part of the SETS project and follows the same license terms.
