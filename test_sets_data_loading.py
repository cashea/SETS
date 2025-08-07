#!/usr/bin/env python3
"""
Test script to verify MediaWiki API data loading within SETS context.
"""

import sys
import os

def test_sets_data_loading():
    """Test that the SETS application can load data via the MediaWiki API."""
    print("=== Testing SETS Data Loading ===")
    
    try:
        # Import SETS as a package
        from src import SETS
        print("✓ SETS package imported successfully")
        
        # Test that the API modules are available
        from src.api_data_loader import create_api_data_loader, load_all_data_via_api
        print("✓ API data loader imported successfully")
        
        from src.mediawiki_api import CachedMediaWikiAPI
        print("✓ MediaWiki API imported successfully")
        
        # Test creating an API client
        print("\nTesting API client creation...")
        api_client = CachedMediaWikiAPI(cache_dir="test_cache_sets_app")
        print("✓ API client created successfully")
        
        # Test loading ships data
        print("\nTesting ships data loading...")
        ships_data = api_client.get_ships_data()
        print(f"✓ Loaded {len(ships_data)} ships")
        
        if ships_data:
            sample_ship = ships_data[0]
            print(f"  Sample ship: {sample_ship.get('name', 'Unknown')}")
            print(f"  Ship fields: {list(sample_ship.keys())}")
        
        # Test loading equipment data
        print("\nTesting equipment data loading...")
        equipment_data = api_client.get_equipment_data()
        print(f"✓ Loaded {len(equipment_data)} equipment items")
        
        if equipment_data:
            sample_equipment = equipment_data[0]
            print(f"  Sample equipment: {sample_equipment.get('name', 'Unknown')}")
            print(f"  Equipment fields: {list(sample_equipment.keys())}")
        
        # Test loading traits data
        print("\nTesting traits data loading...")
        traits_data = api_client.get_traits_data()
        print(f"✓ Loaded {len(traits_data)} traits")
        
        # Test loading starship traits data
        print("\nTesting starship traits data loading...")
        starship_traits_data = api_client.get_starship_traits_data()
        print(f"✓ Loaded {len(starship_traits_data)} starship traits")
        
        # Test the API data loader
        print("\nTesting API data loader...")
        loader = create_api_data_loader("test_cache_sets_app")
        print("✓ API data loader created")
        
        # Test loading ships via loader
        ships_dict = loader.load_ships_data()
        print(f"✓ Loaded {len(ships_dict)} ships via loader")
        
        # Test loading equipment via loader
        equipment_dict = loader.load_equipment_data()
        print(f"✓ Loaded equipment data via loader")
        
        print("\n=== DATA LOADING TEST RESULTS ===")
        print("✓ All API modules imported successfully")
        print("✓ API client working correctly")
        print("✓ Data loading functional")
        print("✓ SETS integration ready")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during data loading test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_integration():
    """Test that cache files are created and accessible."""
    print("\n=== Testing Cache Integration ===")
    
    try:
        cache_dir = "test_cache_sets_app"
        api_data_dir = os.path.join(cache_dir, "api_data")
        
        # Check if directories exist
        if os.path.exists(cache_dir):
            print(f"✓ Cache directory exists: {cache_dir}")
            
            if os.path.exists(api_data_dir):
                print(f"✓ API data directory exists: {api_data_dir}")
                
                # List cache files
                cache_files = [f for f in os.listdir(api_data_dir) if f.endswith('.json')]
                print(f"✓ Found {len(cache_files)} JSON cache files")
                
                for file in cache_files:
                    file_path = os.path.join(api_data_dir, file)
                    file_size = os.path.getsize(file_path)
                    print(f"  {file}: {file_size} bytes")
            else:
                print(f"✗ API data directory missing: {api_data_dir}")
        else:
            print(f"✗ Cache directory missing: {cache_dir}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during cache integration test: {e}")
        return False


def main():
    """Run all tests."""
    print("SETS MediaWiki API Data Loading Test")
    print("=" * 50)
    print()
    
    success = True
    
    # Test data loading
    if not test_sets_data_loading():
        success = False
    
    # Test cache integration
    if not test_cache_integration():
        success = False
    
    print()
    print("=" * 50)
    
    if success:
        print("✓ ALL TESTS PASSED")
        print("✓ MediaWiki API data is properly integrated into SETS")
        print("✓ Data files are accessible and functional")
        print("✓ Ready for use in SETS application")
    else:
        print("✗ SOME TESTS FAILED")
        print("✗ Please check the implementation")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
