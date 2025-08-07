# Future Data Sources for SETS

## Overview

While SETS currently uses the MediaWiki API for stowiki.net data, the wiki scraper remains valuable for potential future expansion to other websites that don't have APIs. This document outlines potential data sources and how the scraper could be adapted.

## Potential Data Sources

### 1. STO Community Websites

#### **STOBuilds.com**
- **URL**: https://stobuilds.com
- **Data Available**: Build guides, meta analysis, community builds
- **Scraping Potential**: High - well-structured HTML with build data
- **Use Case**: Import community builds, meta recommendations

#### **STO Academy**
- **URL**: https://stoacademy.space
- **Data Available**: Build guides, ship reviews, meta analysis
- **Scraping Potential**: Medium - modern React-based site
- **Use Case**: Additional build data, ship reviews

#### **Reddit r/sto**
- **URL**: https://reddit.com/r/sto
- **Data Available**: Community discussions, build sharing, meta posts
- **Scraping Potential**: Medium - Reddit API available but limited
- **Use Case**: Community sentiment, build trends

### 2. Official STO Resources

#### **Arc Games STO Forums**
- **URL**: https://forums.arcgames.com/startrekonline
- **Data Available**: Official announcements, patch notes, developer posts
- **Scraping Potential**: High - traditional forum structure
- **Use Case**: Patch notes, official announcements

#### **STO Official Website**
- **URL**: https://www.arcgames.com/en/games/star-trek-online
- **Data Available**: News, events, official ship/equipment info
- **Scraping Potential**: Medium - modern web structure
- **Use Case**: Official announcements, event data

### 3. Third-Party Tools

#### **STO DPS League**
- **URL**: https://www.stodpsleague.com
- **Data Available**: DPS records, build analysis, performance data
- **Scraping Potential**: High - structured data tables
- **Use Case**: Performance benchmarks, DPS analysis

#### **STO Wiki (Other Languages)**
- **URLs**: Various language versions of STO wikis
- **Data Available**: Localized ship/equipment data
- **Scraping Potential**: High - similar MediaWiki structure
- **Use Case**: Localized data, additional languages

## Scraper Adaptation Strategy

### 1. Modular Scraper Architecture

The current `WikiScraper` can be extended with a modular approach:

```python
class BaseScraper:
    """Base class for all scrapers"""
    
    def __init__(self, base_url: str, cache_dir: str = "cache"):
        self.base_url = base_url
        self.cache_dir = cache_dir
        self.session = requests.Session()
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Base method for fetching pages"""
        pass
    
    def parse_data(self, soup: BeautifulSoup) -> Dict:
        """Abstract method for parsing data"""
        raise NotImplementedError

class STOBuildsScraper(BaseScraper):
    """Scraper for STOBuilds.com"""
    
    def __init__(self):
        super().__init__("https://stobuilds.com")
    
    def parse_builds(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse build data from STOBuilds"""
        # Implementation for STOBuilds structure
        pass

class STOAcademyScraper(BaseScraper):
    """Scraper for STO Academy"""
    
    def __init__(self):
        super().__init__("https://stoacademy.space")
    
    def parse_guides(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse guide data from STO Academy"""
        # Implementation for STO Academy structure
        pass
```

### 2. Data Source Configuration

Create a configuration system for different data sources:

```python
DATA_SOURCES = {
    'stowiki': {
        'type': 'api',
        'url': 'https://stowiki.net',
        'priority': 1,
        'enabled': True
    },
    'stobuilds': {
        'type': 'scraper',
        'url': 'https://stobuilds.com',
        'priority': 2,
        'enabled': False,
        'scraper_class': 'STOBuildsScraper'
    },
    'stoacademy': {
        'type': 'scraper',
        'url': 'https://stoacademy.space',
        'priority': 3,
        'enabled': False,
        'scraper_class': 'STOAcademyScraper'
    }
}
```

### 3. Data Integration Strategy

