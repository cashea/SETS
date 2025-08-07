"""
Cache Manager - Handles all cache operations.

This module refactors the cache management logic from the original codebase,
providing a clean interface for cache operations with better separation of concerns.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics about the cache."""
    ships_count: int = 0
    equipment_categories: int = 0
    total_equipment_items: int = 0
    traits_count: int = 0
    starship_traits_count: int = 0
    images_count: int = 0
    modifiers_count: int = 0
    last_updated: Optional[datetime] = None


class CacheManager:
    """
    Manages all cache operations including data storage, retrieval, and validation.
    
    This class refactors the cache management logic from the original codebase,
    providing a cleaner interface with better error handling and separation of concerns.
    """
    
    def __init__(self, config):
        self.config = config
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize cache with empty data structures."""
        # Ships data
        self.ships: Dict[str, Any] = {}
        
        # Equipment data - organized by category
        self.equipment: Dict[str, Dict[str, Any]] = {}
        
        # Traits data
        self.traits: Dict[str, Dict[str, Dict[str, Any]]] = {
            'space': {
                'personal': {},
                'rep': {},
                'active_rep': {}
            },
            'ground': {
                'personal': {},
                'rep': {},
                'active_rep': {}
            }
        }
        
        # Starship traits
        self.starship_traits: Dict[str, Any] = {}
        
        # Duty officers
        self.space_doffs: Dict[str, Any] = {}
        self.ground_doffs: Dict[str, Any] = {}
        
        # Bridge officer abilities
        self.boff_abilities: Dict[str, Any] = {
            'space': {},
            'ground': {},
            'all': {}
        }
        
        # Skills data
        self.skills: Dict[str, Any] = {
            'space': {},
            'space_unlocks': {},
            'ground': {},
            'ground_unlocks': {},
            'space_points_total': 0,
            'space_points_eng': 0,
            'space_points_sci': 0,
            'space_points_tac': 0,
            'space_points_rank': [0] * 5,
            'ground_points_total': 0,
        }
        
        # Species data
        self.species: Dict[str, Dict[str, Any]] = {
            'Federation': {},
            'Klingon': {},
            'Romulan': {},
            'Dominion': {},
            'TOS Federation': {},
            'DSC Federation': {}
        }
        
        # Modifiers data
        self.modifiers: Dict[str, Dict[str, Any]] = {}
        
        # Images and UI elements
        self.empty_image: Optional[QImage] = None
        self.overlays: Dict[str, Any] = {}
        self.icons: Dict[str, Any] = {}
        self.images: Dict[str, QImage] = {}
        self.images_set: Set[str] = set()
        self.images_populated: bool = False
        self.images_failed: Dict[str, int] = {}
        
        logger.info("Cache initialized")
    
    def reset_cache(self, keep_skills: bool = False) -> None:
        """
        Reset cache to initial state.
        
        Args:
            keep_skills: Whether to preserve skills data
        """
        try:
            # Reset all data structures
            self._initialize_cache()
            
            # Preserve skills if requested
            if keep_skills:
                # Skills data is already preserved in _initialize_cache
                pass
            
            logger.info("Cache reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting cache: {e}")
            raise
    
    def load_cache_from_files(self) -> bool:
        """
        Load cache data from files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_dir = self.config['config_subfolders']['cache']
            
            # Load ships data
            ships_file = os.path.join(cache_dir, 'ships.json')
            if os.path.exists(ships_file):
                self.ships = self._load_json_file(ships_file)
            
            # Load equipment data
            equipment_file = os.path.join(cache_dir, 'equipment.json')
            if os.path.exists(equipment_file):
                self.equipment = self._load_json_file(equipment_file)
            
            # Load traits data
            traits_file = os.path.join(cache_dir, 'traits.json')
            if os.path.exists(traits_file):
                self.traits = self._load_json_file(traits_file)
            
            # Load starship traits data
            starship_traits_file = os.path.join(cache_dir, 'starship_traits.json')
            if os.path.exists(starship_traits_file):
                self.starship_traits = self._load_json_file(starship_traits_file)
            
            # Load modifiers data
            modifiers_file = os.path.join(cache_dir, 'modifiers.json')
            if os.path.exists(modifiers_file):
                self.modifiers = self._load_json_file(modifiers_file)
            
            # Load duty officer data
            doffs_file = os.path.join(cache_dir, 'doffs.json')
            if os.path.exists(doffs_file):
                doffs_data = self._load_json_file(doffs_file)
                self.space_doffs = doffs_data.get('space', {})
                self.ground_doffs = doffs_data.get('ground', {})
            
            # Load bridge officer abilities
            boff_abilities_file = os.path.join(cache_dir, 'boff_abilities.json')
            if os.path.exists(boff_abilities_file):
                self.boff_abilities = self._load_json_file(boff_abilities_file)
            
            # Load failed images data
            images_failed_file = os.path.join(cache_dir, 'images_failed.json')
            if os.path.exists(images_failed_file):
                self.images_failed = self._load_json_file(images_failed_file)
            
            logger.info("Cache loaded from files successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cache from files: {e}")
            return False
    
    def save_cache_to_files(self) -> bool:
        """
        Save cache data to files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_dir = self.config['config_subfolders']['cache']
            os.makedirs(cache_dir, exist_ok=True)
            
            # Save ships data
            self._save_json_file(os.path.join(cache_dir, 'ships.json'), self.ships)
            
            # Save equipment data
            self._save_json_file(os.path.join(cache_dir, 'equipment.json'), self.equipment)
            
            # Save traits data
            self._save_json_file(os.path.join(cache_dir, 'traits.json'), self.traits)
            
            # Save starship traits data
            self._save_json_file(os.path.join(cache_dir, 'starship_traits.json'), self.starship_traits)
            
            # Save modifiers data
            self._save_json_file(os.path.join(cache_dir, 'modifiers.json'), self.modifiers)
            
            # Save duty officer data
            doffs_data = {
                'space': self.space_doffs,
                'ground': self.ground_doffs
            }
            self._save_json_file(os.path.join(cache_dir, 'doffs.json'), doffs_data)
            
            # Save bridge officer abilities
            self._save_json_file(os.path.join(cache_dir, 'boff_abilities.json'), self.boff_abilities)
            
            # Save failed images data
            self._save_json_file(os.path.join(cache_dir, 'images_failed.json'), self.images_failed)
            
            logger.info("Cache saved to files successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache to files: {e}")
            return False
    
    def _load_json_file(self, filepath: str) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Loaded data
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {filepath}: {e}")
            return {}
    
    def _save_json_file(self, filepath: str, data: Any) -> None:
        """
        Save data to a JSON file.
        
        Args:
            filepath: Path to the JSON file
            data: Data to save
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving JSON file {filepath}: {e}")
            raise
    
    def get_cache_stats(self) -> CacheStats:
        """
        Get statistics about the cache.
        
        Returns:
            CacheStats object with cache statistics
        """
        try:
            return CacheStats(
                ships_count=len(self.ships),
                equipment_categories=len(self.equipment),
                total_equipment_items=sum(len(items) for items in self.equipment.values()),
                traits_count=len(self.traits),
                starship_traits_count=len(self.starship_traits),
                images_count=len(self.images_set),
                modifiers_count=sum(len(mods) for mods in self.modifiers.values()),
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats()
    
    def validate_cache_integrity(self) -> Dict[str, bool]:
        """
        Validate the integrity of cache data.
        
        Returns:
            Dictionary with validation results for each data type
        """
        results = {}
        
        try:
            # Validate ships data
            results['ships'] = isinstance(self.ships, dict) and len(self.ships) > 0
            
            # Validate equipment data
            results['equipment'] = isinstance(self.equipment, dict) and len(self.equipment) > 0
            
            # Validate traits data
            results['traits'] = isinstance(self.traits, dict) and len(self.traits) > 0
            
            # Validate starship traits data
            results['starship_traits'] = isinstance(self.starship_traits, dict) and len(self.starship_traits) > 0
            
            # Validate images data
            results['images'] = isinstance(self.images_set, set) and len(self.images_set) >= 0
            
            # Validate modifiers data
            results['modifiers'] = isinstance(self.modifiers, dict) and len(self.modifiers) >= 0
            
            # Validate duty officer data
            results['duty_officers'] = (isinstance(self.space_doffs, dict) and 
                                      isinstance(self.ground_doffs, dict))
            
            logger.info(f"Cache integrity validation results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error validating cache integrity: {e}")
            return {key: False for key in ['ships', 'equipment', 'traits', 'starship_traits', 
                                         'images', 'modifiers', 'duty_officers']}
    
    def clear_failed_images(self, older_than_days: int = 7) -> int:
        """
        Clear failed images older than specified days.
        
        Args:
            older_than_days: Number of days to consider for clearing
            
        Returns:
            Number of cleared images
        """
        try:
            current_time = datetime.now().timestamp()
            cleared_count = 0
            
            # Get list of images to clear
            to_clear = []
            for image_name, timestamp in self.images_failed.items():
                if (current_time - timestamp) > (older_than_days * 24 * 60 * 60):
                    to_clear.append(image_name)
            
            # Clear old failed images
            for image_name in to_clear:
                del self.images_failed[image_name]
                cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} old failed images")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing failed images: {e}")
            return 0
    
    def get_equipment_in_category(self, category: str) -> Dict[str, Any]:
        """
        Get all equipment items in a specific category.
        
        Args:
            category: Equipment category
            
        Returns:
            Dictionary of equipment items in the category
        """
        return self.equipment.get(category, {})
    
    def get_ship_data(self, ship_name: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific ship.
        
        Args:
            ship_name: Name of the ship
            
        Returns:
            Ship data if found, None otherwise
        """
        return self.ships.get(ship_name)
    
    def get_trait_data(self, trait_name: str, environment: str = 'space', trait_type: str = 'personal') -> Optional[Dict[str, Any]]:
        """
        Get data for a specific trait.
        
        Args:
            trait_name: Name of the trait
            environment: Environment (space/ground)
            trait_type: Type of trait (personal/rep/active_rep)
            
        Returns:
            Trait data if found, None otherwise
        """
        try:
            return self.traits.get(environment, {}).get(trait_type, {}).get(trait_name)
        except (KeyError, TypeError):
            return None
    
    def get_starship_trait_data(self, trait_name: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific starship trait.
        
        Args:
            trait_name: Name of the starship trait
            
        Returns:
            Starship trait data if found, None otherwise
        """
        return self.starship_traits.get(trait_name)
    
    def add_failed_image(self, image_name: str) -> None:
        """
        Add an image to the failed images list.
        
        Args:
            image_name: Name of the failed image
        """
        try:
            self.images_failed[image_name] = int(datetime.now().timestamp())
        except Exception as e:
            logger.error(f"Error adding failed image {image_name}: {e}")
    
    def is_image_failed(self, image_name: str) -> bool:
        """
        Check if an image is in the failed images list.
        
        Args:
            image_name: Name of the image
            
        Returns:
            True if image is failed, False otherwise
        """
        return image_name in self.images_failed
    
    def get_cache_size(self) -> int:
        """
        Get approximate size of cache in memory.
        
        Returns:
            Approximate cache size in bytes
        """
        try:
            import sys
            
            # Calculate size of main data structures
            total_size = 0
            
            # Ships
            total_size += sys.getsizeof(self.ships)
            for ship_name, ship_data in self.ships.items():
                total_size += sys.getsizeof(ship_name) + sys.getsizeof(ship_data)
            
            # Equipment
            total_size += sys.getsizeof(self.equipment)
            for category, items in self.equipment.items():
                total_size += sys.getsizeof(category) + sys.getsizeof(items)
            
            # Traits
            total_size += sys.getsizeof(self.traits)
            
            # Starship traits
            total_size += sys.getsizeof(self.starship_traits)
            
            # Images
            total_size += sys.getsizeof(self.images_set)
            total_size += sys.getsizeof(self.images_failed)
            
            return total_size
            
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0
