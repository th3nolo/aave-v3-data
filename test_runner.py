#!/usr/bin/env python3
"""
Comprehensive Test Runner for Aave V3 Data Fetcher
Validates script functionality, data accuracy, and protocol parameters.
"""

import sys
import os
import time
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation import validate_aave_data, ValidationResult, save_validation_report
from networks import get_active_networks, validate_all_networks
from graceful_fetcher import fetch_aave_data_gracefully
from ultra_fast_fetcher import fetch_aave_data_ultra_fast
from json_output import validate_json_schema


class TestRunner:
    """Comprehensive test runner for local validation."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results."""
        self.log(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if result:
                self.log(f"✅ {test_name} PASSED ({duration:.2f}s)", "PASS")
                self.test_results.append({
                    "name": test_name,
                    "status": "PASSED",
                    "duration": duration,
                    "error": None
                })
                return True
            else:
                self.log(f"❌ {test_name} FAILED ({duration:.2f}s)", "FAIL")
                self.test_results.append({
                    "name": test_name,
                    "status": "FAILED",
                    "duration": duration,
                    "error": "Test returned False"
                })
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ {test_name} ERROR: {str(e)} ({duration:.2f}s)", "ERROR")
            self.test_results.append({
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            })
            return False
    
    def print_summary(self):
        """Print test execution summary."""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        total = len(self.test_results)
        
        print("\n" + "="*70)
        print("TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print(f"📊 Tests run: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🔴 Errors: {errors}")
        print(f"📈 Success rate: {passed/max(total, 1)*100:.1f}%")
        
        if failed > 0 or errors > 0:
            print("\nFailed/Error Tests:")
            for result in self.test_results:
                if result["status"] in ["FAILED", "ERROR"]:
                    print(f"  ❌ {result['name']}: {result['error']}")
        
        print("="*70)
        
        return passed == total


class DataValidator:
    """Enhanced data validator with 2025 parameter checks."""
    
    def __init__(self):
        # Known protocol values updated for 2025 including supply/borrow caps
        self.known_values_2025 = {
            'ethereum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'decimals': 6,
                    'supply_cap': 2000000000,  # 2B USDC supply cap
                    'borrow_cap': 1800000000   # 1.8B USDC borrow cap
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18,
                    'supply_cap': 1200000,     # 1.2M WETH supply cap
                    'borrow_cap': 1000000      # 1M WETH borrow cap
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.73,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,
                    'decimals': 8,
                    'supply_cap': 40000,       # 40K WBTC supply cap
                    'borrow_cap': 24000        # 24K WBTC borrow cap
                }
            },
            'polygon': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.00,  # Native USDC disabled as collateral
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,
                    'decimals': 6,
                    'supply_cap': 50000000,    # 50M USDC supply cap
                    'borrow_cap': 45000000     # 45M USDC borrow cap
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,
                    'decimals': 6,
                    'supply_cap': 100000000,   # 100M USDC.e supply cap
                    'borrow_cap': 90000000     # 90M USDC.e borrow cap
                },
                'WMATIC': {
                    'liquidation_threshold': 0.65,
                    'loan_to_value': 0.60,
                    'liquidation_bonus': 0.10,
                    'reserve_factor': 0.20,
                    'decimals': 18,
                    'supply_cap': 61000000,    # 61M WMATIC supply cap
                    'borrow_cap': 51000000     # 51M WMATIC borrow cap
                }
            }
        }
    
    def validate_2025_parameters(self, data: Dict[str, List[Dict]]) -> ValidationResult:
        """Validate 2025-specific parameters including supply/borrow caps."""
        result = ValidationResult()
        
        for network_key, assets in data.items():
            if network_key not in self.known_values_2025:
                continue
            
            network_known = self.known_values_2025[network_key]
            
            for asset in assets:
                symbol = asset.get('symbol', '')
                if symbol not in network_known:
                    continue
                
                expected = network_known[symbol]
                self._validate_2025_asset(network_key, symbol, asset, expected, result)
        
        return result
    
    def _validate_2025_asset(self, network_key: str, symbol: str, asset: Dict, expected: Dict, result: ValidationResult):
        """Validate individual asset against 2025 expected values."""
        # Check supply/borrow caps if available
        if 'supply_cap' in expected:
            if 'supply_cap' in asset:
                actual_cap = asset['supply_cap']
                expected_cap = expected['supply_cap']
                
                # Allow 20% tolerance for caps (governance can adjust)
                tolerance = expected_cap * 0.20
                
                if abs(actual_cap - expected_cap) > tolerance:
                    result.add_warning(
                        f"{network_key} {symbol} supply_cap: expected ~{expected_cap}, got {actual_cap}"
                    )
                else:
                    result.add_pass()
            else:
                result.add_warning(f"{network_key} {symbol}: Missing supply_cap parameter")
        
        if 'borrow_cap' in expected:
            if 'borrow_cap' in asset:
                actual_cap = asset['borrow_cap']
                expected_cap = expected['borrow_cap']
                
                # Allow 20% tolerance for caps
                tolerance = expected_cap * 0.20
                
                if abs(actual_cap - expected_cap) > tolerance:
                    result.add_warning(
                        f"{network_key} {symbol} borrow_cap: expected ~{expected_cap}, got {actual_cap}"
                    )
                else:
                    result.add_pass()
            else:
                result.add_warning(f"{network_key} {symbol}: Missing borrow_cap parameter")
        
        # Validate other parameters with standard validation
        for param, expected_value in expected.items():
            if param in ['supply_cap', 'borrow_cap']:
                continue  # Already handled above
            
            if param not in asset:
                continue
            
            actual_value = asset[param]
            
            # Calculate tolerance
            if isinstance(expected_value, float) and expected_value > 0:
                tolerance = max(expected_value * 0.15, 0.05)  # 15% or 5% absolute
            else:
                tolerance = 0.05
            
            if abs(actual_value - expected_value) > tolerance:
                result.add_warning(
                    f"{network_key} {symbol} {param}: expected ~{expected_value}, got {actual_value}"
                )
            else:
                result.add_pass()


