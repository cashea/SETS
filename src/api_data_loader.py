"""
API-based Data Loader for SETS

This module provides API-based data loading functionality that replaces
web scraping with MediaWiki API calls for better performance and reliability.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .mediawiki_api import CachedMediaWikiAPI
from .constants import EQUIPMENT_TYPES, CAREERS
from .textedit import create_equipment_tooltip, create_trait_tooltip, sanitize_equipment_name, parse_wikitext
from .widgets import TagStyles


class APIDataLoader:
    """
    API-based data loader that uses MediaWiki API instead of web scraping.
    """
    
    def __init__(self, cache_dir: str = "cache", api_cache_duration: int = 86400):
        """
        Initialize the API data loader.
        
        Args:
            cache_dir: Directory for caching data
            api_cache_duration: Cache duration in seconds (default: 24 hours)
        """
        self.api = CachedMediaWikiAPI(cache_dir=cache_dir, cache_duration=api_cache_duration)
        self.cache_dir = cache_dir
        
        # Create cache directories
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, "api_data"), exist_ok=True)
    
    def load_ships_data(self, threaded_worker=None) -> Dict[str, Any]:
        """
        Load ships data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            Dictionary mapping ship pages to ship data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Starships via API')
        
        logging.info("Loading ships data via API...")
        
        try:
            ships_data = self.api.get_ships_data()
            ships_dict = {ship['Page']: ship for ship in ships_data}
            
            logging.info(f"Loaded {len(ships_dict)} ships via API")
            return ships_dict
            
        except Exception as e:
            logging.error(f"Error loading ships data: {e}")
            return {}
    
    def load_equipment_data(self, threaded_worker=None, theme=None) -> Dict[str, Dict[str, Any]]:
        """
        Load equipment data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            theme: Theme dictionary for styling tooltips
            
        Returns:
            Dictionary mapping equipment types to equipment data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Equipment via API')
        
        logging.info("Loading equipment data via API...")
        
        try:
            equipment_data = self.api.get_equipment_data()
            equipment_dict = {eq_type: {} for eq_type in EQUIPMENT_TYPES.values()}
            
            # Initialize tag styles for tooltips
            if theme:
                head_s = theme.get('tooltip', {}).get('equipment_head', "font-weight: bold; color: #ffffff;")
                subhead_s = theme.get('tooltip', {}).get('equipment_subhead', "font-weight: bold; color: #cccccc;")
                who_s = theme.get('tooltip', {}).get('equipment_who', "color: #888888;")
                tags = TagStyles(
                    theme.get('tooltip', {}).get('ul', "list-style-type: disc;"),
                    theme.get('tooltip', {}).get('li', "margin: 2px 0;"),
                    theme.get('tooltip', {}).get('indent', "margin-left: 20px;")
                )
            else:
                head_s = "font-weight: bold; color: #ffffff;"
                subhead_s = "font-weight: bold; color: #cccccc;"
                who_s = "color: #888888;"
                tags = TagStyles("list-style-type: disc;", "margin: 2px 0;", "margin-left: 20px;")
            
            elite_hangar = {
                'Hangar - Elite Federation Mission Scout Ships',
                'Hangar - Elite Valor Fighters'
            }
            
            equipment_types = set(EQUIPMENT_TYPES.keys())
            
            for item in equipment_data:
                if item['type'] in equipment_types:
                    # Skip certain hangar types
                    if (item['type'] == 'Hangar Bay' and 
                        item['name'] not in elite_hangar and
                        (item['name'].startswith('Hangar - Advanced') or 
                         item['name'].startswith('Hangar - Elite'))):
                        continue
                    
                    name = sanitize_equipment_name(item['name'])
                    equipment_dict[EQUIPMENT_TYPES[item['type']]][name] = {
                        'Page': item['Page'],
                        'name': name,
                        'rarity': item['rarity'],
                        'type': item['type'],
                        'tooltip': create_equipment_tooltip(item, head_s, subhead_s, who_s, tags),
                        # Preserve raw API data for stat parsing
                        'raw_data': item
                    }
                    print(f"Debug: Added raw_data for {name}")
            
            # Handle equipment type mappings
            equipment_dict['fore_weapons'].update(equipment_dict['ship_weapon'])
            equipment_dict['aft_weapons'].update(equipment_dict['ship_weapon'])
            if 'ship_weapon' in equipment_dict:
                del equipment_dict['ship_weapon']
            
            equipment_dict['tac_consoles'].update(equipment_dict['uni_consoles'])
            equipment_dict['sci_consoles'].update(equipment_dict['uni_consoles'])
            equipment_dict['eng_consoles'].update(equipment_dict['uni_consoles'])
            equipment_dict['uni_consoles'].update(equipment_dict['tac_consoles'])
            equipment_dict['uni_consoles'].update(equipment_dict['sci_consoles'])
            equipment_dict['uni_consoles'].update(equipment_dict['eng_consoles'])
            
            logging.info(f"Loaded equipment data via API")
            return equipment_dict
            
        except Exception as e:
            logging.error(f"Error loading equipment data: {e}")
            return {eq_type: {} for eq_type in EQUIPMENT_TYPES.values()}
    
    def load_traits_data(self, threaded_worker=None, theme=None) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Load traits data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            theme: Theme dictionary for styling tooltips
            
        Returns:
            Dictionary mapping environments to trait types to trait data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Traits via API')
        
        logging.info("Loading traits data via API...")
        
        try:
            traits_data = self.api.get_traits_data()
            traits_dict = {
                'space': {'personal': {}, 'rep': {}, 'active_rep': {}},
                'ground': {'personal': {}, 'rep': {}, 'active_rep': {}}
            }
            
            # Initialize tag styles for tooltips
            if theme:
                head_s = theme.get('tooltip', {}).get('trait_header', "font-weight: bold; color: #ffffff;")
                subhead_s = theme.get('tooltip', {}).get('trait_subheader', "font-weight: bold; color: #cccccc;")
                tags = TagStyles(
                    theme.get('tooltip', {}).get('ul', "list-style-type: disc;"),
                    theme.get('tooltip', {}).get('li', "margin: 2px 0;"),
                    theme.get('tooltip', {}).get('indent', "margin-left: 20px;")
                )
            else:
                head_s = "font-weight: bold; color: #ffffff;"
                subhead_s = "font-weight: bold; color: #cccccc;"
                tags = TagStyles("list-style-type: disc;", "margin: 2px 0;", "margin-left: 20px;")
            
            for trait in traits_data:
                name = trait['name']
                if trait['chartype'] == 'char' and name is not None:
                    if trait['type'] == 'reputation':
                        trait_type = 'rep'
                    elif trait['type'] == 'activereputation':
                        trait_type = 'active_rep'
                    else:
                        trait_type = 'personal'
                    
                    try:
                        environment = trait['environment']
                        if environment in traits_dict:
                            traits_dict[environment][trait_type][name] = {
                                'Page': trait['Page'],
                                'name': name,
                                'tooltip': create_trait_tooltip(
                                    name, trait['description'], trait_type, environment, 
                                    head_s, subhead_s, tags)
                            }
                    except KeyError:
                        pass
            
            logging.info(f"Loaded traits data via API")
            return traits_dict
            
        except Exception as e:
            logging.error(f"Error loading traits data: {e}")
            return {
                'space': {'personal': {}, 'rep': {}, 'active_rep': {}},
                'ground': {'personal': {}, 'rep': {}, 'active_rep': {}}
            }
    
    def load_starship_traits_data(self, threaded_worker=None, theme=None) -> Dict[str, Any]:
        """
        Load starship traits data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            theme: Theme dictionary for styling tooltips
            
        Returns:
            Dictionary mapping trait names to trait data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Starship Traits via API')
        
        logging.info("Loading starship traits data via API...")
        
        try:
            starship_traits_data = self.api.get_starship_traits_data()
            
            # Initialize tag styles for tooltips
            if theme:
                head_s = theme.get('tooltip', {}).get('trait_header', "font-weight: bold; color: #ffffff;")
                subhead_s = theme.get('tooltip', {}).get('trait_subheader', "font-weight: bold; color: #cccccc;")
                tags = TagStyles(
                    theme.get('tooltip', {}).get('ul', "list-style-type: disc;"),
                    theme.get('tooltip', {}).get('li', "margin: 2px 0;"),
                    theme.get('tooltip', {}).get('indent', "margin-left: 20px;")
                )
            else:
                head_s = "font-weight: bold; color: #ffffff;"
                subhead_s = "font-weight: bold; color: #cccccc;"
                tags = TagStyles("list-style-type: disc;", "margin: 2px 0;", "margin-left: 20px;")
            
            starship_traits_dict = {}
            for trait in starship_traits_data:
                name = trait['name']
                if name:
                    starship_traits_dict[name] = {
                        'Page': trait['Page'],
                        'name': name,
                        'obtained': trait['obtained'],
                        'tooltip': (
                            f"<p style='{head_s}'>{name}</p>"
                            f"<p style='{subhead_s}'>Starship Trait</p>"
                            f"<p style='margin:0'>{trait['short']}</p>"
                            f"{parse_wikitext(trait['detailed'], tags)}")
                    }
            
            logging.info(f"Loaded {len(starship_traits_dict)} starship traits via API")
            return starship_traits_dict
            
        except Exception as e:
            logging.error(f"Error loading starship traits data: {e}")
            return {}
    
    def load_doff_data(self, threaded_worker=None) -> Dict[str, Dict[str, Any]]:
        """
        Load duty officer data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            Dictionary mapping environments to doff data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Duty Officers via API')
        
        logging.info("Loading duty officer data via API...")
        
        try:
            doff_data = self.api.get_doff_data()
            
            space_doffs = {}
            ground_doffs = {}
            
            for doff in doff_data:
                spec = doff.get('spec', '')
                if spec:
                    # Create separate entries for each rarity level that has content
                    rarities = ['white', 'green', 'blue', 'purple', 'violet', 'gold']
                    
                    for rarity in rarities:
                        description = doff.get(rarity, '')
                        if description and isinstance(description, str):
                            description = description.strip()
                            if description:  # Only create entry if description exists
                                doff_info = {
                                'spec': spec,
                                'shipdutytype': doff.get('shipdutytype', ''),
                                'department': doff.get('department', ''),
                                'description': description,
                                'rarity': rarity
                            }
                            
                            # Determine if it's space or ground based on shipdutytype (like the original method)
                            shipdutytype = doff.get('shipdutytype', '')
                            if shipdutytype == 'Space':
                                if spec not in space_doffs:
                                    space_doffs[spec] = {}
                                space_doffs[spec][description] = doff_info
                            elif shipdutytype == 'Ground':
                                if spec not in ground_doffs:
                                    ground_doffs[spec] = {}
                                ground_doffs[spec][description] = doff_info
                            elif shipdutytype is not None and shipdutytype != '':
                                # If it's not explicitly Space or Ground, add to both (like original method)
                                if spec not in space_doffs:
                                    space_doffs[spec] = {}
                                if spec not in ground_doffs:
                                    ground_doffs[spec] = {}
                                space_doffs[spec][description] = doff_info
                                ground_doffs[spec][description] = doff_info
                            else:
                                # Fallback: try to determine from department
                                department = doff.get('department', '').lower()
                                if 'space' in department or 'ship' in department:
                                    if spec not in space_doffs:
                                        space_doffs[spec] = {}
                                    space_doffs[spec][description] = doff_info
                                else:
                                    if spec not in ground_doffs:
                                        ground_doffs[spec] = {}
                                    ground_doffs[spec][description] = doff_info
            
            logging.info(f"Loaded {len(space_doffs)} space and {len(ground_doffs)} ground doffs via API")
            return {
                'space': space_doffs,
                'ground': ground_doffs
            }
            
        except Exception as e:
            logging.error(f"Error loading doff data: {e}")
            return {'space': {}, 'ground': {}}
    
    def load_modifiers_data(self, threaded_worker=None) -> Dict[str, Dict[str, Any]]:
        """
        Load modifiers data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            Dictionary mapping equipment types to modifier data
        """
        if threaded_worker:
            threaded_worker.update_splash.emit('Loading: Modifiers via API')
        
        logging.info("Loading modifiers data via API...")
        
        try:
            modifiers_data = self.api.get_modifiers_data()
            modifiers_dict = {eq_type: {} for eq_type in EQUIPMENT_TYPES.values()}
            
            for modifier in modifiers_data:
                try:
                    # Handle available field
                    available = modifier.get('available', [])
                    if isinstance(available, list) and len(available) > 0 and available[0] == '':
                        available = []
                    
                    # Process each type for this modifier
                    for mod_type in modifier.get('type', []):
                        mod_name = modifier['modifier'].replace('&gt;', '>')
                        
                        try:
                            epic = bool(modifier.get('isepic', False))
                            modifiers_dict[EQUIPMENT_TYPES[mod_type]][mod_name] = {
                                'stats': modifier.get('stats', ''),
                                'available': available,
                                'epic': epic,
                                'isunique': False if epic else bool(modifier.get('isunique', False)),
                            }
                        except KeyError:
                            # Skip if equipment type not found
                            pass
                            
                except Exception as e:
                    logging.warning(f"Error processing modifier {modifier.get('modifier', 'unknown')}: {e}")
                    continue
            
            # Handle equipment type mappings
            modifiers_dict['fore_weapons'].update(modifiers_dict['ship_weapon'])
            modifiers_dict['aft_weapons'].update(modifiers_dict['ship_weapon'])
            if 'ship_weapon' in modifiers_dict:
                del modifiers_dict['ship_weapon']
            
            logging.info(f"Loaded modifiers data via API")
            return modifiers_dict
            
        except Exception as e:
            logging.error(f"Error loading modifiers data: {e}")
            return {eq_type: {} for eq_type in EQUIPMENT_TYPES.values()}
    
    def get_images_set(self, equipment_dict: Dict, traits_dict: Dict, 
                       starship_traits_dict: Dict) -> set:
        """
        Extract image names from loaded data.
        
        Args:
            equipment_dict: Equipment data dictionary
            traits_dict: Traits data dictionary
            starship_traits_dict: Starship traits data dictionary
            
        Returns:
            Set of image names
        """
        images_set = set()
        
        # Add equipment names
        for eq_type_data in equipment_dict.values():
            images_set.update(eq_type_data.keys())
        
        # Add trait names
        for env_data in traits_dict.values():
            for trait_type_data in env_data.values():
                images_set.update(trait_type_data.keys())
        
        # Add starship trait names
        images_set.update(starship_traits_dict.keys())
        
        return images_set
    
    def clear_api_cache(self):
        """Clear the API cache."""
        self.api.clear_cache()
        logging.info("Cleared API cache")


def create_api_data_loader(cache_dir: str = "cache") -> APIDataLoader:
    """
    Create an API data loader instance.
    
    Args:
        cache_dir: Directory for caching data
        
    Returns:
        Configured APIDataLoader instance
    """
    return APIDataLoader(cache_dir=cache_dir)


def load_all_data_via_api(threaded_worker=None, cache_dir: str = "cache", theme=None) -> Dict[str, Any]:
    """
    Load all data using the MediaWiki API.
    
    Args:
        threaded_worker: Optional worker for progress updates
        cache_dir: Directory for caching data
        theme: Theme dictionary for styling tooltips
        
    Returns:
        Dictionary containing all loaded data
    """
    loader = create_api_data_loader(cache_dir)
    
    # Load all data types
    ships = loader.load_ships_data(threaded_worker)
    equipment = loader.load_equipment_data(threaded_worker, theme)
    traits = loader.load_traits_data(threaded_worker, theme)
    starship_traits = loader.load_starship_traits_data(threaded_worker, theme)
    doffs = loader.load_doff_data(threaded_worker)
    modifiers = loader.load_modifiers_data(threaded_worker)
    
    # Get images set
    images_set = loader.get_images_set(equipment, traits, starship_traits)
    
    return {
        'ships': ships,
        'equipment': equipment,
        'traits': traits,
        'starship_traits': starship_traits,
        'doffs': doffs,
        'modifiers': modifiers,
        'images_set': images_set
    }


if __name__ == "__main__":
    # Test the API data loader
    print("Testing API Data Loader...")
    
    loader = create_api_data_loader("test_cache_api")
    
    # Test loading ships
    print("Loading ships...")
    ships = loader.load_ships_data()
    print(f"Loaded {len(ships)} ships")
    
    # Test loading equipment
    print("Loading equipment...")
    equipment = loader.load_equipment_data()
    print(f"Loaded equipment for {len(equipment)} types")
    
    # Test loading traits
    print("Loading traits...")
    traits = loader.load_traits_data()
    print(f"Loaded traits for {len(traits)} environments")
    
    print("API Data Loader test completed successfully!")