#### **Primary Data Source**: stowiki.net (API)
- Ships, equipment, traits, modifiers
- Most reliable and comprehensive
- Used as fallback for other sources

#### **Secondary Data Sources**: Community sites (Scraping)
- Build guides and meta analysis
- Community sentiment and trends
- Performance benchmarks

#### **Tertiary Data Sources**: Official sites (Scraping)
- Patch notes and announcements
- Event information
- Official news

### 4. Implementation Examples

#### **STOBuilds Scraper Example**

```python
class STOBuildsScraper(BaseScraper):
    """Scraper for STOBuilds.com build data"""
    
    def scrape_builds(self, category: str = None) -> List[Dict]:
        """Scrape builds from STOBuilds"""
        url = f"{self.base_url}/builds"
        if category:
            url += f"/{category}"
        
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        builds = []
        build_elements = soup.find_all('div', class_='build-card')
        
        for element in build_elements:
            build_data = {
                'title': element.find('h3').text.strip(),
                'author': element.find('span', class_='author').text.strip(),
                'ship': element.find('span', class_='ship').text.strip(),
                'category': element.find('span', class_='category').text.strip(),
                'url': self.base_url + element.find('a')['href']
            }
            builds.append(build_data)
        
        return builds
    
    def scrape_build_details(self, build_url: str) -> Dict:
        """Scrape detailed build information"""
        soup = self.get_page_content(build_url)
        if not soup:
            return {}
        
        # Parse detailed build data
        build_details = {
            'equipment': self._parse_equipment(soup),
            'skills': self._parse_skills(soup),
            'traits': self._parse_traits(soup),
            'stats': self._parse_stats(soup)
        }
        
        return build_details
```

#### **STO Academy Scraper Example**

```python
class STOAcademyScraper(BaseScraper):
    """Scraper for STO Academy guides"""
    
    def scrape_guides(self, ship_type: str = None) -> List[Dict]:
        """Scrape guides from STO Academy"""
        url = f"{self.base_url}/guides"
        if ship_type:
            url += f"/{ship_type}"
        
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        guides = []
        guide_elements = soup.find_all('article', class_='guide')
        
        for element in guide_elements:
            guide_data = {
                'title': element.find('h2').text.strip(),
                'author': element.find('span', class_='author').text.strip(),
                'ship': element.find('span', class_='ship').text.strip(),
                'rating': element.find('span', class_='rating').text.strip(),
                'url': self.base_url + element.find('a')['href']
            }
            guides.append(guide_data)
        
        return guides
```

## Benefits of Keeping the Scraper

### 1. **Data Redundancy**
- Multiple sources provide backup if one fails
- Cross-reference data for accuracy
- Fill gaps in primary data source

### 2. **Enhanced Features**
- Community build imports
- Meta analysis and trends
- Performance benchmarks
- Localized content

### 3. **Future-Proofing**
- New websites may emerge
- Existing sites may change APIs
- Community-driven data sources

### 4. **Competitive Analysis**
- Compare builds across platforms
- Identify popular strategies
- Track meta evolution

## Implementation Priority

### **Phase 1: Foundation** (Current)
- ✅ MediaWiki API for stowiki.net
- ✅ Wiki scraper as fallback
- ✅ Basic data loading system

### **Phase 2: Community Integration** (Future)
- 🔄 STOBuilds scraper
- 🔄 Community build imports
- 🔄 Meta analysis features

### **Phase 3: Advanced Features** (Future)
- 🔄 Multi-source data aggregation
- 🔄 Cross-reference validation
- 🔄 Community sentiment analysis

## Conclusion

The wiki scraper should be **kept and enhanced** rather than removed. It provides:

1. **Fallback capability** for API failures
2. **Future expansion** to other data sources
3. **Community integration** possibilities
4. **Data redundancy** and reliability

The modular approach allows for easy addition of new data sources while maintaining the current API-first strategy.
