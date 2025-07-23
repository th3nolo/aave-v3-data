#!/usr/bin/env python3
"""
Protocol Parameter Validation Script
Compares fetched Aave V3 data against known protocol values and 2025 risk updates.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation import validate_aave_data, ValidationResult


class ProtocolParameterValidator:
    """Validator for specific protocol parameters with 2025 updates."""
    
    def __init__(self):
        # Comprehensive known values for 2025 including supply/borrow caps
        self.protocol_values_2025 = {
            'ethereum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 2000000000,  # 2B USDC
                    'borrow_cap_expected': 1800000000   # 1.8B USDC
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 1200000,     # 1.2M WETH
                    'borrow_cap_expected': 1000000      # 1M WETH
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,     # Updated from 0.70
                    'loan_to_value': 0.73,             # Updated from 0.65
                    'liquidation_bonus': 0.05,         # Updated from 0.10
                    'reserve_factor': 0.50,            # Updated from 0.20
                    'decimals': 8,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 40000,       # 40K WBTC
                    'borrow_cap_expected': 24000        # 24K WBTC
                },
                'DAI': {
                    'liquidation_threshold': 0.77,
                    'loan_to_value': 0.63,             # Updated from 0.75
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.25,            # Updated from 0.10
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': True,
                    'supply_cap_expected': 100000000,   # 100M DAI
                    'borrow_cap_expected': 85000000     # 85M DAI
                }
            },
            'polygon': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.00,             # Native USDC disabled as collateral
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,            # Updated from 0.10
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 50000000,    # 50M USDC
                    'borrow_cap_expected': 45000000     # 45M USDC
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,            # Updated from 0.10
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 100000000,   # 100M USDC.e
                    'borrow_cap_expected': 90000000     # 90M USDC.e
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 10000,       # 10K WETH
                    'borrow_cap_expected': 8000         # 8K WETH
                },
                'WMATIC': {
                    'liquidation_threshold': 0.65,
                    'loan_to_value': 0.60,
                    'liquidation_bonus': 0.10,
                    'reserve_factor': 0.20,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 61000000,    # 61M WMATIC
                    'borrow_cap_expected': 51000000     # 51M WMATIC
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,     # Updated from 0.70
                    'loan_to_value': 0.73,             # Updated from 0.65
                    'liquidation_bonus': 0.065,        # Updated from 0.10
                    'reserve_factor': 0.50,            # Updated from 0.20
                    'decimals': 8,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 3200,        # 3.2K WBTC
                    'borrow_cap_expected': 1920         # 1.92K WBTC
                }
            },
            'arbitrum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,            # Native USDC
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 200000000,   # 200M USDC
                    'borrow_cap_expected': 180000000    # 180M USDC
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,            # Updated from 0.10
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 300000000,   # 300M USDC.e
                    'borrow_cap_expected': 270000000    # 270M USDC.e
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 70000,       # 70K WETH
                    'borrow_cap_expected': 56000        # 56K WETH
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,     # Updated from 0.70
                    'loan_to_value': 0.73,             # Updated from 0.65
                    'liquidation_bonus': 0.07,         # Updated from 0.10
                    'reserve_factor': 0.50,            # Updated from 0.20
                    'decimals': 8,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 4200,        # 4.2K WBTC
                    'borrow_cap_expected': 2520         # 2.52K WBTC
                }
            },
            'optimism': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,            # Updated to match current
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 100000000,   # 100M USDC
                    'borrow_cap_expected': 90000000     # 90M USDC
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,            # Updated from 0.10
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 150000000,   # 150M USDC.e
                    'borrow_cap_expected': 135000000    # 135M USDC.e
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 35000,       # 35K WETH
                    'borrow_cap_expected': 28000        # 28K WETH
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,     # Updated from 0.70
                    'loan_to_value': 0.73,             # Updated from 0.65
                    'liquidation_bonus': 0.075,        # Updated from 0.10
                    'reserve_factor': 0.50,            # Updated from 0.20
                    'decimals': 8,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 1200,        # 1.2K WBTC
                    'borrow_cap_expected': 720          # 720 WBTC
                }
            },
            'base': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'decimals': 6,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 50000000,    # 50M USDC
                    'borrow_cap_expected': 45000000     # 45M USDC
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'active': True,
                    'borrowing_enabled': True,
                    'stable_borrowing_enabled': False,
                    'supply_cap_expected': 9000,        # 9K WETH
                    'borrow_cap_expected': 7200         # 7.2K WETH
                }
            }
        }
        
        # Tolerance settings
        self.parameter_tolerance = 0.15  # 15% tolerance for most parameters
        self.cap_tolerance = 0.25        # 25% tolerance for supply/borrow caps (more volatile)
        self.strict_tolerance = 0.05     # 5% tolerance for critical parameters
    
    def validate_protocol_parameters(self, data: Dict[str, List[Dict]]) -> ValidationResult:
        """Validate all protocol parameters against known values."""
        result = ValidationResult()
        
        print("🔍 Validating protocol parameters against known 2025 values...")
        
        for network_key, assets in data.items():
            if network_key not in self.protocol_values_2025:
                result.add_info(f"No known values for network: {network_key}")
                continue
            
            network_known = self.protocol_values_2025[network_key]
            result.add_info(f"Validating {len(assets)} assets in {network_key}")
            
            for asset in assets:
                symbol = asset.get('symbol', 'UNKNOWN')
                
                if symbol in network_known:
                    self._validate_asset_parameters(network_key, symbol, asset, network_known[symbol], result)
                else:
                    result.add_info(f"No known values for {network_key} {symbol}")
        
        return result
    
    def _validate_asset_parameters(
        self, 
        network_key: str, 
        symbol: str, 
        asset: Dict, 
        expected: Dict, 
        result: ValidationResult
    ):
        """Validate individual asset parameters."""
        # Critical parameters (strict tolerance)
        critical_params = ['liquidation_threshold', 'loan_to_value', 'decimals']
        
        # Standard parameters (normal tolerance)
        standard_params = ['liquidation_bonus', 'reserve_factor']
        
        # Boolean parameters
        boolean_params = ['active', 'borrowing_enabled', 'stable_borrowing_enabled']
        
        # Cap parameters (higher tolerance)
        cap_params = ['supply_cap_expected', 'borrow_cap_expected']
        
        # Validate critical parameters
        for param in critical_params:
            if param in expected and param in asset:
                expected_val = expected[param]
                actual_val = asset[param]
                tolerance = expected_val * self.strict_tolerance if expected_val > 0 else self.strict_tolerance
                
                if abs(actual_val - expected_val) > tolerance:
                    result.add_error(
                        f"{network_key} {symbol} {param}: expected {expected_val}, got {actual_val} "
                        f"(diff: {abs(actual_val - expected_val):.4f}, tolerance: {tolerance:.4f})"
                    )
                else:
                    result.add_pass()
        
        # Validate standard parameters
        for param in standard_params:
            if param in expected and param in asset:
                expected_val = expected[param]
                actual_val = asset[param]
                tolerance = expected_val * self.parameter_tolerance if expected_val > 0 else self.parameter_tolerance
                
                if abs(actual_val - expected_val) > tolerance:
                    result.add_warning(
                        f"{network_key} {symbol} {param}: expected {expected_val}, got {actual_val} "
                        f"(diff: {abs(actual_val - expected_val):.4f})"
                    )
                else:
                    result.add_pass()
        
        # Validate boolean parameters
        for param in boolean_params:
            if param in expected and param in asset:
                expected_val = expected[param]
                actual_val = asset[param]
                
                if actual_val != expected_val:
                    result.add_warning(
                        f"{network_key} {symbol} {param}: expected {expected_val}, got {actual_val}"
                    )
                else:
                    result.add_pass()
        
        # Validate supply/borrow caps (2025 feature)
        for cap_param in cap_params:
            if cap_param in expected:
                # Map expected parameter to actual parameter name
                actual_param = cap_param.replace('_expected', '')
                
                if actual_param in asset:
                    expected_val = expected[cap_param]
                    actual_val = asset[actual_param]
                    tolerance = expected_val * self.cap_tolerance
                    
                    if abs(actual_val - expected_val) > tolerance:
                        result.add_warning(
                            f"{network_key} {symbol} {actual_param}: expected ~{expected_val}, got {actual_val} "
                            f"(diff: {abs(actual_val - expected_val):.0f})"
                        )
                    else:
                        result.add_pass()
                else:
                    result.add_info(f"{network_key} {symbol}: Missing {actual_param} parameter")
    
    def generate_comparison_report(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Generate detailed comparison report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "networks_analyzed": list(data.keys()),
            "total_assets": sum(len(assets) for assets in data.values()),
            "comparisons": {},
            "summary": {
                "exact_matches": 0,
                "within_tolerance": 0,
                "significant_differences": 0,
                "missing_parameters": 0
            }
        }
        
        for network_key, assets in data.items():
            if network_key not in self.protocol_values_2025:
                continue
            
            network_known = self.protocol_values_2025[network_key]
            network_comparisons = {}
            
            for asset in assets:
                symbol = asset.get('symbol', 'UNKNOWN')
                
                if symbol in network_known:
                    comparison = self._compare_asset_detailed(asset, network_known[symbol])
                    network_comparisons[symbol] = comparison
                    
                    # Update summary
                    report["summary"]["exact_matches"] += comparison["exact_matches"]
                    report["summary"]["within_tolerance"] += comparison["within_tolerance"]
                    report["summary"]["significant_differences"] += comparison["significant_differences"]
                    report["summary"]["missing_parameters"] += comparison["missing_parameters"]
            
            if network_comparisons:
                report["comparisons"][network_key] = network_comparisons
        
        return report
    
    def _compare_asset_detailed(self, asset: Dict, expected: Dict) -> Dict[str, Any]:
        """Generate detailed comparison for a single asset."""
        comparison = {
            "exact_matches": 0,
            "within_tolerance": 0,
            "significant_differences": 0,
            "missing_parameters": 0,
            "parameter_details": {}
        }
        
        for param, expected_val in expected.items():
            if param.endswith('_expected'):
                # Handle cap parameters
                actual_param = param.replace('_expected', '')
                if actual_param in asset:
                    actual_val = asset[actual_param]
                    tolerance = expected_val * self.cap_tolerance
                    diff = abs(actual_val - expected_val)
                    
                    if diff == 0:
                        comparison["exact_matches"] += 1
                        status = "exact"
                    elif diff <= tolerance:
                        comparison["within_tolerance"] += 1
                        status = "within_tolerance"
                    else:
                        comparison["significant_differences"] += 1
                        status = "significant_difference"
                    
                    comparison["parameter_details"][actual_param] = {
                        "expected": expected_val,
                        "actual": actual_val,
                        "difference": diff,
                        "tolerance": tolerance,
                        "status": status
                    }
                else:
                    comparison["missing_parameters"] += 1
                    comparison["parameter_details"][actual_param] = {
                        "expected": expected_val,
                        "actual": None,
                        "status": "missing"
                    }
            
            elif param in asset:
                actual_val = asset[param]
                
                if isinstance(expected_val, bool):
                    if actual_val == expected_val:
                        comparison["exact_matches"] += 1
                        status = "exact"
                    else:
                        comparison["significant_differences"] += 1
                        status = "different"
                    
                    comparison["parameter_details"][param] = {
                        "expected": expected_val,
                        "actual": actual_val,
                        "status": status
                    }
                
                elif isinstance(expected_val, (int, float)):
                    tolerance = expected_val * self.parameter_tolerance if expected_val > 0 else self.parameter_tolerance
                    diff = abs(actual_val - expected_val)
                    
                    if diff == 0:
                        comparison["exact_matches"] += 1
                        status = "exact"
                    elif diff <= tolerance:
                        comparison["within_tolerance"] += 1
                        status = "within_tolerance"
                    else:
                        comparison["significant_differences"] += 1
                        status = "significant_difference"
                    
                    comparison["parameter_details"][param] = {
                        "expected": expected_val,
                        "actual": actual_val,
                        "difference": diff,
                        "tolerance": tolerance,
                        "status": status
                    }
        
        return comparison


def load_data_from_file(filepath: str) -> Optional[Dict[str, List[Dict]]]:
    """Load Aave data from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"📂 Loaded data from {filepath}")
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(description='Validate Aave V3 Protocol Parameters')
    parser.add_argument('--data-file', default='aave_v3_data.json', help='JSON data file to validate')
    parser.add_argument('--save-report', action='store_true', help='Save detailed comparison report')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🔍 Aave V3 Protocol Parameter Validation")
    print("=" * 50)
    
    # Load data
    data = load_data_from_file(args.data_file)
    if not data:
        return 1
    
    print(f"� Loaded dTata for {len(data)} networks")
    total_assets = sum(len(assets) for assets in data.values())
    print(f"� STotal assets: {total_assets}")
    
    # Run validation
    validator = ProtocolParameterValidator()
    result = validator.validate_protocol_parameters(data)
    
    # Print results
    print(f"\n✅ Validation completed:")
    print(f"   📊 Total checks: {result.total_checks}")
    print(f"   ✅ Passed: {result.passed_checks}")
    print(f"   ❌ Errors: {len(result.errors)}")
    print(f"   ⚠️  Warnings: {len(result.warnings)}")
    print(f"   📈 Success rate: {result.passed_checks/max(result.total_checks, 1)*100:.1f}%")
    
    if args.verbose:
        if result.errors:
            print(f"\n❌ ERRORS ({len(result.errors)}):")
            for error in result.errors:
                print(f"   {error}")
        
        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for warning in result.warnings[:10]:  # Limit to first 10
                print(f"   {warning}")
            if len(result.warnings) > 10:
                print(f"   ... and {len(result.warnings) - 10} more warnings")
    
    # Generate and save detailed report if requested
    if args.save_report:
        report = validator.generate_comparison_report(data)
        report_file = 'protocol_parameter_comparison.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Detailed comparison report saved to {report_file}")
    
    # Return appropriate exit code
    if len(result.errors) > 0:
        print("\n❌ Validation failed due to errors")
        return 1
    elif len(result.warnings) > 20:  # Too many warnings might indicate issues
        print("\n⚠️  Validation completed with many warnings")
        return 2
    else:
        print("\n✅ Validation passed successfully")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)