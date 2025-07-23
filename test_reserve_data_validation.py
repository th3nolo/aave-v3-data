#!/usr/bin/env python3
"""
Validation script to test reserve data extraction with real network data.
This script demonstrates the get_reserve_data function working with actual blockchain data.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import get_reserve_data, get_reserves, get_asset_symbol


def test_polygon_usdc_reserve_data():
    """Test reserve data extraction for USDC on Polygon network."""
    print("Testing USDC reserve data extraction on Polygon...")
    
    # Polygon network configuration
    polygon_rpc = "https://polygon-rpc.com"
    polygon_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
    
    try:
        # Test getting reserve data
        reserve_data = get_reserve_data(usdc_address, polygon_pool, polygon_rpc)
        
        print(f"✓ Successfully retrieved reserve data for USDC")
        print(f"  - LTV: {reserve_data['loan_to_value']:.2%}")
        print(f"  - Liquidation Threshold: {reserve_data['liquidation_threshold']:.2%}")
        print(f"  - Liquidation Bonus: {reserve_data['liquidation_bonus']:.2%}")
        print(f"  - Decimals: {reserve_data['decimals']}")
        print(f"  - Active: {reserve_data['active']}")
        print(f"  - Borrowing Enabled: {reserve_data['borrowing_enabled']}")
        print(f"  - Reserve Factor: {reserve_data['reserve_factor']:.2%}")
        print(f"  - aToken Address: {reserve_data['a_token_address']}")
        
        # Validate expected ranges for USDC
        assert 0.70 <= reserve_data['loan_to_value'] <= 0.85, f"LTV out of expected range: {reserve_data['loan_to_value']}"
        assert 0.75 <= reserve_data['liquidation_threshold'] <= 0.85, f"LT out of expected range: {reserve_data['liquidation_threshold']}"
        assert reserve_data['decimals'] == 6, f"USDC should have 6 decimals, got {reserve_data['decimals']}"
        assert reserve_data['active'], "USDC should be active"
        
        print("✓ All validation checks passed for USDC")
        
        # Test getting asset symbol
        symbol = get_asset_symbol(usdc_address, polygon_rpc)
        print(f"✓ Asset symbol: {symbol}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing USDC reserve data: {e}")
        return False


def test_reserves_list():
    """Test getting the list of reserves from Polygon."""
    print("\nTesting reserves list retrieval...")
    
    # Polygon network configuration
    polygon_rpc = "https://polygon-rpc.com"
    polygon_pool = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    
    try:
        reserves = get_reserves(polygon_pool, polygon_rpc)
        
        print(f"✓ Successfully retrieved {len(reserves)} reserves")
        print(f"  - First few reserves: {reserves[:3]}")
        
        # Validate we got a reasonable number of reserves
        assert len(reserves) >= 10, f"Expected at least 10 reserves, got {len(reserves)}"
        
        # Validate addresses are properly formatted
        for reserve in reserves[:5]:  # Check first 5
            assert reserve.startswith('0x'), f"Invalid address format: {reserve}"
            assert len(reserve) == 42, f"Invalid address length: {reserve}"
        
        print("✓ Reserves list validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing reserves list: {e}")
        return False


def main():
    """Run validation tests."""
    print("=== Aave V3 Reserve Data Validation ===\n")
    
    success_count = 0
    total_tests = 2
    
    # Test individual reserve data
    if test_polygon_usdc_reserve_data():
        success_count += 1
    
    # Test reserves list
    if test_reserves_list():
        success_count += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {success_count}/{total_tests} tests")
    
    if success_count == total_tests:
        print("✓ All validation tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())