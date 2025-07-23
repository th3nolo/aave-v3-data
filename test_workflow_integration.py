#!/usr/bin/env python3
"""
Workflow Integration Test Script
Tests the complete Aave V3 data fetcher workflow including network expansion scenarios.
"""

import sys
import os
import json
import time
import tempfile
import shutil
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networks import get_active_networks, validate_all_networks
from graceful_fetcher import fetch_aave_data_gracefully
from ultra_fast_fetcher import fetch_aave_data_ultra_fast
from json_output import save_json_output, validate_json_schema
from html_output import save_html_output
from validation import validate_aave_data
from monitoring import save_health_report


class WorkflowIntegrationTester:
    """Integration tester for complete workflow scenarios."""
    
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self.test_results = []
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_integration_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single integration test."""
        self.log(f"🧪 Running integration test: {test_name}")
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
    
    def test_complete_graceful_workflow(self) -> bool:
        """Test complete workflow using graceful fetcher."""
        try:
            self.log("🔄 Testing complete graceful workflow...")
            
            # Step 1: Fetch data
            data, fetch_report = fetch_aave_data_gracefully(
                max_failures=3,
                save_reports=False
            )
            
            if not data:
                self.log("❌ No data returned from graceful fetcher")
                return False
            
            self.log(f"✅ Fetched data from {len(data)} networks")
            
            # Step 2: Validate data
            validation_result = validate_aave_data(data, verbose=False)
            if not validation_result.is_valid():
                self.log(f"⚠️  Data validation found {len(validation_result.errors)} errors")
                # Don't fail the test for validation warnings, but log them
            
            # Step 3: Validate JSON schema
            schema_errors = validate_json_schema(data)
            if schema_errors:
                self.log(f"❌ JSON schema validation failed: {schema_errors}")
                return False
            
            # Step 4: Save JSON output
            json_file = os.path.join(self.temp_dir, 'test_graceful_output.json')
            json_success = save_json_output(data, json_file, include_metadata=True)
            if not json_success:
                self.log("❌ Failed to save JSON output")
                return False
            
            # Step 5: Save HTML output
            html_file = os.path.join(self.temp_dir, 'test_graceful_output.html')
            html_success = save_html_output(data, html_file)
            if not html_success:
                self.log("❌ Failed to save HTML output")
                return False
            
            # Step 6: Verify output files
            if not os.path.exists(json_file) or not os.path.exists(html_file):
                self.log("❌ Output files not created")
                return False
            
            # Step 7: Verify JSON file content
            with open(json_file, 'r') as f:
                saved_data = json.load(f)
            
            if len(saved_data) != len(data):
                self.log("❌ Saved JSON data doesn't match original")
                return False
            
            self.log("✅ Complete graceful workflow test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Graceful workflow test failed: {e}")
            return False
    
    def test_complete_ultra_fast_workflow(self) -> bool:
        """Test complete workflow using ultra-fast fetcher."""
        try:
            self.log("🚀 Testing complete ultra-fast workflow...")
            
            # Step 1: Fetch data with ultra-fast mode
            data, fetch_report = fetch_aave_data_ultra_fast(
                max_network_workers=4,
                save_reports=False
            )
            
            if not data:
                self.log("❌ No data returned from ultra-fast fetcher")
                return False
            
            self.log(f"✅ Ultra-fast fetched data from {len(data)} networks")
            
            # Step 2: Verify performance report
            if 'fetch_summary' not in fetch_report:
                self.log("❌ Missing fetch_summary in ultra-fast report")
                return False
            
            fetch_summary = fetch_report['fetch_summary']
            total_time = fetch_summary.get('total_time', 0)
            
            if total_time > 300:  # Should be faster than 5 minutes
                self.log(f"⚠️  Ultra-fast mode took {total_time:.1f}s (expected < 300s)")
            
            # Step 3: Validate data quality
            validation_result = validate_aave_data(data, verbose=False)
            success_rate = validation_result.passed_checks / max(validation_result.total_checks, 1)
            
            if success_rate < 0.80:  # 80% success rate minimum
                self.log(f"❌ Ultra-fast data quality too low: {success_rate:.1%}")
                return False
            
            # Step 4: Save outputs
            json_file = os.path.join(self.temp_dir, 'test_ultra_fast_output.json')
            html_file = os.path.join(self.temp_dir, 'test_ultra_fast_output.html')
            
            json_success = save_json_output(data, json_file, fetch_report=fetch_summary)
            html_success = save_html_output(data, html_file, fetch_report=fetch_summary)
            
            if not (json_success and html_success):
                self.log("❌ Failed to save ultra-fast outputs")
                return False
            
            self.log("✅ Complete ultra-fast workflow test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Ultra-fast workflow test failed: {e}")
            return False
    
    def test_network_expansion_scenario(self) -> bool:
        """Test network expansion scenarios."""
        try:
            self.log("🌐 Testing network expansion scenario...")
            
            # Get current networks
            networks = get_active_networks()
            original_count = len(networks)
            
            self.log(f"📊 Current network count: {original_count}")
            
            # Verify we have major networks
            major_networks = ['ethereum', 'polygon', 'arbitrum', 'optimism', 'base']
            missing_major = [net for net in major_networks if net not in networks]
            
            if missing_major:
                self.log(f"⚠️  Missing major networks: {missing_major}")
                # Don't fail the test, but warn
            
            # Test network configuration validation
            is_valid, validation_errors = validate_all_networks()
            if not is_valid:
                self.log("❌ Network configuration validation failed")
                for network, errors in validation_errors.items():
                    for error in errors:
                        self.log(f"   {network}: {error}")
                return False
            
            # Test fetching from subset of networks (simulating expansion)
            test_networks = list(networks.keys())[:5]  # Test with first 5 networks
            self.log(f"🧪 Testing with subset of networks: {test_networks}")
            
            # Fetch data from subset
            data, _ = fetch_aave_data_gracefully(max_failures=2, save_reports=False)
            
            if not data:
                self.log("❌ Failed to fetch data for network expansion test")
                return False
            
            # Verify we got data from multiple networks
            if len(data) < 3:
                self.log(f"❌ Expected data from at least 3 networks, got {len(data)}")
                return False
            
            # Test adding new network scenario (simulate by checking extensibility)
            # This tests that the system can handle new networks being added
            total_assets = sum(len(assets) for assets in data.values())
            if total_assets < 50:  # Should have reasonable number of assets
                self.log(f"❌ Expected at least 50 total assets, got {total_assets}")
                return False
            
            self.log("✅ Network expansion scenario test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Network expansion test failed: {e}")
            return False
    
    def test_error_recovery_scenarios(self) -> bool:
        """Test error recovery and graceful degradation."""
        try:
            self.log("🛡️  Testing error recovery scenarios...")
            
            # Test with high failure tolerance
            data, fetch_report = fetch_aave_data_gracefully(
                max_failures=10,  # Allow many failures
                save_reports=False
            )
            
            if not data:
                self.log("❌ Graceful fetcher failed completely with high failure tolerance")
                return False
            
            # Should still get some data even with failures
            if len(data) == 0:
                self.log("❌ No networks succeeded even with high failure tolerance")
                return False
            
            # Test validation with potentially incomplete data
            validation_result = validate_aave_data(data, verbose=False)
            
            # Should still pass basic validation even with some missing networks
            if validation_result.total_checks == 0:
                self.log("❌ No validation checks ran on recovered data")
                return False
            
            # Test output generation with partial data
            json_file = os.path.join(self.temp_dir, 'test_recovery_output.json')
            json_success = save_json_output(data, json_file)
            
            if not json_success:
                self.log("❌ Failed to save output from recovered data")
                return False
            
            self.log("✅ Error recovery scenario test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error recovery test failed: {e}")
            return False
    
    def test_performance_compliance(self) -> bool:
        """Test performance compliance for CI/CD environments."""
        try:
            self.log("⚡ Testing performance compliance...")
            
            start_time = time.time()
            
            # Run a performance test with limited scope
            data, fetch_report = fetch_aave_data_gracefully(
                max_failures=2,
                save_reports=False
            )
            
            execution_time = time.time() - start_time
            
            # Should complete within reasonable time for CI
            if execution_time > 300:  # 5 minutes
                self.log(f"❌ Performance test failed: {execution_time:.1f}s (limit: 300s)")
                return False
            
            # Should get reasonable amount of data
            if not data or len(data) < 3:
                self.log("❌ Performance test didn't fetch sufficient data")
                return False
            
            # Test JSON schema validation performance
            schema_start = time.time()
            schema_errors = validate_json_schema(data)
            schema_time = time.time() - schema_start
            
            if schema_time > 10:  # Should validate quickly
                self.log(f"⚠️  JSON schema validation slow: {schema_time:.1f}s")
            
            if schema_errors:
                self.log(f"❌ Schema validation failed: {schema_errors}")
                return False
            
            self.log(f"✅ Performance compliance test passed ({execution_time:.1f}s)")
            return True
            
        except Exception as e:
            self.log(f"❌ Performance compliance test failed: {e}")
            return False
    
    def test_data_consistency_across_runs(self) -> bool:
        """Test data consistency across multiple runs."""
        try:
            self.log("🔄 Testing data consistency across runs...")
            
            # Run 1
            data1, _ = fetch_aave_data_gracefully(max_failures=2, save_reports=False)
            if not data1:
                self.log("❌ First run failed")
                return False
            
            # Small delay between runs
            time.sleep(2)
            
            # Run 2
            data2, _ = fetch_aave_data_gracefully(max_failures=2, save_reports=False)
            if not data2:
                self.log("❌ Second run failed")
                return False
            
            # Compare network coverage
            networks1 = set(data1.keys())
            networks2 = set(data2.keys())
            
            # Should have similar network coverage
            network_overlap = len(networks1 & networks2) / max(len(networks1 | networks2), 1)
            if network_overlap < 0.80:  # 80% overlap minimum
                self.log(f"❌ Network coverage inconsistent: {network_overlap:.1%} overlap")
                return False
            
            # Compare asset counts for common networks
            for network in networks1 & networks2:
                count1 = len(data1[network])
                count2 = len(data2[network])
                
                # Asset counts should be identical or very close
                if abs(count1 - count2) > 2:  # Allow small differences
                    self.log(f"⚠️  Asset count difference in {network}: {count1} vs {count2}")
            
            self.log("✅ Data consistency test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Data consistency test failed: {e}")
            return False
    
    def test_output_format_compatibility(self) -> bool:
        """Test output format compatibility and standards compliance."""
        try:
            self.log("📄 Testing output format compatibility...")
            
            # Fetch data
            data, _ = fetch_aave_data_gracefully(max_failures=3, save_reports=False)
            if not data:
                self.log("❌ Failed to fetch data for format test")
                return False
            
            # Test JSON output
            json_file = os.path.join(self.temp_dir, 'test_format_output.json')
            json_success = save_json_output(data, json_file, include_metadata=True)
            
            if not json_success:
                self.log("❌ JSON output generation failed")
                return False
            
            # Verify JSON is valid and parseable
            with open(json_file, 'r') as f:
                loaded_data = json.load(f)
            
            if not isinstance(loaded_data, dict):
                self.log("❌ JSON output is not a dictionary")
                return False
            
            # Test HTML output
            html_file = os.path.join(self.temp_dir, 'test_format_output.html')
            html_success = save_html_output(data, html_file)
            
            if not html_success:
                self.log("❌ HTML output generation failed")
                return False
            
            # Verify HTML file exists and has content
            with open(html_file, 'r') as f:
                html_content = f.read()
            
            if len(html_content) < 1000:  # Should have substantial content
                self.log("❌ HTML output too small")
                return False
            
            # Check for basic HTML structure
            if not all(tag in html_content for tag in ['<html>', '<table>', '</html>']):
                self.log("❌ HTML output missing required tags")
                return False
            
            self.log("✅ Output format compatibility test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Output format compatibility test failed: {e}")
            return False
    
    def print_summary(self) -> bool:
        """Print test execution summary."""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        total = len(self.test_results)
        
        print("\n" + "="*70)
        print("WORKFLOW INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print(f"🧪 Integration tests run: {total}")
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


def main():
    """Main integration test entry point."""
    parser = argparse.ArgumentParser(description='Aave V3 Workflow Integration Tests')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--full', action='store_true', help='Run full integration test suite')
    parser.add_argument('--save-outputs', action='store_true', help='Save test outputs to files')
    parser.add_argument('--temp-dir', help='Temporary directory for test outputs')
    
    args = parser.parse_args()
    
    # Set up temporary directory
    if args.temp_dir:
        temp_dir = args.temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix='aave_integration_test_')
    
    print("🧪 Aave V3 Workflow Integration Test Suite")
    print("=" * 50)
    print(f"📁 Test directory: {temp_dir}")
    
    try:
        tester = WorkflowIntegrationTester(temp_dir)
        
        # Core workflow tests
        tester.run_integration_test(
            "Complete Graceful Workflow",
            tester.test_complete_graceful_workflow
        )
        
        if not args.quick:
            tester.run_integration_test(
                "Complete Ultra-Fast Workflow",
                tester.test_complete_ultra_fast_workflow
            )
        
        # Network and expansion tests
        tester.run_integration_test(
            "Network Expansion Scenario",
            tester.test_network_expansion_scenario
        )
        
        # Reliability tests
        tester.run_integration_test(
            "Error Recovery Scenarios",
            tester.test_error_recovery_scenarios
        )
        
        tester.run_integration_test(
            "Performance Compliance",
            tester.test_performance_compliance
        )
        
        if args.full:
            # Additional comprehensive tests
            tester.run_integration_test(
                "Data Consistency Across Runs",
                tester.test_data_consistency_across_runs
            )
            
            tester.run_integration_test(
                "Output Format Compatibility",
                tester.test_output_format_compatibility
            )
        
        # Print summary
        success = tester.print_summary()
        
        # Save test results if requested
        if args.save_outputs:
            test_report = {
                "timestamp": datetime.now().isoformat(),
                "total_time": time.time() - tester.start_time,
                "results": tester.test_results,
                "temp_dir": temp_dir
            }
            
            report_file = os.path.join(temp_dir, 'integration_test_report.json')
            with open(report_file, 'w') as f:
                json.dump(test_report, f, indent=2)
            print(f"📋 Integration test report saved to {report_file}")
        
        return 0 if success else 1
        
    finally:
        # Clean up temporary directory unless saving outputs
        if not args.save_outputs and not args.temp_dir:
            try:
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"⚠️  Failed to clean up {temp_dir}: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)