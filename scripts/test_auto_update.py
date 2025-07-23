#!/usr/bin/env python3
"""
Test script for network auto-update functionality.
This script demonstrates the auto-update features and validates the implementation.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from networks import (
    get_networks_with_fallback,
    periodic_network_discovery,
    discover_new_networks,
    update_networks_from_address_book,
    save_discovered_networks,
    load_cached_networks,
    validate_all_networks,
    get_network_summary,
    AAVE_V3_NETWORKS
)


def test_static_configuration():
    """Test the static network configuration."""
    print("=" * 60)
    print("TESTING STATIC NETWORK CONFIGURATION")
    print("=" * 60)
    
    # Validate static networks
    is_valid, errors = validate_all_networks()
    print(f"Static configuration valid: {is_valid}")
    
    if errors:
        print("Validation errors:")
        for network, network_errors in errors.items():
            print(f"  {network}: {network_errors}")
    
    # Get network summary
    summary = get_network_summary()
    print(f"Network summary: {summary}")
    
    return is_valid


def test_address_book_integration():
    """Test integration with aave-address-book."""
    print("\n" + "=" * 60)
    print("TESTING AAVE-ADDRESS-BOOK INTEGRATION")
    print("=" * 60)
    
    try:
        # Test network update from address book
        print("Testing network update from address book...")
        updated_networks, errors = update_networks_from_address_book()
        
        print(f"Updated networks count: {len(updated_networks)}")
        print(f"Errors during update: {len(errors)}")
        
        if errors:
            print("Update errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        # Count networks by source
        sources = {}
        for network_key, config in updated_networks.items():
            source = config.get('source', 'static')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"Networks by source: {sources}")
        
        return len(updated_networks) > 0
        
    except Exception as e:
        print(f"Error testing address book integration: {e}")
        return False


def test_fallback_mechanism():
    """Test the fallback mechanism."""
    print("\n" + "=" * 60)
    print("TESTING FALLBACK MECHANISM")
    print("=" * 60)
    
    try:
        # Test get_networks_with_fallback
        print("Testing networks with fallback...")
        networks = get_networks_with_fallback()
        
        print(f"Networks retrieved: {len(networks)}")
        
        # Verify we have essential networks
        essential_networks = ['ethereum', 'polygon', 'arbitrum', 'optimism']
        missing_networks = []
        
        for network in essential_networks:
            if network not in networks:
                missing_networks.append(network)
        
        if missing_networks:
            print(f"Missing essential networks: {missing_networks}")
            return False
        else:
            print("All essential networks present")
            return True
            
    except Exception as e:
        print(f"Error testing fallback mechanism: {e}")
        return False


def test_periodic_discovery():
    """Test periodic network discovery."""
    print("\n" + "=" * 60)
    print("TESTING PERIODIC NETWORK DISCOVERY")
    print("=" * 60)
    
    try:
        # Test periodic discovery
        print("Testing periodic network discovery...")
        networks, success = periodic_network_discovery()
        
        print(f"Discovery successful: {success}")
        print(f"Networks discovered: {len(networks)}")
        
        # Check for new networks
        static_keys = set(AAVE_V3_NETWORKS.keys())
        discovered_keys = set(networks.keys())
        new_networks = discovered_keys - static_keys
        
        if new_networks:
            print(f"New networks discovered: {list(new_networks)}")
        else:
            print("No new networks discovered")
        
        return success
        
    except Exception as e:
        print(f"Error testing periodic discovery: {e}")
        return False


def test_network_discovery():
    """Test network discovery functionality."""
    print("\n" + "=" * 60)
    print("TESTING NETWORK DISCOVERY")
    print("=" * 60)
    
    try:
        # Test discover_new_networks
        print("Testing new network discovery...")
        new_networks = discover_new_networks()
        
        print(f"New networks found: {len(new_networks)}")
        if new_networks:
            print(f"New network names: {new_networks}")
        
        return True
        
    except Exception as e:
        print(f"Error testing network discovery: {e}")
        return False


def test_caching_functionality():
    """Test network caching functionality."""
    print("\n" + "=" * 60)
    print("TESTING CACHING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test saving and loading cached networks
        test_networks = {
            'test_network': {
                'name': 'Test Network',
                'chain_id': 999,
                'rpc': 'https://test.rpc.com',
                'pool': '0x1234567890123456789012345678901234567890',
                'pool_data_provider': '0x0987654321098765432109876543210987654321',
                'active': True,
                'source': 'test'
            }
        }
        
        cache_file = 'test_cache.json'
        
        # Test saving
        print("Testing cache save...")
        save_success = save_discovered_networks(test_networks, cache_file)
        print(f"Cache save successful: {save_success}")
        
        # Test loading
        print("Testing cache load...")
        loaded_networks = load_cached_networks(cache_file, max_age_hours=1)
        
        if loaded_networks:
            print(f"Cache load successful: {len(loaded_networks)} networks loaded")
            print(f"Test network present: {'test_network' in loaded_networks}")
        else:
            print("Cache load failed or expired")
        
        # Cleanup
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        return save_success and loaded_networks is not None
        
    except Exception as e:
        print(f"Error testing caching functionality: {e}")
        return False


def main():
    """Run all tests."""
    print("AAVE V3 NETWORK AUTO-UPDATE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Static Configuration", test_static_configuration),
        ("Address Book Integration", test_address_book_integration),
        ("Fallback Mechanism", test_fallback_mechanism),
        ("Periodic Discovery", test_periodic_discovery),
        ("Network Discovery", test_network_discovery),
        ("Caching Functionality", test_caching_functionality),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Auto-update functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())