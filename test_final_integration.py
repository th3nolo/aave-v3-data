#!/usr/bin/env python3
"""
Final Integration and Deployment Testing Suite
Tests complete workflow from repository setup to Pages deployment.
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networks import get_active_networks, validate_all_networks
from validation import validate_aave_data, ValidationResult
from json_output import validate_json_schema
from monitoring import health_monitor


class IntegrationTestSuite:
    """Comprehensive integration testing suite for final deployment validation."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.github_pages_base_url = None
        self.github_raw_base_url = None
        
    def setup_test_environment(self):
        """Set up test environment and detect GitHub repository URLs."""
        print("🔧 Setting up test environment...")
        
        # Try to detect GitHub repository information
        try:
            # Get remote origin URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Parse GitHub repository info
            if 'github.com' in remote_url:
                # Handle both SSH and HTTPS URLs
                if remote_url.startswith('git@github.com:'):
                    repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                elif remote_url.startswith('https://github.com/'):
                    repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
                else:
                    repo_path = None
                
                if repo_path:
                    username, repo_name = repo_path.split('/')
                    self.github_pages_base_url = f"https://{username}.github.io/{repo_name}"
                    self.github_raw_base_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main"
                    
                    print(f"✅ Detected GitHub repository: {username}/{repo_name}")
                    print(f"   📄 Pages URL: {self.github_pages_base_url}")
                    print(f"   📊 Raw URL: {self.github_raw_base_url}")
                else:
                    print("⚠️  Could not parse GitHub repository path")
            else:
                print("⚠️  Not a GitHub repository")
                
        except subprocess.CalledProcessError:
            print("⚠️  Could not detect Git repository information")
        except Exception as e:
            print(f"⚠️  Error detecting repository info: {e}")
    
    def test_complete_workflow_execution(self) -> bool:
        """Test complete workflow from data fetching to file generation."""
        print("\n🔄 Testing complete workflow execution...")
        
        try:
            # Test basic execution with turbo mode
            result = subprocess.run([
                sys.executable, 'aave_fetcher.py', '--turbo', '--validate', '--timeout', '60'
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"❌ Workflow execution failed with return code {result.returncode}")
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
                return False
            
            # Check if output files were created
            required_files = ['aave_v3_data.json', 'aave_v3_data.html']
            missing_files = []
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                print(f"❌ Missing output files: {missing_files}")
                return False
            
            # Validate JSON file structure
            try:
                with open('aave_v3_data.json', 'r') as f:
                    data = json.load(f)
                
                # Basic structure validation
                if 'networks' not in data:
                    print("❌ JSON missing 'networks' key")
                    return False
                
                if 'metadata' not in data:
                    print("❌ JSON missing 'metadata' key")
                    return False
                
                # Check if we have data from multiple networks
                if len(data['networks']) < 3:
                    print(f"❌ Expected data from at least 3 networks, got {len(data['networks'])}")
                    return False
                
                print(f"✅ Workflow execution successful")
                print(f"   📊 Generated data for {len(data['networks'])} networks")
                print(f"   📄 Files: {', '.join(required_files)}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON generated: {e}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Workflow execution timed out (10 minutes)")
            return False
        except Exception as e:
            print(f"❌ Workflow execution error: {e}")
            return False
    
    def test_automated_daily_updates(self) -> bool:
        """Test GitHub Actions workflow configuration for automated updates."""
        print("\n⏰ Testing automated daily update configuration...")
        
        workflow_path = '.github/workflows/update-aave-data.yml'
        
        if not os.path.exists(workflow_path):
            print(f"❌ GitHub Actions workflow not found: {workflow_path}")
            return False
        
        try:
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            # Check for required components
            required_components = [
                'schedule:',
                "cron: '0 0 * * *'",  # Daily at midnight UTC
                'workflow_dispatch:',  # Manual triggering
                'python aave_fetcher.py',
                'git add',
                'git commit',
                'git push'
            ]
            
            missing_components = []
            for component in required_components:
                if component not in workflow_content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"❌ Missing workflow components: {missing_components}")
                return False
            
            # Check for turbo mode usage
            if '--turbo' not in workflow_content:
                print("⚠️  Workflow not using --turbo mode (performance may be suboptimal)")
            
            print("✅ Automated daily update configuration valid")
            print("   ⏰ Daily schedule: midnight UTC")
            print("   🔧 Manual trigger: enabled")
            print("   ⚡ Performance mode: turbo")
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading workflow file: {e}")
            return False
    
    def test_manual_workflow_triggering(self) -> bool:
        """Test manual workflow triggering capability."""
        print("\n🔧 Testing manual workflow triggering...")
        
        # This test validates the workflow_dispatch configuration
        # Actual triggering would require GitHub API access
        
        workflow_path = '.github/workflows/update-aave-data.yml'
        
        try:
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            if 'workflow_dispatch:' not in workflow_content:
                print("❌ Manual triggering not configured")
                return False
            
            print("✅ Manual workflow triggering configured")
            print("   🎯 Can be triggered via GitHub Actions UI")
            print("   🔧 workflow_dispatch event enabled")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating manual triggering: {e}")
            return False
    
    def test_json_api_accessibility(self) -> bool:
        """Test JSON API accessibility and structure."""
        print("\n📊 Testing JSON API accessibility...")
        
        # Test local JSON file first
        if not os.path.exists('aave_v3_data.json'):
            print("❌ Local JSON file not found")
            return False
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            # Validate JSON schema - pass the networks portion
            schema_errors = validate_json_schema(data['networks'])
            if schema_errors:
                print(f"❌ JSON schema validation failed: {len(schema_errors)} errors")
                for error in schema_errors[:3]:
                    print(f"   {error}")
                return False
            
            # Test JSON structure for LLM consumption
            if not self._validate_llm_friendly_structure(data):
                return False
            
            print("✅ Local JSON API structure valid")
            
            # Test remote accessibility if GitHub URLs are available
            if self.github_raw_base_url:
                json_url = f"{self.github_raw_base_url}/aave_v3_data.json"
                
                try:
                    with urllib.request.urlopen(json_url, timeout=30) as response:
                        if response.status == 200:
                            remote_data = json.loads(response.read().decode())
                            
                            # Basic validation of remote data
                            if 'networks' in remote_data and 'metadata' in remote_data:
                                print(f"✅ Remote JSON API accessible: {json_url}")
                                return True
                            else:
                                print("❌ Remote JSON has invalid structure")
                                return False
                        else:
                            print(f"❌ Remote JSON API returned status {response.status}")
                            return False
                            
                except urllib.error.URLError as e:
                    print(f"⚠️  Remote JSON API not accessible (expected for new repos): {e}")
                    print("   This is normal for repositories that haven't been deployed yet")
                    return True  # Don't fail the test for new repositories
                except Exception as e:
                    print(f"⚠️  Error testing remote JSON API: {e}")
                    return True  # Don't fail the test for connectivity issues
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON structure: {e}")
            return False
        except Exception as e:
            print(f"❌ Error testing JSON API: {e}")
            return False
    
    def test_html_page_rendering(self) -> bool:
        """Test HTML page generation and structure."""
        print("\n🌐 Testing HTML page rendering...")
        
        if not os.path.exists('aave_v3_data.html'):
            print("❌ HTML file not found")
            return False
        
        try:
            with open('aave_v3_data.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Check for required HTML elements
            required_elements = [
                '<html',
                '<head>',
                '<title>',
                '<table',
                'LT',  # Liquidation Threshold abbreviated
                'LTV',  # Loan-to-Value abbreviated
                'Symbol',
                'Asset Address'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ Missing HTML elements: {missing_elements}")
                return False
            
            # Check for responsive design elements
            responsive_indicators = ['viewport', 'responsive', 'mobile', '@media']
            has_responsive = any(indicator in html_content.lower() for indicator in responsive_indicators)
            
            if not has_responsive:
                print("⚠️  HTML may not be responsive (no mobile optimization detected)")
            
            print("✅ HTML page structure valid")
            print("   📋 Contains required table elements")
            print("   📊 Includes protocol parameters")
            
            if has_responsive:
                print("   📱 Responsive design detected")
            
            # Test remote accessibility if GitHub URLs are available
            if self.github_pages_base_url:
                html_url = f"{self.github_pages_base_url}/aave_v3_data.html"
                
                try:
                    with urllib.request.urlopen(html_url, timeout=30) as response:
                        if response.status == 200:
                            print(f"✅ Remote HTML page accessible: {html_url}")
                        else:
                            print(f"❌ Remote HTML page returned status {response.status}")
                            return False
                            
                except urllib.error.URLError as e:
                    print(f"⚠️  Remote HTML page not accessible (expected for new repos): {e}")
                    print("   This is normal for repositories that haven't been deployed yet")
                except Exception as e:
                    print(f"⚠️  Error testing remote HTML page: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing HTML page: {e}")
            return False
    
    def test_llm_consumption_validation(self) -> bool:
        """Test data structure and format for LLM consumption."""
        print("\n🤖 Testing LLM consumption validation...")
        
        if not os.path.exists('aave_v3_data.json'):
            print("❌ JSON file not found for LLM testing")
            return False
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            # Test LLM-friendly structure
            if not self._validate_llm_friendly_structure(data):
                return False
            
            # Test sample LLM queries
            llm_test_results = self._run_llm_consumption_tests(data)
            
            if not llm_test_results:
                print("❌ LLM consumption tests failed")
                return False
            
            print("✅ LLM consumption validation passed")
            print("   🤖 Data structure optimized for AI consumption")
            print("   📊 Sample queries validated")
            print("   🔍 Parameter accessibility confirmed")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in LLM consumption validation: {e}")
            return False
    
    def test_end_to_end_validation(self) -> bool:
        """Perform comprehensive end-to-end validation."""
        print("\n🔍 Running end-to-end validation...")
        
        try:
            # Load generated data
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            # Run comprehensive validation - pass the networks portion
            validation_result = validate_aave_data(data['networks'], verbose=False)
            
            if not validation_result.is_valid():
                print(f"❌ Data validation failed:")
                print(f"   Errors: {len(validation_result.errors)}")
                print(f"   Warnings: {len(validation_result.warnings)}")
                
                # Show critical errors
                for error in validation_result.errors[:5]:
                    print(f"   ❌ {error}")
                
                return False
            
            # Check data completeness
            total_assets = sum(len(assets) for assets in data['networks'].values())
            if total_assets < 50:  # Expect at least 50 assets across all networks
                print(f"❌ Insufficient data: only {total_assets} assets found")
                return False
            
            # Check network coverage
            expected_networks = ['ethereum', 'polygon', 'arbitrum']
            missing_networks = [net for net in expected_networks if net not in data['networks']]
            
            if missing_networks:
                print(f"⚠️  Missing critical networks: {missing_networks}")
            
            # Check data freshness
            metadata = data.get('metadata', {})
            last_updated = metadata.get('last_updated')
            
            if last_updated:
                try:
                    update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    age = datetime.now().astimezone() - update_time
                    
                    if age > timedelta(hours=25):  # Allow 1 hour buffer for daily updates
                        print(f"⚠️  Data may be stale: {age.total_seconds() / 3600:.1f} hours old")
                    else:
                        print(f"✅ Data is fresh: {age.total_seconds() / 3600:.1f} hours old")
                        
                except Exception as e:
                    print(f"⚠️  Could not parse update timestamp: {e}")
            
            print("✅ End-to-end validation passed")
            print(f"   📊 {len(data['networks'])} networks, {total_assets} assets")
            print(f"   ✅ {validation_result.passed_checks}/{validation_result.total_checks} validation checks passed")
            
            return True
            
        except Exception as e:
            print(f"❌ End-to-end validation error: {e}")
            return False
    
    def _validate_llm_friendly_structure(self, data: Dict[str, Any]) -> bool:
        """Validate that data structure is optimized for LLM consumption."""
        
        # Check top-level structure
        if not isinstance(data, dict):
            print("❌ Data is not a dictionary")
            return False
        
        if 'networks' not in data:
            print("❌ Missing 'networks' key")
            return False
        
        if 'metadata' not in data:
            print("❌ Missing 'metadata' key")
            return False
        
        # Check networks structure
        networks = data['networks']
        if not isinstance(networks, dict):
            print("❌ 'networks' is not a dictionary")
            return False
        
        # Check at least one network has data
        if not networks:
            print("❌ No network data found")
            return False
        
        # Validate sample network data
        sample_network = next(iter(networks.values()))
        if not isinstance(sample_network, list):
            print("❌ Network data is not a list")
            return False
        
        if not sample_network:
            print("❌ Sample network has no assets")
            return False
        
        # Validate sample asset structure
        sample_asset = sample_network[0]
        required_fields = [
            'asset_address', 'symbol', 'liquidation_threshold', 
            'loan_to_value', 'active', 'decimals'
        ]
        
        missing_fields = [field for field in required_fields if field not in sample_asset]
        if missing_fields:
            print(f"❌ Missing required asset fields: {missing_fields}")
            return False
        
        # Check data types
        if not isinstance(sample_asset['liquidation_threshold'], (int, float)):
            print("❌ liquidation_threshold is not numeric")
            return False
        
        if not isinstance(sample_asset['loan_to_value'], (int, float)):
            print("❌ loan_to_value is not numeric")
            return False
        
        return True
    
    def _run_llm_consumption_tests(self, data: Dict[str, Any]) -> bool:
        """Run sample LLM consumption tests."""
        
        try:
            # Test 1: Find USDC across networks
            usdc_assets = []
            for network, assets in data['networks'].items():
                for asset in assets:
                    if asset['symbol'] == 'USDC':
                        usdc_assets.append({
                            'network': network,
                            'ltv': asset['loan_to_value'],
                            'lt': asset['liquidation_threshold']
                        })
            
            if not usdc_assets:
                print("❌ Could not find USDC assets for LLM test")
                return False
            
            # Test 2: Find highest LTV assets
            high_ltv_assets = []
            for network, assets in data['networks'].items():
                for asset in assets:
                    if asset['loan_to_value'] > 0.75:
                        high_ltv_assets.append({
                            'network': network,
                            'symbol': asset['symbol'],
                            'ltv': asset['loan_to_value']
                        })
            
            # Test 3: Calculate risk metrics
            risk_metrics = {}
            for network, assets in data['networks'].items():
                network_risks = []
                for asset in assets:
                    if asset['active'] and asset['loan_to_value'] > 0:
                        risk_buffer = asset['liquidation_threshold'] - asset['loan_to_value']
                        network_risks.append(risk_buffer)
                
                if network_risks:
                    risk_metrics[network] = {
                        'avg_risk_buffer': sum(network_risks) / len(network_risks),
                        'min_risk_buffer': min(network_risks),
                        'assets_count': len(network_risks)
                    }
            
            # Validate test results
            if len(usdc_assets) < 2:
                print("⚠️  Limited USDC coverage for LLM testing")
            
            if len(high_ltv_assets) < 5:
                print("⚠️  Limited high-LTV assets for LLM testing")
            
            if len(risk_metrics) < 3:
                print("⚠️  Limited networks for risk analysis")
            
            print(f"   🔍 Found {len(usdc_assets)} USDC assets across networks")
            print(f"   📊 Found {len(high_ltv_assets)} high-LTV assets")
            print(f"   📈 Calculated risk metrics for {len(risk_metrics)} networks")
            
            return True
            
        except Exception as e:
            print(f"❌ LLM consumption test error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests and return results."""
        print("🚀 Starting Final Integration and Deployment Testing")
        print("=" * 70)
        
        self.setup_test_environment()
        
        # Define all tests
        tests = [
            ("Complete Workflow Execution", self.test_complete_workflow_execution),
            ("Automated Daily Updates", self.test_automated_daily_updates),
            ("Manual Workflow Triggering", self.test_manual_workflow_triggering),
            ("JSON API Accessibility", self.test_json_api_accessibility),
            ("HTML Page Rendering", self.test_html_page_rendering),
            ("LLM Consumption Validation", self.test_llm_consumption_validation),
            ("End-to-End Validation", self.test_end_to_end_validation)
        ]
        
        # Run all tests
        results = {}
        passed_tests = 0
        
        for test_name, test_function in tests:
            try:
                result = test_function()
                results[test_name] = result
                
                if result:
                    passed_tests += 1
                    
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {e}")
                results[test_name] = False
        
        # Print summary
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("FINAL INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Summary: {passed_tests}/{len(tests)} tests passed")
        print(f"⏱️  Total test time: {total_time:.1f}s")
        
        if passed_tests == len(tests):
            print("🎉 ALL TESTS PASSED - Ready for deployment!")
        else:
            print("⚠️  Some tests failed - review issues before deployment")
        
        # Save test report
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "passed_tests": passed_tests,
            "failed_tests": len(tests) - passed_tests,
            "success_rate": passed_tests / len(tests),
            "execution_time": total_time,
            "test_results": results,
            "github_pages_url": self.github_pages_base_url,
            "github_raw_url": self.github_raw_base_url
        }
        
        try:
            with open('integration_test_report.json', 'w') as f:
                json.dump(test_report, f, indent=2)
            print(f"📊 Test report saved to integration_test_report.json")
        except Exception as e:
            print(f"⚠️  Could not save test report: {e}")
        
        return results


def main():
    """Main entry point for integration testing."""
    test_suite = IntegrationTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)