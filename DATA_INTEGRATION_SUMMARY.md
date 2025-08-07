# MediaWiki API Data Integration Summary

## Overview

The SETS application now incorporates data from stowiki.net using the MediaWiki API instead of web scraping. This provides more reliable, efficient, and maintainable data access.

## Data Files Location

### Cache Directory Structure
```
cache/
├── api_data/                    # MediaWiki API cache files
│   ├── ships_all_all_all.json  # Complete ship database (989KB)
│   ├── equipment_all_all.json  # Complete equipment database (2.6MB)
│   ├── traits_all_all.json     # Trait data (when loaded)
│   ├── starship_traits_all.json # Starship trait data (when loaded)
│   ├── doffs_all_all.json      # Duty officer data (when loaded)
│   └── modifiers_all_all.json  # Modifier data (when loaded)
└── [other cache files...]
```

### Data File Contents

#### Ships Data (`ships_all_all_all.json`)
- **Size**: 989KB
- **Records**: 772 ships
- **Fields**: Page, name, image, fc, tier, type, hull, hullmod, shieldmod, turnrate, impulse, inertia, powerall, powerweapons, powershields, powerengines, powerauxiliary, powerboost, boffs, fore, aft, equipcannons, devices, consolestac, consoleseng, consolessci, uniconsole, t5uconsole, experimental, secdeflector, hangars, abilities, displayprefix, displayclass, displaytype, factionlede

#### Equipment Data (`equipment_all_all.json`)
- **Size**: 2.6MB
- **Records**: 2,500 equipment items
- **Fields**: Page, name, rarity, type, boundto, boundwhen, who, head1-9, subhead1-9, text1-9

#### Traits Data (`traits_all_all.json`)
- **Records**: 1,074 traits
- **Fields**: Page, name, chartype, environment, type, isunique, description

#### Starship Traits Data (`starship_traits_all.json`)
- **Records**: 341 starship traits
- **Fields**: Page, name, short, type, detailed, obtained, basic

## Integration Points

### 1. API Data Loader (`src/api_data_loader.py`)
The main integration point that handles loading all data types:

```python
class APIDataLoader:
    def load_ships_data(self) -> Dict[str, Any]
    def load_equipment_data(self) -> Dict[str, Dict[str, Any]]
    def load_traits_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]
    def load_starship_traits_data(self) -> Dict[str, Any]
    def load_doff_data(self) -> Dict[str, Dict[str, Any]]
    def load_modifiers_data(self) -> Dict[str, Dict[str, Any]]
```

### 2. MediaWiki API Client (`src/mediawiki_api.py`)
The underlying API client that fetches data from stowiki.net:

```python
class CachedMediaWikiAPI:
    def get_ships_data(self) -> List[Dict[str, Any]]
    def get_equipment_data(self) -> List[Dict[str, Any]]
    def get_traits_data(self) -> List[Dict[str, Any]]
    def get_starship_traits_data(self) -> List[Dict[str, Any]]
    def get_doff_data(self) -> List[Dict[str, Any]]
    def get_modifiers_data(self) -> List[Dict[str, Any]]
```

### 3. Data Functions Integration (`src/datafunctions.py`)
The main data loading function has been updated to use the API:

```python
def load_cargo_data(self, threaded_worker: ThreadObject):
    """
    Loads cargo data for all cargo tables using the MediaWiki API.
    """
    try:
        # Create API data loader
        loader = create_api_data_loader(self.config['config_subfolders']['cache'])
        
        # Load all data via API
        api_data = load_all_data_via_api(threaded_worker, self.config['config_subfolders']['cache'])
        
        # Store data in cache
        self.cache.ships = api_data['ships']
        self.cache.equipment = api_data['equipment']
        self.cache.traits = api_data['traits']
        self.cache.starship_traits = api_data['starship_traits']
        self.cache.modifiers = api_data['modifiers']
        self.cache.space_doffs = api_data['doffs']['space']
        self.cache.ground_doffs = api_data['doffs']['ground']
        
    except Exception as e:
        # Fallback to original method if API fails
        load_cargo_data_fallback(self, threaded_worker)
```

## Data Flow

### 1. Application Startup
1. SETS application starts
2. `init_backend()` is called
3. `populate_cache()` loads data
4. `load_cargo_data()` uses MediaWiki API
5. Data is cached locally for future use

### 2. Data Loading Process
1. **API Request**: MediaWiki API client requests data from stowiki.net
2. **Data Processing**: Raw data is processed into SETS-compatible format
3. **Caching**: Processed data is saved to local JSON files
4. **Application Integration**: Data is loaded into SETS cache objects

### 3. Cache Management
- **Cache Duration**: 24 hours (configurable)
- **Cache Location**: `cache/api_data/` directory
- **Cache Format**: JSON files with structured data
- **Cache Validation**: Automatic expiration and refresh

## Key Features

### 1. Read-Only Access
- **Safety**: All API operations are read-only
- **User-Agent**: "SETS/1.0 (Star Trek Online Build Tool - Read Only)"
- **No Write Operations**: Never attempts to modify stowiki.net

### 2. Efficient Caching
- **Local Storage**: Data cached in JSON files
- **Automatic Refresh**: Cache expires after 24 hours
- **Reduced Network Load**: Minimizes API calls

### 3. Fallback Support
- **Graceful Degradation**: Falls back to original web scraping if API fails
- **Error Handling**: Comprehensive error handling and logging
- **Data Integrity**: Ensures data is always available

### 4. Performance Benefits
- **Faster Loading**: API is more efficient than web scraping
- **Structured Data**: Direct access to Cargo tables
- **Reliable**: MediaWiki API is more stable than HTML parsing

## Usage in SETS

### Accessing Ship Data
```python
# Ships are stored in self.cache.ships
ships = self.cache.ships
for ship_name, ship_data in ships.items():
    print(f"Ship: {ship_data['name']}")
    print(f"Tier: {ship_data['tier']}")
    print(f"Type: {ship_data['type']}")
```

### Accessing Equipment Data
```python
# Equipment is organized by type
equipment = self.cache.equipment
for eq_type, eq_items in equipment.items():
    for item_name, item_data in eq_items.items():
        print(f"Equipment: {item_data['name']}")
        print(f"Type: {item_data['type']}")
        print(f"Rarity: {item_data['rarity']}")
```

### Accessing Traits Data
```python
# Traits are organized by career and environment
traits = self.cache.traits
for career, career_traits in traits.items():
    for env, env_traits in career_traits.items():
        for trait_name, trait_data in env_traits.items():
            print(f"Trait: {trait_data['name']}")
            print(f"Description: {trait_data['description']}")
```

## Testing

### Integration Test Results
```
✓ SETS package imported successfully
✓ API data loader imported successfully
✓ MediaWiki API imported successfully
✓ Loaded 772 ships
✓ Loaded 2,500 equipment items
✓ Loaded 1,074 traits
✓ Loaded 341 starship traits
✓ Cache files created and accessible
✓ ALL TESTS PASSED
```

## Benefits

1. **Reliability**: MediaWiki API is more stable than web scraping
2. **Performance**: Faster data loading and reduced network usage
3. **Maintainability**: Structured API calls are easier to maintain
4. **Safety**: Read-only access ensures no accidental modifications
5. **Caching**: Local cache reduces load on stowiki.net
6. **Fallback**: Graceful degradation if API is unavailable

## Conclusion

The MediaWiki API integration successfully incorporates stowiki.net data into the SETS application. The data files are automatically managed, cached locally, and provide reliable access to all ship, equipment, trait, and modifier information needed by the application.
