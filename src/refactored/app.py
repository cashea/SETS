"""
Refactored SETS Application - Main application class.

This module provides a refactored version of the main SETS application,
integrating all the refactored modules with better separation of concerns.
"""

import logging
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QObject, pyqtSignal

from .cache_manager import CacheManager
from .data_loader import DataLoader
from .equipment_manager import EquipmentManager
from .stat_calculator import StatCalculator
from .build_manager import BuildManager

logger = logging.getLogger(__name__)


class LoadingWorker(QObject):
    """Worker class for handling data loading in background thread."""
    
    progress_updated = pyqtSignal(str)
    loading_finished = pyqtSignal(bool, str)
    
    def __init__(self, data_loader, cache_manager):
        super().__init__()
        self.data_loader = data_loader
        self.cache_manager = cache_manager
    
    def load_data(self):
        """Load all application data."""
        try:
            # Load main data
            result = self.data_loader.load_all_data(self)
            if not result.success:
                self.loading_finished.emit(False, result.error_message or "Unknown error")
                return
            
            # Load images
            image_result = self.data_loader.load_images(self)
            if not image_result.success:
                logger.warning(f"Image loading failed: {image_result.error_message}")
            
            self.loading_finished.emit(True, "Data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error in loading worker: {e}")
            self.loading_finished.emit(False, str(e))


@dataclass
class AppConfig:
    """Application configuration."""
    config_subfolders: Dict[str, str]
    ui_scale: int = 1
    theme: str = "default"
    autosave_enabled: bool = True
    debug_mode: bool = False