def test_network_configuration() -> bool:
    """Test network configuration validity."""
    is_valid, errors = validate_all_networks()
    
    if not is_valid:
        print("Network configuration errors:")
        for network, network_errors in errors.items():
            for error in network_errors:
                print(f"  {network}: {error}")
        return False
    
    networks = get_active_networks()
    if len(networks) < 5:  # Should have at least 5 major networks
        print(f"Expected at least 5 networks, got {len(networks)}")
        return False
    
    return True


def test_data_fetching_graceful() -> bool:
    """Test graceful data fetching functionality."""
    try:
        data, report = fetch_aave_data_gracefully(max_failures=3, save_reports=False)
        
        if not data:
            print("No data returned from graceful fetcher")
            return False
        
        if len(data) < 3:  # Should get data from at least 3 networks
            print(f"Expected data from at least 3 networks, got {len(data)}")
            return False
        
        # Check data structure
        for network_key, assets in data.items():
            if not isinstance(assets, list):
                print(f"Network {network_key} data is not a list")
                return False
            
            if not assets:
                print(f"Network {network_key} has no assets")
                return False
            
            # Check first asset structure
            asset = assets[0]
            required_fields = ['asset_address', 'symbol', 'liquidation_threshold', 'loan_to_value']
            for field in required_fields:
                if field not in asset:
                    print(f"Asset missing required field: {field}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"Graceful fetching failed: {e}")
        return False


def test_data_fetching_ultra_fast() -> bool:
    """Test ultra-fast data fetching functionality."""
    try:
        data, report = fetch_aave_data_ultra_fast(max_network_workers=4, save_reports=False)
        
        if not data:
            print("No data returned from ultra-fast fetcher")
            return False
        
        if len(data) < 3:  # Should get data from at least 3 networks
            print(f"Expected data from at least 3 networks, got {len(data)}")
            return False
        
        # Verify performance report
        if 'fetch_summary' not in report:
            print("Missing fetch_summary in report")
            return False
        
        fetch_summary = report['fetch_summary']
        if fetch_summary.get('total_time', 0) > 300:  # Should complete in under 5 minutes
            print(f"Ultra-fast fetching took too long: {fetch_summary.get('total_time')}s")
            return False
        
        return True
        
    except Exception as e:
        print(f"Ultra-fast fetching failed: {e}")
        return False


def test_data_validation_comprehensive(data: Dict[str, List[Dict]]) -> bool:
    """Test comprehensive data validation."""
    try:
        result = validate_aave_data(data, verbose=False)
        
        # Should have run many checks
        if result.total_checks < 50:
            print(f"Expected at least 50 validation checks, got {result.total_checks}")
            return False
        
        # Should have high success rate
        success_rate = result.passed_checks / max(result.total_checks, 1)
        if success_rate < 0.80:  # 80% success rate minimum
            print(f"Validation success rate too low: {success_rate:.1%}")
            return False
        
        # Should not have critical errors (some warnings are expected)
        if len(result.errors) > 10:
            print(f"Too many validation errors: {len(result.errors)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Data validation failed: {e}")
        return False


def test_2025_parameter_validation(data: Dict[str, List[Dict]]) -> bool:
    """Test 2025-specific parameter validation including supply/borrow caps."""
    try:
        validator = DataValidator()
        result = validator.validate_2025_parameters(data)
        
        # Should have run some checks
        if result.total_checks == 0:
            print("No 2025 parameter checks were run")
            return False
        
        # Allow warnings but not errors for 2025 parameters
        if len(result.errors) > 0:
            print(f"2025 parameter validation errors: {result.errors}")
            return False
        
        return True
        
    except Exception as e:
        print(f"2025 parameter validation failed: {e}")
        return False


def test_json_schema_validation(data: Dict[str, List[Dict]]) -> bool:
    """Test JSON schema validation."""
    try:
        errors = validate_json_schema(data)
        
        if errors:
            print(f"JSON schema validation errors: {errors}")
            return False
        
        return True
        
    except Exception as e:
        print(f"JSON schema validation failed: {e}")
        return False


def test_known_protocol_values(data: Dict[str, List[Dict]]) -> bool:
    """Test against known protocol values."""
    try:
        # Test specific known values
        known_checks = [
            ('ethereum', 'USDC', 'liquidation_threshold', 0.78, 0.05),
            ('ethereum', 'WETH', 'liquidation_threshold', 0.825, 0.05),
            ('polygon', 'USDC', 'loan_to_value', 0.00, 0.01),  # Should be 0 (disabled)
        ]
        
        for network_key, symbol, param, expected, tolerance in known_checks:
            if network_key not in data:
                continue
            
            found = False
            for asset in data[network_key]:
                if asset.get('symbol') == symbol:
                    actual = asset.get(param, 0)
                    if abs(actual - expected) > tolerance:
                        print(f"Known value check failed: {network_key} {symbol} {param} "
                              f"expected {expected}, got {actual}")
                        return False
                    found = True
                    break
            
            if not found:
                print(f"Asset not found for known value check: {network_key} {symbol}")
                # Don't fail the test - asset might not be available
        
        return True
        
    except Exception as e:
        print(f"Known protocol values test failed: {e}")
        return False


def test_network_expansion_scenario() -> bool:
    """Test network expansion scenarios."""
    try:
        networks = get_active_networks()
        
        # Should support major networks
        expected_networks = ['ethereum', 'polygon', 'arbitrum', 'optimism', 'base']
        missing_networks = []
        
        for network in expected_networks:
            if network not in networks:
                missing_networks.append(network)
        
        if missing_networks:
            print(f"Missing expected networks: {missing_networks}")
            return False
        
        # Should have reasonable number of networks (15+ for 2025)
        if len(networks) < 10:
            print(f"Expected at least 10 networks for 2025, got {len(networks)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Network expansion test failed: {e}")
        return False


def test_performance_compliance() -> bool:
    """Test performance compliance for GitHub Actions."""
    try:
        start_time = time.time()
        
        # Run a quick data fetch to test performance
        data, report = fetch_aave_data_graceful(max_failures=2, save_reports=False)
        
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time for CI
        if execution_time > 300:  # 5 minutes
            print(f"Performance test failed: took {execution_time:.1f}s (limit: 300s)")
            return False
        
        return True
        
    except Exception as e:
        print(f"Performance test failed: {e}")
        return False


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description='Comprehensive Aave V3 Data Fetcher Test Runner')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only (skip data fetching)')
    parser.add_argument('--full', action='store_true', help='Run full test suite including data fetching')
    parser.add_argument('--validation-only', action='store_true', help='Run validation tests only')
    parser.add_argument('--save-reports', action='store_true', help='Save test reports to files')
    parser.add_argument('--verbose', action='store_true', default=True, help='Verbose output')
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    print("🧪 Aave V3 Data Fetcher - Comprehensive Test Suite")
    print("=" * 60)
    
    # Always run configuration tests
    runner.run_test("Network Configuration", test_network_configuration)
    runner.run_test("Network Expansion Scenario", test_network_expansion_scenario)
    
    if not args.validation_only:
        if args.full or not args.quick:
            # Data fetching tests
            runner.run_test("Graceful Data Fetching", test_data_fetching_graceful)
            runner.run_test("Ultra-Fast Data Fetching", test_data_fetching_ultra_fast)
            runner.run_test("Performance Compliance", test_performance_compliance)
        
        # Get data for validation tests
        print("\n🔄 Fetching data for validation tests...")
        try:
            data, _ = fetch_aave_data_gracefully(max_failures=3, save_reports=False)
            if not data:
                print("❌ Failed to fetch data for validation tests")
                return 1
        except Exception as e:
            print(f"❌ Failed to fetch data: {e}")
            return 1
    else:
        # Load existing data for validation-only mode
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            print("📂 Loaded existing data for validation tests")
        except FileNotFoundError:
            print("❌ No existing data file found. Run with --full to fetch data first.")
            return 1
        except Exception as e:
            print(f"❌ Failed to load existing data: {e}")
            return 1
    
    # Validation tests
    runner.run_test("Comprehensive Data Validation", test_data_validation_comprehensive, data)
    runner.run_test("2025 Parameter Validation", test_2025_parameter_validation, data)
    runner.run_test("JSON Schema Validation", test_json_schema_validation, data)
    runner.run_test("Known Protocol Values", test_known_protocol_values, data)
    
    # Print summary and save reports if requested
    success = runner.print_summary()
    
    if args.save_reports:
        # Save test results
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "total_time": time.time() - runner.start_time,
            "results": runner.test_results,
            "summary": {
                "total": len(runner.test_results),
                "passed": sum(1 for r in runner.test_results if r["status"] == "PASSED"),
                "failed": sum(1 for r in runner.test_results if r["status"] == "FAILED"),
                "errors": sum(1 for r in runner.test_results if r["status"] == "ERROR")
            }
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(test_report, f, indent=2)
        print("📋 Test report saved to test_report.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)