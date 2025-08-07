"""
Data Loader - Handles all data loading operations.

This module refactors the data loading logic from the original codebase,
providing a clean interface for loading data from various sources with better separation of concerns.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.exceptions import ConnectionError, Timeout

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Represents the result of a data loading operation."""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    load_time: Optional[float] = None


class DataLoader:
    """
    Handles loading of all application data including ships, equipment, traits, and images.
    
    This class refactors the data loading logic from the original codebase,
    providing a cleaner interface with better error handling and separation of concerns.
    """
    
    def __init__(self, cache_manager, config):
        self.cache_manager = cache_manager
        self.config = config
        self.api_data_loader = None
        self._setup_api_loader()
    
    def _setup_api_loader(self):
        """Setup the API data loader."""
        try:
            from ..api_data_loader import create_api_data_loader
            self.api_data_loader = create_api_data_loader(self.config['config_subfolders']['cache'])
        except ImportError as e:
            logger.warning(f"Could not import API data loader: {e}")
            self.api_data_loader = None
    
    def load_all_data(self, threaded_worker=None) -> LoadResult:
        """
        Load all application data.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            LoadResult with success status and loaded data
        """
        start_time = datetime.now()
        
        try:
            logger.info("Starting data load process...")
            
            # Try to load via API first
            if self.api_data_loader:
                result = self._load_data_via_api(threaded_worker)
                if result.success:
                    return result
            
            # Fallback to legacy loading method
            logger.info("API loading failed, falling back to legacy method...")
            return self._load_data_legacy(threaded_worker)
            
        except Exception as e:
            error_msg = f"Error loading data: {e}"
            logger.error(error_msg)
            return LoadResult(
                success=False,
                data={},
                error_message=error_msg,
                load_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _load_data_via_api(self, threaded_worker=None) -> LoadResult:
        """
        Load data using the MediaWiki API.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            LoadResult with API data
        """
        try:
            from ..api_data_loader import load_all_data_via_api
            
            if threaded_worker:
                threaded_worker.update_splash.emit('Loading: Data via API')
            
            api_data = load_all_data_via_api(threaded_worker, self.config['config_subfolders']['cache'])
            
            # Store data in cache
            self._store_api_data(api_data)
            
            logger.info("Successfully loaded all data via API")
            return LoadResult(
                success=True,
                data=api_data,
                load_time=0.0  # API loader handles timing
            )
            
        except Exception as e:
            error_msg = f"Error loading data via API: {e}"
            logger.error(error_msg)
            return LoadResult(
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _load_data_legacy(self, threaded_worker=None) -> LoadResult:
        """
        Load data using legacy methods (web scraping).
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            LoadResult with legacy data
        """
        try:
            # This would implement the legacy loading logic
            # For now, return empty result
            logger.warning("Legacy data loading not implemented")
            return LoadResult(
                success=False,
                data={},
                error_message="Legacy data loading not implemented"
            )
            
        except Exception as e:
            error_msg = f"Error loading data via legacy method: {e}"
            logger.error(error_msg)
            return LoadResult(
                success=False,
                data={},
                error_message=error_msg
            )
    
    def _store_api_data(self, api_data: Dict[str, Any]) -> None:
        """
        Store API data in cache and save to files.
        
        Args:
            api_data: Data loaded from API
        """
        try:
            # Store in cache
            self.cache_manager.ships = api_data.get('ships', {})
            self.cache_manager.equipment = api_data.get('equipment', {})
            self.cache_manager.traits = api_data.get('traits', {})
            self.cache_manager.starship_traits = api_data.get('starship_traits', {})
            self.cache_manager.images_set = api_data.get('images_set', set())
            self.cache_manager.modifiers = api_data.get('modifiers', {})
            
            # Store duty officer data
            doff_data = api_data.get('doffs', {})
            self.cache_manager.space_doffs = doff_data.get('space', {})
            self.cache_manager.ground_doffs = doff_data.get('ground', {})
            
            # Save to cache files
            self._save_cache_files(api_data)
            
            logger.info("Successfully stored API data in cache")
            
        except Exception as e:
            logger.error(f"Error storing API data: {e}")
            raise
    
    def _save_cache_files(self, api_data: Dict[str, Any]) -> None:
        """
        Save data to cache files.
        
        Args:
            api_data: Data to save
        """
        try:
            from ..iofunc import store_to_cache
            
            # Save main data files
            store_to_cache(self, api_data.get('ships', {}), 'ships.json')
            store_to_cache(self, api_data.get('equipment', {}), 'equipment.json')
            store_to_cache(self, api_data.get('traits', {}), 'traits.json')
            store_to_cache(self, api_data.get('starship_traits', {}), 'starship_traits.json')
            store_to_cache(self, api_data.get('modifiers', {}), 'modifiers.json')
            
            logger.info("Successfully saved cache files")
            
        except Exception as e:
            logger.error(f"Error saving cache files: {e}")
            raise
    
    def load_images(self, threaded_worker=None) -> LoadResult:
        """
        Load application images.
        
        Args:
            threaded_worker: Optional worker for progress updates
            
        Returns:
            LoadResult with image loading status
        """
        start_time = datetime.now()
        
        try:
            logger.info("Starting image loading process...")
            
            # Get list of images to download
            images_to_download = self._get_images_to_download()
            
            if not images_to_download:
                logger.info("No images to download")
                return LoadResult(
                    success=True,
                    data={'downloaded_count': 0},
                    load_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Download images in parallel
            downloaded_count = self._download_images_parallel(images_to_download, threaded_worker)
            
            logger.info(f"Successfully downloaded {downloaded_count} images")
            return LoadResult(
                success=True,
                data={'downloaded_count': downloaded_count},
                load_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            error_msg = f"Error loading images: {e}"
            logger.error(error_msg)
            return LoadResult(
                success=False,
                data={},
                error_message=error_msg,
                load_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _get_images_to_download(self) -> List[Tuple[str, str]]:
        """
        Get list of images that need to be downloaded.
        
        Returns:
            List of (image_name, url) tuples
        """
        try:
            # Get already downloaded images
            downloaded_images = self._get_downloaded_images()
            
            # Get images that need to be downloaded
            images_to_download = []
            
            for image_name in self.cache_manager.images_set:
                if image_name not in downloaded_images:
                    # Determine URL for image
                    url = self._get_image_url(image_name)
                    images_to_download.append((image_name, url))
            
            logger.info(f"Found {len(images_to_download)} images to download")
            return images_to_download
            
        except Exception as e:
            logger.error(f"Error getting images to download: {e}")
            return []
    
    def _get_downloaded_images(self) -> set:
        """Get set of already downloaded images."""
        try:
            img_folder = self.config['config_subfolders']['images']
            downloaded = set()
            
            if os.path.exists(img_folder):
                for filename in os.listdir(img_folder):
                    if filename.endswith('.png'):
                        downloaded.add(filename.replace('.png', ''))
            
            return downloaded
            
        except Exception as e:
            logger.error(f"Error getting downloaded images: {e}")
            return set()
    
    def _get_image_url(self, image_name: str) -> str:
        """
        Get URL for an image.
        
        Args:
            image_name: Name of the image
            
        Returns:
            URL for the image
        """
        # This is a simplified version - the original code has more complex URL logic
        base_url = "https://stowiki.net/w/images/"
        return f"{base_url}{image_name.replace(' ', '_')}.png"
    
    def _download_images_parallel(self, images_to_download: List[Tuple[str, str]], 
                                 threaded_worker=None) -> int:
        """
        Download images in parallel.
        
        Args:
            images_to_download: List of (image_name, url) tuples
            threaded_worker: Optional worker for progress updates
            
        Returns:
            Number of successfully downloaded images
        """
        downloaded_count = 0
        img_folder = self.config['config_subfolders']['images']
        
        # Ensure images directory exists
        os.makedirs(img_folder, exist_ok=True)
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._download_single_image, image_name, url, img_folder): 
                (image_name, url) for image_name, url in images_to_download
            }
            
            completed = 0
            for future in as_completed(futures):
                image_name, url = futures[future]
                completed += 1
                
                try:
                    success = future.result()
                    if success:
                        downloaded_count += 1
                    
                    # Update progress
                    if threaded_worker and completed % 5 == 0:
                        threaded_worker.update_splash.emit(
                            f'Downloading: Images ({completed}/{len(images_to_download)})'
                        )
                        
                except Exception as e:
                    logger.error(f"Error downloading {image_name}: {e}")
        
        return downloaded_count
    
    def _download_single_image(self, image_name: str, url: str, img_folder: str) -> bool:
        """
        Download a single image.
        
        Args:
            image_name: Name of the image
            url: URL to download from
            img_folder: Folder to save to
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(img_folder, f"{image_name}.png")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {image_name}: {e}")
            return False
    
    def validate_data_integrity(self) -> Dict[str, bool]:
        """
        Validate the integrity of loaded data.
        
        Returns:
            Dictionary with validation results for each data type
        """
        results = {}
        
        try:
            # Validate ships data
            results['ships'] = len(self.cache_manager.ships) > 0
            
            # Validate equipment data
            results['equipment'] = len(self.cache_manager.equipment) > 0
            
            # Validate traits data
            results['traits'] = len(self.cache_manager.traits) > 0
            
            # Validate starship traits data
            results['starship_traits'] = len(self.cache_manager.starship_traits) > 0
            
            # Validate images data
            results['images'] = len(self.cache_manager.images_set) > 0
            
            logger.info(f"Data integrity validation results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error validating data integrity: {e}")
            return {key: False for key in ['ships', 'equipment', 'traits', 'starship_traits', 'images']}
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of loaded data.
        
        Returns:
            Dictionary with data summary
        """
        try:
            return {
                'ships_count': len(self.cache_manager.ships),
                'equipment_categories': len(self.cache_manager.equipment),
                'total_equipment_items': sum(len(items) for items in self.cache_manager.equipment.values()),
                'traits_count': len(self.cache_manager.traits),
                'starship_traits_count': len(self.cache_manager.starship_traits),
                'images_count': len(self.cache_manager.images_set),
                'modifiers_count': sum(len(mods) for mods in self.cache_manager.modifiers.values())
            }
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
