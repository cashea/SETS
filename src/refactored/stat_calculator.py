"""
Stat Calculator - Handles all stat calculation operations.

This module refactors the stat calculation logic from the original codebase,
providing a clean interface for calculating ship statistics with better separation of concerns.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StatType(Enum):
    """Ship stat types for better type safety."""
    HULL = "hull"
    SHIELDS = "shields"
    TURN_RATE = "turn_rate"
    IMPULSE = "impulse"
    INERTIA = "inertia"
    POWER_WEAPONS = "power_weapons"
    POWER_SHIELDS = "power_shields"
    POWER_ENGINES = "power_engines"
    POWER_AUXILIARY = "power_auxiliary"
    FORE_WEAPONS = "fore_weapons"
    AFT_WEAPONS = "aft_weapons"
    DEVICES = "devices"
    HANGARS = "hangars"


@dataclass
class ShipStats:
    """Represents ship statistics with base values and bonuses."""
    base_stats: Dict[str, float]
    equipment_bonuses: Dict[str, float]
    trait_bonuses: Dict[str, float]
    skill_bonuses: Dict[str, float]
    
    @property
    def total_bonuses(self) -> Dict[str, float]:
        """Calculate total bonuses from all sources."""
        total = {}
        for stat in self.base_stats.keys():
            total[stat] = (
                self.equipment_bonuses.get(stat, 0) +
                self.trait_bonuses.get(stat, 0) +
                self.skill_bonuses.get(stat, 0)
            )
        return total
    
    @property
    def final_stats(self) -> Dict[str, float]:
        """Calculate final stats (base + bonuses)."""
        final = {}
        for stat, base_value in self.base_stats.items():
            bonus = self.total_bonuses.get(stat, 0)
            final[stat] = base_value + bonus
        return final


class StatCalculator:
    """
    Calculates ship statistics including base stats, equipment bonuses, trait bonuses, and skill bonuses.
    
    This class refactors the stat calculation logic from the original codebase,
    providing a cleaner interface with better error handling and separation of concerns.
    """
    
    def __init__(self, equipment_manager, cache_manager):
        self.equipment_manager = equipment_manager
        self.cache_manager = cache_manager
    
    def calculate_ship_stats(self, ship_name: str, build_data: Dict[str, Any]) -> ShipStats:
        """
        Calculate complete ship statistics.
        
        Args:
            ship_name: Name of the selected ship
            build_data: Current build data
            
        Returns:
            ShipStats object with all calculated statistics
        """
        try:
            # Get base ship stats
            base_stats = self._get_base_ship_stats(ship_name)
            
            # Calculate equipment bonuses
            equipment_bonuses = self.equipment_manager.get_equipment_bonuses(build_data)
            
            # Calculate trait bonuses
            trait_bonuses = self._calculate_trait_bonuses(build_data)
            
            # Calculate skill bonuses
            skill_bonuses = self._calculate_skill_bonuses(build_data)
            
            return ShipStats(
                base_stats=base_stats,
                equipment_bonuses=equipment_bonuses,
                trait_bonuses=trait_bonuses,
                skill_bonuses=skill_bonuses
            )
            
        except Exception as e:
            logger.error(f"Error calculating ship stats: {e}")
            return ShipStats(
                base_stats={},
                equipment_bonuses={},
                trait_bonuses={},
                skill_bonuses={}
            )
    
    def _get_base_ship_stats(self, ship_name: str) -> Dict[str, float]:
        """
        Get base ship statistics from ship data.
        
        Args:
            ship_name: Name of the ship
            
        Returns:
            Dictionary of base ship stats
        """
        try:
            if not ship_name or ship_name not in self.cache_manager.ships:
                return {}
            
            ship_data = self.cache_manager.ships[ship_name]
            
            return {
                'hull': float(ship_data.get('hull', 0) or 0),
                'shields': float(ship_data.get('shieldmod', 1.0) or 1.0),
                'turn_rate': float(ship_data.get('turnrate', 0) or 0),
                'impulse': float(ship_data.get('impulse', 0) or 0),
                'inertia': float(ship_data.get('inertia', 0) or 0),
                'power_weapons': float(ship_data.get('powerweapons', 0) or 0),
                'power_shields': float(ship_data.get('powershields', 0) or 0),
                'power_engines': float(ship_data.get('powerengines', 0) or 0),
                'power_auxiliary': float(ship_data.get('powerauxiliary', 0) or 0),
                'fore_weapons': float(ship_data.get('fore', 0) or 0),
                'aft_weapons': float(ship_data.get('aft', 0) or 0),
                'devices': float(ship_data.get('devices', 0) or 0),
                'hangars': float(ship_data.get('hangars', 0) or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting base ship stats for '{ship_name}': {e}")
            return {}
    
    def _calculate_trait_bonuses(self, build_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate bonuses from selected traits.
        
        Args:
            build_data: Build data containing trait selections
            
        Returns:
            Dictionary of trait bonuses
        """
        bonuses = {}
        
        try:
            # Check personal traits
            if 'traits' in build_data:
                for trait_data in build_data['traits']:
                    if self._is_valid_trait_item(trait_data):
                        trait_name = trait_data['item']
                        trait_bonuses = self._parse_trait_bonuses(trait_name, 'personal')
                        bonuses.update(trait_bonuses)
            
            # Check starship traits
            if 'starship_traits' in build_data:
                for trait_data in build_data['starship_traits']:
                    if self._is_valid_trait_item(trait_data):
                        trait_name = trait_data['item']
                        trait_bonuses = self._parse_trait_bonuses(trait_name, 'starship')
                        bonuses.update(trait_bonuses)
            
            logger.debug(f"Calculated trait bonuses: {bonuses}")
            return bonuses
            
        except Exception as e:
            logger.error(f"Error calculating trait bonuses: {e}")
            return bonuses
    
    def _is_valid_trait_item(self, trait_data: Any) -> bool:
        """Check if trait data represents a valid trait item."""
        return (trait_data and 
                isinstance(trait_data, dict) and 
                'item' in trait_data and 
                trait_data['item'])
    
    def _parse_trait_bonuses(self, trait_name: str, trait_type: str) -> Dict[str, float]:
        """
        Parse trait effects for stat bonuses.
        
        Args:
            trait_name: Name of the trait
            trait_type: Type of trait (personal/starship)
            
        Returns:
            Dictionary of stat bonuses
        """
        bonuses = {}
        
        try:
            if trait_type == 'personal':
                # Look in personal traits
                for env in ['space', 'ground']:
                    if trait_name in self.cache_manager.traits.get(env, {}).get('personal', {}):
                        trait_info = self.cache_manager.traits[env]['personal'][trait_name]
                        if 'tooltip' in trait_info:
                            bonuses.update(self._parse_stat_text('', trait_info['tooltip']))
                        break
                        
            elif trait_type == 'starship':
                # Look in starship traits
                if trait_name in self.cache_manager.starship_traits:
                    trait_info = self.cache_manager.starship_traits[trait_name]
                    if 'tooltip' in trait_info:
                        bonuses.update(self._parse_stat_text('', trait_info['tooltip']))
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error parsing trait bonuses for '{trait_name}': {e}")
            return bonuses
    
    def _calculate_skill_bonuses(self, build_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate bonuses from skill tree selections.
        
        Args:
            build_data: Build data containing skill selections
            
        Returns:
            Dictionary of skill bonuses
        """
        # This is a placeholder for skill bonus calculation
        # The original codebase doesn't seem to have comprehensive skill bonus calculation
        # This would need to be implemented based on the skill system
        return {}
    
    def _parse_stat_text(self, head_text: str, text_content: str) -> Dict[str, float]:
        """
        Parse text content for stat bonuses using regex patterns.
        
        Args:
            head_text: Header text
            text_content: Content text
            
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
    
    def format_stat_value(self, value: float, stat_type: str = None) -> str:
        """
        Format stat value for display.
        
        Args:
            value: Stat value to format
            stat_type: Type of stat (for special formatting)
            
        Returns:
            Formatted string representation
        """
        if isinstance(value, float):
            return f"{value:.1f}"
        else:
            return str(value)
    
    def get_stat_display_name(self, stat_name: str) -> str:
        """
        Get display name for a stat.
        
        Args:
            stat_name: Internal stat name
            
        Returns:
            Display name for the stat
        """
        display_names = {
            'hull': 'Hull',
            'shields': 'Shields',
            'turn_rate': 'Turn Rate',
            'impulse': 'Impulse',
            'inertia': 'Inertia',
            'power_weapons': 'Power Weapons',
            'power_shields': 'Power Shields',
            'power_engines': 'Power Engines',
            'power_auxiliary': 'Power Auxiliary',
            'fore_weapons': 'Fore Weapons',
            'aft_weapons': 'Aft Weapons',
            'devices': 'Devices',
            'hangars': 'Hangars'
        }
        
        return display_names.get(stat_name, stat_name.replace('_', ' ').title())
