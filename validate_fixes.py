#!/usr/bin/env python3
"""
Quick Validation Script
Validates basic functionality and known protocol values quickly.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation import validate_aave_data
from networks import get_active_networks, validate_all_networks


def quick_network_check() -> bool:
    """Quick check of network configuration."""
    print("🔍 Checking network configuration...")
    
    is_valid, errors = validate_all_networks()
    if not is_valid:
        print("❌ Network configuration errors:")
        for network, network_errors in errors.items():
            for error in network_errors:
                print(f"   {network}: {error}")
        return False
    
    networks = get_active_networks()
    print(f"✅ {len(networks)} networks configured")
    
    # Check for major networks
    major_networks = ['ethereum', 'polygon', 'arbitrum', 'optimism', 'base']
    missing = [net for net in major_networks if net not in networks]
    
    if missing:
        print(f"⚠️  Missing major networks: {missing}")
    else:
        print("✅ All major networks present")
    
    return True


def quick_data_validation(data: Dict[str, List[Dict]]) -> bool:
    """Quick validation of data structure and key values."""
    print("🔍 Running quick data validation...")
    
    if not data:
        print("❌ No data provided")
        return False
    
    print(f"📊 Data for {len(data)} networks")
    total_assets = sum(len(assets) for assets in data.values())
    print(f"📈 Total assets: {total_assets}")
    
    # Run comprehensive validation
    result = validate_aave_data(data, verbose=False)
    
    print(f"✅ Validation checks: {result.passed_checks}/{result.total_checks}")
    print(f"📈 Success rate: {result.passed_checks/max(result.total_checks, 1)*100:.1f}%")
    
    if result.errors:
        print(f"❌ Errors: {len(result.errors)}")
        for error in result.errors[:3]:  # Show first 3
            print(f"   {error}")
        if len(result.errors) > 3:
            print(f"   ... and {len(result.errors) - 3} more errors")
    
    if result.warnings:
        print(f"⚠️  Warnings: {len(result.warnings)}")
        for warning in result.warnings[:3]:  # Show first 3
            print(f"   {warning}")
        if len(result.warnings) > 3:
            print(f"   ... and {len(result.warnings) - 3} more warnings")
    
    # Check specific known values
    known_checks = [
        ('ethereum', 'USDC', 'liquidation_threshold', 0.78, 0.05),
        ('ethereum', 'WETH', 'liquidation_threshold', 0.825, 0.05),
        ('polygon', 'USDC', 'loan_to_value', 0.00, 0.01),  # Should be 0
    ]
    
    print("🔍 Checking known protocol values...")
    known_value_errors = 0
    
    for network_key, symbol, param, expected, tolerance in known_checks:
        if network_key not in data:
            continue
        
        found = False
        for asset in data[network_key]:
            if asset.get('symbol') == symbol:
                actual = asset.get(param, 0)
                if abs(actual - expected) > tolerance:
                    print(f"❌ {network_key} {symbol} {param}: expected {expected}, got {actual}")
                    known_value_errors += 1
                else:
                    print(f"✅ {network_key} {symbol} {param}: {actual} (expected {expected})")
                found = True
                break
        
        if not found:
            print(f"⚠️  {network_key} {symbol} not found")
    
    # Overall assessment
    is_valid = (
        len(result.errors) == 0 and
        known_value_errors == 0 and
        result.passed_checks > 0
    )
    
    if is_valid:
        print("✅ Quick validation passed")
    else:
        print("❌ Quick validation failed")
    
    return is_valid


def check_2025_features(data: Dict[str, List[Dict]]) -> bool:
    """Check for 2025 feature implementation."""
    print("🔍 Checking 2025 features...")
    
    # Check for supply/borrow caps
    caps_found = 0
    total_assets = 0
    
    for network_key, assets in data.items():
        for asset in assets:
            total_assets += 1
            if 'supply_cap' in asset and 'borrow_cap' in asset:
                caps_found += 1
    
    caps_percentage = caps_found / max(total_assets, 1) * 100
    print(f"📊 Supply/borrow caps: {caps_found}/{total_assets} assets ({caps_percentage:.1f}%)")
    
    if caps_percentage < 50:  # Should have caps on most assets
        print("⚠️  Low supply/borrow cap coverage")
    else:
        print("✅ Good supply/borrow cap coverage")
    
    # Check for WBTC parameter updates
    wbtc_updates_found = 0
    wbtc_total = 0
    
    for network_key, assets in data.items():
        for asset in assets:
            if asset.get('symbol') == 'WBTC':
                wbtc_total += 1
                lt = asset.get('liquidation_threshold', 0)
                # Check if LT is around new value (0.78) rather than old (0.70)
                if 0.75 <= lt <= 0.80:  # Range around new value
                    wbtc_updates_found += 1
    
    if wbtc_total > 0:
        print(f"📊 WBTC updates: {wbtc_updates_found}/{wbtc_total} networks")
        if wbtc_updates_found == wbtc_total:
            print("✅ WBTC parameters updated across all networks")
        else:
            print("⚠️  WBTC parameters not fully updated")
    
    return caps_percentage >= 50


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Quick Aave V3 Validation')
    parser.add_argument('--data-file', default='aave_v3_data.json', help='JSON data file')
    parser.add_argument('--network-only', action='store_true', help='Check networks only')
    
    args = parser.parse_args()
    
    print("🔍 Aave V3 Quick Validation")
    print("=" * 30)
    
    # Always check network configuration
    network_ok = quick_network_check()
    
    if args.network_only:
        return 0 if network_ok else 1
    
    # Load and validate data
    try:
        with open(args.data_file, 'r') as f:
            data = json.load(f)
        print(f"📂 Loaded data from {args.data_file}")
    except FileNotFoundError:
        print(f"❌ Data file not found: {args.data_file}")
        print("   Run 'python aave_fetcher.py' to fetch data first")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return 1
    
    # Run validations
    data_ok = quick_data_validation(data)
    features_ok = check_2025_features(data)
    
    # Summary
    print("\n" + "=" * 30)
    print("QUICK VALIDATION SUMMARY")
    print("=" * 30)
    print(f"🌐 Networks: {'✅' if network_ok else '❌'}")
    print(f"📊 Data: {'✅' if data_ok else '❌'}")
    print(f"🆕 2025 Features: {'✅' if features_ok else '⚠️'}")
    
    overall_ok = network_ok and data_ok
    
    if overall_ok:
        print("✅ Overall validation: PASSED")
        return 0
    else:
        print("❌ Overall validation: FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)