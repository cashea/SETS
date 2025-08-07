"""
Equipment Manager - Handles all equipment-related operations.

This module refactors the equipment handling logic from the original codebase,
providing a clean interface for equipment operations with better separation of concerns.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EquipmentCategory(Enum):
    """Equipment categories for better type safety."""
    FORE_WEAPONS = "fore_weapons"
    AFT_WEAPONS = "aft_weapons"
    DEVICES = "devices"
    DEFLECTOR = "deflector"
    ENGINES = "engines"
    CORE = "core"
    SHIELD = "shield"
    TAC_CONSOLES = "tac_consoles"
    ENG_CONSOLES = "eng_consoles"
    SCI_CONSOLES = "sci_consoles"
    UNI_CONSOLES = "uni_consoles"


class EquipmentRarity(Enum):
    """Equipment rarity levels."""
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    VERY_RARE = "Very Rare"
    ULTRA_RARE = "Ultra Rare"


@dataclass
class EquipmentItem:
    """Represents an equipment item with all its properties."""
    name: str
    category: EquipmentCategory
    rarity: EquipmentRarity
    item_type: str
    tooltip: str
    raw_data: Dict[str, Any]
    modifiers: List[str] = None
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []


class EquipmentManager:
    """
    Manages equipment operations including loading, parsing, and stat calculations.
    
    This class refactors the equipment handling logic from the original codebase,
    providing a cleaner interface with better error handling and separation of concerns.
    """
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.equipment_cache = {}
        self._equipment_categories = [cat.value for cat in EquipmentCategory]
    
    def load_equipment_data(self, api_data: Dict[str, Any]) -> None:
        """
        Load equipment data from API response.
        
        Args:
            api_data: Equipment data from API
        """
        try:
            self.equipment_cache = api_data.get('equipment', {})
            logger.info(f"Loaded {len(self.equipment_cache)} equipment categories")
        except Exception as e:
            logger.error(f"Error loading equipment data: {e}")
            self.equipment_cache = {}
    
    def get_equipment_item(self, item_name: str, category: str = None) -> Optional[EquipmentItem]:
        """
        Get equipment item by name, optionally searching in a specific category.
        
        Args:
            item_name: Name of the equipment item
            category: Optional category to search in
            
        Returns:
            EquipmentItem if found, None otherwise
        """
        try:
            if category and category in self.equipment_cache:
                if item_name in self.equipment_cache[category]:
                    return self._create_equipment_item(item_name, category, self.equipment_cache[category][item_name])
            
            # Search all categories
            for cat, items in self.equipment_cache.items():
                if item_name in items:
                    return self._create_equipment_item(item_name, cat, items[item_name])
            
            logger.warning(f"Equipment item '{item_name}' not found in any category")
            return None
            
        except Exception as e:
            logger.error(f"Error getting equipment item '{item_name}': {e}")
            return None
    
    def _create_equipment_item(self, name: str, category: str, item_data: Dict[str, Any]) -> EquipmentItem:
        """Create EquipmentItem from raw data."""
        try:
            return EquipmentItem(
                name=name,
                category=EquipmentCategory(category),
                rarity=EquipmentRarity(item_data.get('rarity', 'Common')),
                item_type=item_data.get('type', ''),
                tooltip=item_data.get('tooltip', ''),
                raw_data=item_data.get('raw_data', {}),
                modifiers=item_data.get('modifiers', [])
            )
        except Exception as e:
            logger.error(f"Error creating equipment item '{name}': {e}")
            raise
    
    def get_equipment_bonuses(self, build_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate equipment bonuses from build data.
        
        Args:
            build_data: Build data containing equipped items
            
        Returns:
            Dictionary of stat bonuses
        """
        bonuses = {}
        
        try:
            for category in self._equipment_categories:
                if category in build_data:
                    category_items = build_data[category]
                    if isinstance(category_items, list):
                        for item_data in category_items:
                            if self._is_valid_equipment_item(item_data):
                                item_bonuses = self._parse_equipment_bonuses(item_data['item'])
                                if item_bonuses:
                                    bonuses.update(item_bonuses)
            
            logger.debug(f"Calculated equipment bonuses: {bonuses}")
            return bonuses
            
        except Exception as e:
            logger.error(f"Error calculating equipment bonuses: {e}")
            return bonuses
    
    def _is_valid_equipment_item(self, item_data: Any) -> bool:
        """Check if item data represents a valid equipment item."""
        return (item_data and 
                isinstance(item_data, dict) and 
                'item' in item_data and 
                item_data['item'])
    
    def _parse_equipment_bonuses(self, item_name: str) -> Dict[str, float]:
        """
        Parse equipment bonuses from item data.
        
        Args:
            item_name: Name of the equipment item
            
        Returns:
            Dictionary of stat bonuses
        """
        try:
            equipment_item = self.get_equipment_item(item_name)
            if not equipment_item:
                return {}
            
            return self._extract_stat_bonuses(equipment_item.raw_data)
            
        except Exception as e:
            logger.error(f"Error parsing bonuses for '{item_name}': {e}")
            return {}
    
    def _extract_stat_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract stat bonuses from raw equipment data.
        
        Args:
            raw_data: Raw equipment data from API
            
        Returns:
            Dictionary of stat bonuses
        """
        bonuses = {}
        
        try:
            # Parse head and text fields for stat bonuses
            for i in range(1, 10):
                head_key = f'head{i}'
                text_key = f'text{i}'
                
                if head_key in raw_data and raw_data[head_key]:
                    head_text = raw_data[head_key]
                    text_content = raw_data.get(text_key, '')
                    
                    # Parse common stat patterns
                    stat_bonuses = self._parse_stat_text(head_text, text_content)
                    bonuses.update(stat_bonuses)
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error extracting stat bonuses: {e}")
            return bonuses
    
    def _parse_stat_text(self, head_text: str, text_content: str) -> Dict[str, float]:
        """
        Parse text content for stat bonuses using regex patterns.
        
        Args:
            head_text: Header text from equipment data
            text_content: Content text from equipment data
            
        Returns:
            Dictionary of stat bonuses
        """
        import re
        
        bonuses = {}
        
        # Common stat patterns to look for
        stat_patterns = {
            'hull': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?hull',
            'shields': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?shield',
            'turn_rate': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?turn\s+rate',
            'impulse': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?impulse',
            'power_weapons': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?weapon\s+power',
            'power_shields': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?shield\s+power',
            'power_engines': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?engine\s+power',
            'power_auxiliary': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?auxiliary\s+power'
        }
        
        # Combine head and text content for parsing
        full_text = f"{head_text} {text_content}".lower()
        
        for stat_name, pattern in stat_patterns.items():
            matches = re.findall(pattern, full_text)
            if matches:
                try:
                    # Take the first match and convert to float
                    value = float(matches[0])
                    bonuses[stat_name] = value
                except (ValueError, IndexError):
                    continue
        
        return bonuses
    
    def get_equipment_categories(self) -> List[str]:
        """Get list of all equipment categories."""
        return self._equipment_categories.copy()
    
    def get_equipment_in_category(self, category: str) -> Dict[str, Any]:
        """Get all equipment items in a specific category."""
        return self.equipment_cache.get(category, {})
    
    def validate_equipment_item(self, item_name: str, category: str) -> bool:
        """
        Validate that an equipment item exists in the specified category.
        
        Args:
            item_name: Name of the equipment item
            category: Category to check
            
        Returns:
            True if item exists in category, False otherwise
        """
        return (category in self.equipment_cache and 
                item_name in self.equipment_cache[category])
