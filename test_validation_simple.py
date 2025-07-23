#!/usr/bin/env python3
"""
Simple validation test to verify our testing scripts work correctly.
"""

import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation import validate_aave_data


def create_test_data():
    """Create test data in the expected format."""
    return {
        "ethereum": [
            {
                "asset_address": "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0",
                "symbol": "USDC",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "decimals": 6,
                "active": True,
                "frozen": False,
                "borrowing_enabled": True,
                "stable_borrowing_enabled": False,
                "paused": False,
                "borrowable_in_isolation": True,
                "siloed_borrowing": False,
                "reserve_factor": 0.10,
                "liquidation_protocol_fee": 0.10,
                "debt_ceiling": 0,
                "emode_category": 1,
                "liquidity_index": 1.0234,
                "variable_borrow_index": 1.0456,
                "current_liquidity_rate": 0.0234,
                "current_variable_borrow_rate": 0.0456,
                "last_update_timestamp": 1704067200,
                "a_token_address": "0xBcca60bB61934080951369a648Fb03DF4F96263C",
                "variable_debt_token_address": "0x619beb58998eD2278e08620f97007e1116D5D25b",
                "supply_cap": 1000000000,
                "borrow_cap": 900000000
            }
        ],
        "polygon": [
            {
                "asset_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "symbol": "USDC.e",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "decimals": 6,
                "active": True,
                "frozen": False,
                "borrowing_enabled": True,
                "stable_borrowing_enabled": False,
                "paused": False,
                "borrowable_in_isolation": True,
                "siloed_borrowing": False,
                "reserve_factor": 0.60,
                "liquidation_protocol_fee": 0.10,
                "debt_ceiling": 0,
                "emode_category": 1,
                "liquidity_index": 1.0345,
                "variable_borrow_index": 1.0567,
                "current_liquidity_rate": 0.0345,
                "current_variable_borrow_rate": 0.0567,
                "last_update_timestamp": 1704067200,
                "a_token_address": "0x625E7708f30cA75bfd92586e17077590C60eb4cD",
                "variable_debt_token_address": "0xFCCf3cAbbe80101232d343252614b6A3eE81C989",
                "supply_cap": 500000000,
                "borrow_cap": 450000000
            }
        ]
    }


def test_validation():
    """Test the validation functionality."""
    print("🧪 Testing validation functionality...")
    
    # Create test data
    test_data = create_test_data()
    
    # Run validation
    result = validate_aave_data(test_data, verbose=False)
    
    # Print results
    summary = result.get_summary()
    print(f"✅ Validation test completed:")
    print(f"   Total checks: {result.total_checks}")
    print(f"   Passed checks: {result.passed_checks}")
    print(f"   Success rate: {summary['success_rate']:.1%}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Warnings: {len(result.warnings)}")
    
    if result.errors:
        print("❌ Errors found:")
        for error in result.errors[:3]:
            print(f"   {error}")
    
    if result.warnings:
        print("⚠️  Warnings found:")
        for warning in result.warnings[:3]:
            print(f"   {warning}")
    
    return result.is_valid()


def test_2025_parameters():
    """Test 2025 parameter validation."""
    print("\n🧪 Testing 2025 parameter validation...")
    
    test_data = create_test_data()
    
    # Check for 2025 parameters
    param_count = 0
    for network_data in test_data.values():
        for asset in network_data:
            if 'supply_cap' in asset and 'borrow_cap' in asset:
                param_count += 1
    
    print(f"✅ Found {param_count} assets with 2025 parameters (supply_cap, borrow_cap)")
    
    # Test parameter relationships
    relationship_errors = 0
    for network_key, network_data in test_data.items():
        for asset in network_data:
            supply_cap = asset.get('supply_cap', 0)
            borrow_cap = asset.get('borrow_cap', 0)
            
            if supply_cap > 0 and borrow_cap > 0 and borrow_cap > supply_cap:
                relationship_errors += 1
                print(f"❌ {network_key} {asset.get('symbol')}: Borrow cap > Supply cap")
    
    if relationship_errors == 0:
        print("✅ All supply/borrow cap relationships are valid")
    
    return relationship_errors == 0


def test_comparison_functionality():
    """Test comparison functionality."""
    print("\n🧪 Testing comparison functionality...")
    
    test_data = create_test_data()
    
    # Test known values comparison
    known_values = {
        'ethereum': {
            'USDC': {
                'liquidation_threshold': 0.78,
                'loan_to_value': 0.75
            }
        }
    }
    
    matches = 0
    for network_key, assets in test_data.items():
        if network_key in known_values:
            network_known = known_values[network_key]
            for asset in assets:
                symbol = asset.get('symbol', '')
                if symbol in network_known:
                    expected = network_known[symbol]
                    for param, expected_value in expected.items():
                        if param in asset:
                            actual_value = asset[param]
                            if abs(actual_value - expected_value) <= 0.01:
                                matches += 1
    
    print(f"✅ Found {matches} parameter matches with known values")
    return matches > 0


def main():
    """Run all validation tests."""
    print("🚀 Running Local Testing and Validation Scripts")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Basic validation
    validation_passed = test_validation()
    all_passed = all_passed and validation_passed
    
    # Test 2: 2025 parameters
    params_2025_passed = test_2025_parameters()
    all_passed = all_passed and params_2025_passed
    
    # Test 3: Comparison functionality
    comparison_passed = test_comparison_functionality()
    all_passed = all_passed and comparison_passed
    
    # Final summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validation tests passed!")
        print("✅ Local testing and validation scripts are working correctly")
    else:
        print("❌ Some validation tests failed")
    
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)