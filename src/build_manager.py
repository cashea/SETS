from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
from pathlib import Path
from datetime import datetime

class BuildType(Enum):
    SPACE = "space"
    GROUND = "ground"

@dataclass
class EquipmentItem:
    item: str
    mark: str = ""
    modifiers: List[str] = field(default_factory=list)
    
@dataclass
class ShipData:
    name: str
    tier: str
    image: str
    description: str = ""
    
@dataclass
class CharacterData:
    name: str = ""
    career: str = ""
    faction: str = ""
    species: str = ""
    primary_spec: str = ""
    secondary_spec: str = ""
    elite: bool = False

class BuildManager:
    """Manages build state and operations"""
    
    def __init__(self, cache_manager, config):
        self.cache_manager = cache_manager
        self.config = config
        self._build = self._create_empty_build()
        self._autosave_enabled = True
        self._last_modified = datetime.now()
        
    def _create_empty_build(self) -> Dict[str, Any]:
        """Create an empty build structure"""
        return {
            'space': {
                'ship': '',
                'ship_name': '',
                'ship_desc': '',
                'tier': '',
                'fore_weapons': [None] * 5,
                'aft_weapons': [None] * 5,
                'experimental': [None],
                'devices': [None] * 6,
                'hangars': [None] * 2,
                'deflector': [''],
                'sec_def': [None],
                'engines': [''],
                'core': [''],
                'shield': [''],
                'uni_consoles': [None] * 3,
                'eng_consoles': [None] * 5,
                'sci_consoles': [None] * 5,
                'tac_consoles': [None] * 5,
                'boffs': [[None] * 4, [None] * 4, [None] * 4, [None] * 4, [None] * 4, [None] * 4],
                'traits': [None] * 12,
                'starship_traits': [None] * 7,
                'rep_traits': [None] * 5,
                'active_rep_traits': [None] * 5,
                'doffs_spec': [''] * 6,
                'doffs_variant': [''] * 6,
            },
            'ground': {
                'ground_desc': '',
                'weapons': [None] * 2,
                'ground_devices': [None] * 5,
                'kit': [''],
                'armor': [''],
                'kit_modules': [None] * 6,
                'personal_shield': [''],
                'ev_suit': [''],
                'traits': [None] * 12,
                'rep_traits': [None] * 5,
                'active_rep_traits': [None] * 5,
                'boffs': [[''] * 4, [''] * 4, [''] * 4, [''] * 4],
                'boff_profs': [''] * 4,
                'boff_specs': [''] * 4,
                'doffs_spec': [''] * 6,
                'doffs_variant': [''] * 6,
            },
            'captain': {
                'name': '',
                'career': '',
                'faction': '',
                'species': '',
                'primary_spec': '',
                'secondary_spec': '',
                'elite': False
            },
            'space_skills': {
                'eng': [False] * 30,
                'sci': [False] * 30,
                'tac': [False] * 30,
            },
            'ground_skills': [
                [False] * 6,
                [False] * 6,
                [False] * 4,
                [False] * 4
            ],
            'skill_unlocks': {
                'eng': [None] * 5,
                'sci': [None] * 5,
                'tac': [None] * 5,
                'ground': [None] * 5
            },
            'skill_desc': {
                'space': '',
                'ground': ''
            }
        }
    
    @property
    def build(self) -> Dict[str, Any]:
        """Get current build data"""
        return self._build
    
    @property
    def last_modified(self) -> datetime:
        """Get last modification time"""
        return self._last_modified
    
    def set_equipment_item(self, environment: str, slot_type: str, 
                          slot_index: int, item_data: Optional[Dict]) -> bool:
        """Set equipment item in specific slot"""
        try:
            if environment not in self._build:
                return False
                
            if slot_type not in self._build[environment]:
                return False
                
            if not isinstance(self._build[environment][slot_type], list):
                return False
                
            if slot_index >= len(self._build[environment][slot_type]):
                return False
                
            self._build[environment][slot_type][slot_index] = item_data
            self._mark_modified()
            return True
        except (IndexError, KeyError, TypeError):
            return False
    
    def get_equipment_item(self, environment: str, slot_type: str, 
                          slot_index: int) -> Optional[Dict]:
        """Get equipment item from specific slot"""
        try:
            if environment not in self._build:
                return None
            if slot_type not in self._build[environment]:
                return None
            if not isinstance(self._build[environment][slot_type], list):
                return None
            if slot_index >= len(self._build[environment][slot_type]):
                return None
            return self._build[environment][slot_type][slot_index]
        except (IndexError, KeyError, TypeError):
            return None
    
    def set_ship(self, ship_name: str, ship_data: Optional[Dict] = None) -> bool:
        """Set current ship"""
        try:
            if ship_name == '<Pick Ship>' or ship_name == '':
                self._build['space']['ship'] = ''
                self._build['space']['ship_name'] = ''
                self._build['space']['ship_desc'] = ''
                self._build['space']['tier'] = ''
            else:
                self._build['space']['ship'] = ship_name
                if ship_data:
                    self._build['space']['ship_name'] = ship_data.get('name', ship_name)
                    self._build['space']['ship_desc'] = ship_data.get('description', '')
                    self._build['space']['tier'] = ship_data.get('tier', 'T6')
            
            self._mark_modified()
            return True
        except (KeyError, TypeError):
            return False
    
    def set_character_data(self, field: str, value: Any) -> bool:
        """Set character data field"""
        try:
            if field in self._build['captain']:
                self._build['captain'][field] = value
                self._mark_modified()
                return True
            return False
        except (KeyError, TypeError):
            return False
    
    def get_character_data(self, field: str) -> Any:
        """Get character data field"""
        try:
            return self._build['captain'].get(field)
        except (KeyError, TypeError):
            return None
    
    def set_trait_item(self, environment: str, trait_type: str, 
                      trait_index: int, trait_data: Optional[Dict]) -> bool:
        """Set trait item in specific slot"""
        return self.set_equipment_item(environment, trait_type, trait_index, trait_data)
    
    def get_trait_item(self, environment: str, trait_type: str, 
                      trait_index: int) -> Optional[Dict]:
        """Get trait item from specific slot"""
        return self.get_equipment_item(environment, trait_type, trait_index)
    
    def set_boff_ability(self, boff_id: int, ability_index: int, 
                        ability_data: Optional[Dict]) -> bool:
        """Set bridge officer ability"""
        try:
            if boff_id >= len(self._build['space']['boffs']):
                return False
            if ability_index >= len(self._build['space']['boffs'][boff_id]):
                return False
                
            self._build['space']['boffs'][boff_id][ability_index] = ability_data
            self._mark_modified()
            return True
        except (IndexError, KeyError, TypeError):
            return False
    
    def get_boff_ability(self, boff_id: int, ability_index: int) -> Optional[Dict]:
        """Get bridge officer ability"""
        try:
            if boff_id >= len(self._build['space']['boffs']):
                return None
            if ability_index >= len(self._build['space']['boffs'][boff_id]):
                return None
            return self._build['space']['boffs'][boff_id][ability_index]
        except (IndexError, KeyError, TypeError):
            return None
    
    def set_doff_data(self, environment: str, doff_id: int, 
                     doff_type: str, value: str) -> bool:
        """Set duty officer data"""
        try:
            if environment not in self._build:
                return False
            if f'doffs_{doff_type}' not in self._build[environment]:
                return False
            if doff_id >= len(self._build[environment][f'doffs_{doff_type}']):
                return False
                
            self._build[environment][f'doffs_{doff_type}'][doff_id] = value
            self._mark_modified()
            return True
        except (IndexError, KeyError, TypeError):
            return False
    
    def get_doff_data(self, environment: str, doff_id: int, 
                     doff_type: str) -> Optional[str]:
        """Get duty officer data"""
        try:
            if environment not in self._build:
                return None
            if f'doffs_{doff_type}' not in self._build[environment]:
                return None
            if doff_id >= len(self._build[environment][f'doffs_{doff_type}']):
                return None
            return self._build[environment][f'doffs_{doff_type}'][doff_id]
        except (IndexError, KeyError, TypeError):
            return None
    
    def load_build_from_file(self, filepath: str) -> bool:
        """Load build from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_build = json.load(f)
            
            # Validate and merge with current structure
            self._build = self._merge_build_data(self._build, loaded_build)
            self._mark_modified()
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError, IOError):
            return False
    
    def save_build_to_file(self, filepath: str) -> bool:
        """Save current build to JSON file"""
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._build, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError):
            return False
    
    def clear_build(self, build_type: str = 'full') -> None:
        """Clear build data"""
        try:
            if build_type == 'full':
                self._build = self._create_empty_build()
            elif build_type == 'space':
                self._build['space'] = self._create_empty_build()['space']
            elif build_type == 'ground':
                self._build['ground'] = self._create_empty_build()['ground']
            elif build_type == 'captain':
                self._build['captain'] = self._create_empty_build()['captain']
            
            self._mark_modified()
        except (KeyError, TypeError):
            pass
    
    def get_build_summary(self) -> Dict[str, Any]:
        """Get a summary of the current build"""
        try:
            return {
                'ship': self._build['space']['ship'],
                'character_name': self._build['captain']['name'],
                'career': self._build['captain']['career'],
                'faction': self._build['captain']['faction'],
                'species': self._build['captain']['species'],
                'elite': self._build['captain']['elite'],
                'last_modified': self._last_modified.isoformat(),
                'has_space_equipment': any(
                    item is not None and item != '' 
                    for category in self._build['space'].values() 
                    if isinstance(category, list)
                    for item in category
                ),
                'has_ground_equipment': any(
                    item is not None and item != '' 
                    for category in self._build['ground'].values() 
                    if isinstance(category, list)
                    for item in category
                )
            }
        except (KeyError, TypeError):
            return {}
    
    def validate_build(self) -> List[str]:
        """Validate current build and return list of issues"""
        issues = []
        
        try:
            # Check required character fields
            required_fields = ['name', 'career', 'faction', 'species']
            for field in required_fields:
                if not self._build['captain'].get(field):
                    issues.append(f"Missing character {field}")
            
            # Check ship selection
            if not self._build['space']['ship']:
                issues.append("No ship selected")
            
            # Check for invalid equipment references
            for environment in ['space', 'ground']:
                for category, items in self._build[environment].items():
                    if isinstance(items, list):
                        for i, item in enumerate(items):
                            if item and isinstance(item, dict):
                                if 'item' in item and item['item']:
                                    # Could add validation against cache here
                                    pass
            
        except (KeyError, TypeError) as e:
            issues.append(f"Build structure error: {str(e)}")
        
        return issues
    
    def _mark_modified(self) -> None:
        """Mark build as modified and trigger autosave"""
        self._last_modified = datetime.now()
        self._autosave()
    
    def _autosave(self) -> None:
        """Perform autosave if enabled"""
        if self._autosave_enabled:
            try:
                # Handle both dict and object access for config
                if hasattr(self.config, 'autosave_filename'):
                    autosave_filename = self.config.autosave_filename
                elif isinstance(self.config, dict) and 'autosave_filename' in self.config:
                    autosave_filename = self.config['autosave_filename']
                else:
                    return  # No autosave filename configured
                
                autosave_path = Path(autosave_filename)
                self.save_build_to_file(str(autosave_path))
            except (KeyError, IOError, AttributeError):
                # Silently fail autosave to avoid breaking the application
                pass
    
    def _merge_build_data(self, current: Dict, new: Dict) -> Dict:
        """Merge new build data with current structure"""
        try:
            # Deep merge with validation
            result = current.copy()
            
            for section in ['space', 'ground', 'captain']:
                if section in new:
                    if section not in result:
                        result[section] = {}
                    
                    for key, value in new[section].items():
                        if key in result[section]:
                            # For lists, merge item by item
                            if isinstance(result[section][key], list) and isinstance(value, list):
                                # Ensure the list has the right length
                                if len(value) <= len(result[section][key]):
                                    for i, item in enumerate(value):
                                        if i < len(result[section][key]):
                                            result[section][key][i] = item
                            else:
                                result[section][key] = value
                        else:
                            result[section][key] = value
            
            return result
        except (KeyError, TypeError):
            # If merge fails, return current structure
            return current
    
    def enable_autosave(self, enabled: bool = True) -> None:
        """Enable or disable autosave"""
        self._autosave_enabled = enabled
    
    def is_modified(self, since: Optional[datetime] = None) -> bool:
        """Check if build has been modified since given time"""
        if since is None:
            return self._last_modified > datetime.now()
        return self._last_modified > since 