class RefactoredSETSApp:
    """
    Refactored SETS Application - Main application class.
    
    This class integrates all the refactored modules and provides
    a clean interface for the SETS application functionality.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.app = None
        self.main_window = None
        
        # Initialize managers
        self.cache_manager = CacheManager(config.__dict__)
        self.data_loader = DataLoader(self.cache_manager, config.__dict__)
        self.equipment_manager = EquipmentManager(self.cache_manager)
        self.stat_calculator = StatCalculator(self.equipment_manager, self.cache_manager)
        self.build_manager = BuildManager()
        
        # Loading state
        self.is_loading = False
        self.loading_worker = None
        self.loading_thread = None
        
        logger.info("Refactored SETS Application initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing SETS application...")
            
            # Create Qt application
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("SETS")
            self.app.setApplicationVersion("2.0.0")
            
            # Load cache from files
            if not self.cache_manager.load_cache_from_files():
                logger.warning("Failed to load cache from files")
            
            # Validate cache integrity
            integrity_results = self.cache_manager.validate_cache_integrity()
            if not all(integrity_results.values()):
                logger.warning("Cache integrity issues detected")
            
            # Initialize equipment manager with cache data
            if self.cache_manager.equipment:
                self.equipment_manager.load_equipment_data({
                    'equipment': self.cache_manager.equipment
                })
            
            logger.info("SETS application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing SETS application: {e}")
            return False
    
    def load_data_async(self, progress_callback=None, completion_callback=None):
        """
        Load application data asynchronously.
        
        Args:
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback for completion
        """
        if self.is_loading:
            logger.warning("Data loading already in progress")
            return
        
        try:
            self.is_loading = True
            
            # Create worker and thread
            self.loading_worker = LoadingWorker(self.data_loader, self.cache_manager)
            self.loading_thread = QThread()
            
            # Move worker to thread
            self.loading_worker.moveToThread(self.loading_thread)
            
            # Connect signals
            self.loading_thread.started.connect(self.loading_worker.load_data)
            self.loading_worker.loading_finished.connect(self._on_loading_finished)
            
            if progress_callback:
                self.loading_worker.progress_updated.connect(progress_callback)
            
            if completion_callback:
                self._completion_callback = completion_callback
            
            # Start loading
            self.loading_thread.start()
            
            logger.info("Started async data loading")
            
        except Exception as e:
            logger.error(f"Error starting async data loading: {e}")
            self.is_loading = False
    
    def _on_loading_finished(self, success: bool, message: str):
        """Handle loading completion."""
        try:
            self.is_loading = False
            
            # Clean up thread
            if self.loading_thread:
                self.loading_thread.quit()
                self.loading_thread.wait()
                self.loading_thread = None
            
            self.loading_worker = None
            
            if success:
                logger.info("Data loading completed successfully")
                # Update equipment manager with new data
                if self.cache_manager.equipment:
                    self.equipment_manager.load_equipment_data({
                        'equipment': self.cache_manager.equipment
                    })
            else:
                logger.error(f"Data loading failed: {message}")
            
            # Call completion callback if provided
            if hasattr(self, '_completion_callback'):
                self._completion_callback(success, message)
                delattr(self, '_completion_callback')
            
        except Exception as e:
            logger.error(f"Error handling loading completion: {e}")
    
    def calculate_ship_stats(self, ship_name: str, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate ship statistics.
        
        Args:
            ship_name: Name of the selected ship
            build_data: Current build data
            
        Returns:
            Dictionary with calculated ship statistics
        """
        try:
            ship_stats = self.stat_calculator.calculate_ship_stats(ship_name, build_data)
            
            # Format results for display
            result = {
                'base_stats': {},
                'equipment_bonuses': {},
                'trait_bonuses': {},
                'skill_bonuses': {},
                'total_bonuses': {},
                'final_stats': {}
            }
            
            # Format base stats
            for stat_name, value in ship_stats.base_stats.items():
                result['base_stats'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            # Format bonuses
            for stat_name, value in ship_stats.equipment_bonuses.items():
                result['equipment_bonuses'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            for stat_name, value in ship_stats.trait_bonuses.items():
                result['trait_bonuses'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            for stat_name, value in ship_stats.skill_bonuses.items():
                result['skill_bonuses'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            # Format total bonuses
            for stat_name, value in ship_stats.total_bonuses.items():
                result['total_bonuses'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            # Format final stats
            for stat_name, value in ship_stats.final_stats.items():
                result['final_stats'][stat_name] = self.stat_calculator.format_stat_value(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ship stats: {e}")
            return {}
    
    def get_equipment_item(self, item_name: str, category: str = None):
        """
        Get equipment item by name.
        
        Args:
            item_name: Name of the equipment item
            category: Optional category to search in
            
        Returns:
            EquipmentItem if found, None otherwise
        """
        return self.equipment_manager.get_equipment_item(item_name, category)
    
    def get_ship_data(self, ship_name: str):
        """
        Get ship data by name.
        
        Args:
            ship_name: Name of the ship
            
        Returns:
            Ship data if found, None otherwise
        """
        return self.cache_manager.get_ship_data(ship_name)
    
    def get_cache_stats(self):
        """Get cache statistics."""
        return self.cache_manager.get_cache_stats()
    
    def validate_data_integrity(self):
        """Validate data integrity."""
        return self.data_loader.validate_data_integrity()
    
    def get_data_summary(self):
        """Get data summary."""
        return self.data_loader.get_data_summary()
    
    def save_cache(self) -> bool:
        """Save cache to files."""
        return self.cache_manager.save_cache_to_files()
    
    def clear_failed_images(self, older_than_days: int = 7) -> int:
        """Clear old failed images."""
        return self.cache_manager.clear_failed_images(older_than_days)
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Application exit code
        """
        try:
            if not self.app:
                logger.error("Application not initialized")
                return 1
            
            # Show main window (this would be implemented in a separate UI module)
            # For now, just run the event loop
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"Error running application: {e}")
            return 1
    
    def cleanup(self):
        """Clean up application resources."""
        try:
            # Save cache
            self.save_cache()
            
            # Clean up loading thread if active
            if self.loading_thread and self.loading_thread.isRunning():
                self.loading_thread.quit()
                self.loading_thread.wait()
            
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_app(config_dict: Dict[str, Any]) -> RefactoredSETSApp:
    """
    Create a refactored SETS application instance.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        RefactoredSETSApp instance
    """
    config = AppConfig(
        config_subfolders=config_dict.get('config_subfolders', {}),
        ui_scale=config_dict.get('ui_scale', 1),
        theme=config_dict.get('theme', 'default'),
        autosave_enabled=config_dict.get('autosave_enabled', True),
        debug_mode=config_dict.get('debug_mode', False)
    )
    
    return RefactoredSETSApp(config)
