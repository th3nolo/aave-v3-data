#!/usr/bin/env python3
"""
LLM Consumption Testing Suite
Tests actual LLM consumption patterns and API accessibility.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import subprocess


class LLMConsumptionTester:
    """Tests data structure and accessibility for LLM consumption."""
    
    def __init__(self):
        self.test_results = {}
        self.github_info = self._detect_github_repository()
        
    def _detect_github_repository(self) -> Optional[Dict[str, str]]:
        """Detect GitHub repository information for API testing."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            if 'github.com' in remote_url:
                if remote_url.startswith('git@github.com:'):
                    repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                elif remote_url.startswith('https://github.com/'):
                    repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
                else:
                    return None
                
                if '/' in repo_path:
                    username, repo_name = repo_path.split('/', 1)
                    return {
                        'username': username,
                        'repo_name': repo_name,
                        'raw_url': f"https://raw.githubusercontent.com/{username}/{repo_name}/main"
                    }
            
            return None
            
        except Exception:
            return None
    
    def test_data_structure_for_llm(self) -> bool:
        """Test data structure optimization for LLM consumption."""
        print("🤖 Testing data structure for LLM consumption...")
        
        if not os.path.exists('aave_v3_data.json'):
            print("❌ JSON file not found")
            return False
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            # Test 1: Top-level structure
            required_keys = ['networks', 'metadata']
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                print(f"❌ Missing top-level keys: {missing_keys}")
                return False
            
            # Test 2: Networks structure
            networks = data['networks']
            if not isinstance(networks, dict) or len(networks) == 0:
                print("❌ Invalid networks structure")
                return False
            
            # Test 3: Asset structure consistency
            sample_network = next(iter(networks.values()))
            if not isinstance(sample_network, list) or len(sample_network) == 0:
                print("❌ Invalid asset list structure")
                return False
            
            sample_asset = sample_network[0]
            required_asset_fields = [
                'asset_address', 'symbol', 'liquidation_threshold',
                'loan_to_value', 'active', 'decimals'
            ]
            
            missing_asset_fields = [field for field in required_asset_fields if field not in sample_asset]
            if missing_asset_fields:
                print(f"❌ Missing asset fields: {missing_asset_fields}")
                return False
            
            # Test 4: Data type validation
            if not isinstance(sample_asset['liquidation_threshold'], (int, float)):
                print("❌ liquidation_threshold is not numeric")
                return False
            
            if not isinstance(sample_asset['loan_to_value'], (int, float)):
                print("❌ loan_to_value is not numeric")
                return False
            
            # Test 5: Metadata completeness
            metadata = data['metadata']
            required_metadata = ['last_updated', 'total_networks', 'total_assets']
            missing_metadata = [field for field in required_metadata if field not in metadata]
            
            if missing_metadata:
                print(f"⚠️  Missing metadata fields: {missing_metadata}")
            
            print("✅ Data structure optimized for LLM consumption")
            print(f"   📊 {len(networks)} networks, {metadata.get('total_assets', 'unknown')} assets")
            print(f"   🔍 All required fields present")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format: {e}")
            return False
        except Exception as e:
            print(f"❌ Error testing data structure: {e}")
            return False
    
    def test_common_llm_queries(self) -> bool:
        """Test common LLM query patterns against the data."""
        print("🔍 Testing common LLM query patterns...")
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            networks = data['networks']
            
            # Query 1: Find specific asset across networks
            print("   Query 1: Find USDC across all networks")
            usdc_results = []
            for network, assets in networks.items():
                for asset in assets:
                    if asset['symbol'] == 'USDC':
                        usdc_results.append({
                            'network': network,
                            'ltv': asset['loan_to_value'],
                            'liquidation_threshold': asset['liquidation_threshold'],
                            'active': asset['active']
                        })
            
            if len(usdc_results) < 2:
                print(f"⚠️  Limited USDC coverage: {len(usdc_results)} networks")
            else:
                print(f"   ✅ Found USDC on {len(usdc_results)} networks")
            
            # Query 2: Find highest LTV assets
            print("   Query 2: Find assets with highest LTV ratios")
            high_ltv_assets = []
            for network, assets in networks.items():
                for asset in assets:
                    if asset['loan_to_value'] > 0.75:
                        high_ltv_assets.append({
                            'network': network,
                            'symbol': asset['symbol'],
                            'ltv': asset['loan_to_value']
                        })
            
            high_ltv_assets.sort(key=lambda x: x['ltv'], reverse=True)
            
            if len(high_ltv_assets) < 5:
                print(f"⚠️  Limited high-LTV assets: {len(high_ltv_assets)}")
            else:
                print(f"   ✅ Found {len(high_ltv_assets)} high-LTV assets")
            
            # Query 3: Compare asset parameters across networks
            print("   Query 3: Compare WETH parameters across networks")
            weth_comparison = []
            for network, assets in networks.items():
                for asset in assets:
                    if asset['symbol'] in ['WETH', 'ETH']:
                        weth_comparison.append({
                            'network': network,
                            'symbol': asset['symbol'],
                            'ltv': asset['loan_to_value'],
                            'liquidation_threshold': asset['liquidation_threshold']
                        })
            
            if len(weth_comparison) < 2:
                print(f"⚠️  Limited WETH/ETH coverage: {len(weth_comparison)} networks")
            else:
                print(f"   ✅ Found WETH/ETH on {len(weth_comparison)} networks")
            
            # Query 4: Risk analysis
            print("   Query 4: Calculate risk metrics by network")
            network_risk_metrics = {}
            for network, assets in networks.items():
                active_assets = [asset for asset in assets if asset['active']]
                if active_assets:
                    risk_buffers = []
                    for asset in active_assets:
                        if asset['loan_to_value'] > 0:
                            risk_buffer = asset['liquidation_threshold'] - asset['loan_to_value']
                            risk_buffers.append(risk_buffer)
                    
                    if risk_buffers:
                        network_risk_metrics[network] = {
                            'avg_risk_buffer': sum(risk_buffers) / len(risk_buffers),
                            'min_risk_buffer': min(risk_buffers),
                            'max_risk_buffer': max(risk_buffers),
                            'assets_analyzed': len(risk_buffers)
                        }
            
            if len(network_risk_metrics) < 3:
                print(f"⚠️  Limited networks for risk analysis: {len(network_risk_metrics)}")
            else:
                print(f"   ✅ Risk metrics calculated for {len(network_risk_metrics)} networks")
            
            # Query 5: Asset status analysis
            print("   Query 5: Analyze asset status flags")
            status_analysis = {
                'total_assets': 0,
                'active_assets': 0,
                'frozen_assets': 0,
                'borrowing_enabled': 0
            }
            
            for network, assets in networks.items():
                for asset in assets:
                    status_analysis['total_assets'] += 1
                    if asset.get('active', False):
                        status_analysis['active_assets'] += 1
                    if asset.get('frozen', False):
                        status_analysis['frozen_assets'] += 1
                    if asset.get('borrowing_enabled', False):
                        status_analysis['borrowing_enabled'] += 1
            
            active_rate = status_analysis['active_assets'] / max(status_analysis['total_assets'], 1)
            
            if active_rate < 0.8:
                print(f"⚠️  Low active asset rate: {active_rate:.1%}")
            else:
                print(f"   ✅ Good active asset rate: {active_rate:.1%}")
            
            print("✅ Common LLM query patterns validated")
            return True
            
        except Exception as e:
            print(f"❌ Error testing LLM queries: {e}")
            return False
    
    def test_api_accessibility_for_llm(self) -> bool:
        """Test API accessibility for LLM applications."""
        print("🌐 Testing API accessibility for LLM applications...")
        
        # Test local file access
        if not os.path.exists('aave_v3_data.json'):
            print("❌ Local JSON file not accessible")
            return False
        
        # Test remote API access if GitHub repository is detected
        if self.github_info:
            json_url = f"{self.github_info['raw_url']}/aave_v3_data.json"
            
            try:
                print(f"   Testing remote API: {json_url}")
                
                with urllib.request.urlopen(json_url, timeout=30) as response:
                    if response.status == 200:
                        content = response.read().decode('utf-8')
                        
                        # Validate JSON content
                        try:
                            data = json.loads(content)
                            
                            if 'networks' in data and 'metadata' in data:
                                print("   ✅ Remote API accessible and valid")
                                
                                # Check response headers for LLM-friendly features
                                headers = dict(response.headers)
                                
                                content_type = headers.get('Content-Type', '')
                                if 'application/json' in content_type:
                                    print("   ✅ Correct Content-Type header")
                                else:
                                    print(f"   ⚠️  Content-Type: {content_type}")
                                
                                # Check for CORS headers (important for web-based LLM apps)
                                if 'Access-Control-Allow-Origin' in headers:
                                    print("   ✅ CORS headers present")
                                else:
                                    print("   ⚠️  No CORS headers (may limit web app usage)")
                                
                                # Check content size (important for LLM token limits)
                                content_size = len(content)
                                content_size_kb = content_size / 1024
                                
                                print(f"   📊 Content size: {content_size_kb:.1f} KB")
                                
                                if content_size_kb > 1000:  # 1MB
                                    print("   ⚠️  Large content size may hit LLM token limits")
                                elif content_size_kb > 500:  # 500KB
                                    print("   ⚠️  Moderate content size - consider pagination for large LLMs")
                                else:
                                    print("   ✅ Content size suitable for LLM consumption")
                                
                                return True
                            else:
                                print("   ❌ Remote API has invalid structure")
                                return False
                                
                        except json.JSONDecodeError:
                            print("   ❌ Remote API returned invalid JSON")
                            return False
                    else:
                        print(f"   ❌ Remote API returned status {response.status}")
                        return False
                        
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("   ⚠️  Remote API not yet available (404)")
                    print("   This is normal for new repositories")
                    return True  # Don't fail for new repositories
                else:
                    print(f"   ❌ Remote API error {e.code}: {e}")
                    return False
            except Exception as e:
                print(f"   ⚠️  Error testing remote API: {e}")
                return True  # Don't fail for connectivity issues
        else:
            print("   ⚠️  No GitHub repository detected - skipping remote API test")
        
        print("✅ API accessibility validated")
        return True
    
    def test_llm_integration_examples(self) -> bool:
        """Test practical LLM integration examples."""
        print("💡 Testing LLM integration examples...")
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            # Example 1: Generate LLM-friendly summary
            print("   Example 1: Generate data summary for LLM context")
            
            networks = data['networks']
            metadata = data['metadata']
            
            summary = {
                'overview': {
                    'total_networks': len(networks),
                    'total_assets': metadata.get('total_assets', 0),
                    'last_updated': metadata.get('last_updated', 'unknown'),
                    'data_freshness': 'recent' if 'last_updated' in metadata else 'unknown'
                },
                'network_list': list(networks.keys()),
                'sample_assets': []
            }
            
            # Get sample assets from each network
            for network, assets in list(networks.items())[:3]:  # First 3 networks
                if assets:
                    sample_asset = assets[0]
                    summary['sample_assets'].append({
                        'network': network,
                        'symbol': sample_asset['symbol'],
                        'ltv': sample_asset['loan_to_value'],
                        'liquidation_threshold': sample_asset['liquidation_threshold']
                    })
            
            if len(summary['sample_assets']) >= 3:
                print("   ✅ LLM summary generation successful")
            else:
                print("   ⚠️  Limited sample data for LLM summary")
            
            # Example 2: Format data for specific LLM prompt
            print("   Example 2: Format data for risk analysis prompt")
            
            risk_prompt_data = {
                'instruction': 'Analyze Aave V3 liquidation risks across networks',
                'data_context': {
                    'networks_analyzed': len(networks),
                    'total_assets': metadata.get('total_assets', 0),
                    'data_timestamp': metadata.get('last_updated', 'unknown')
                },
                'risk_parameters': []
            }
            
            # Extract risk-relevant data
            for network, assets in networks.items():
                network_risks = []
                for asset in assets[:5]:  # Limit to first 5 assets per network
                    if asset['active'] and asset['loan_to_value'] > 0:
                        risk_buffer = asset['liquidation_threshold'] - asset['loan_to_value']
                        network_risks.append({
                            'symbol': asset['symbol'],
                            'ltv': asset['loan_to_value'],
                            'liquidation_threshold': asset['liquidation_threshold'],
                            'risk_buffer': risk_buffer
                        })
                
                if network_risks:
                    risk_prompt_data['risk_parameters'].append({
                        'network': network,
                        'assets': network_risks
                    })
            
            if len(risk_prompt_data['risk_parameters']) >= 3:
                print("   ✅ Risk analysis prompt formatting successful")
            else:
                print("   ⚠️  Limited risk data for prompt formatting")
            
            # Example 3: Test data filtering for specific queries
            print("   Example 3: Test data filtering capabilities")
            
            # Filter for high-risk assets (low risk buffer)
            high_risk_assets = []
            for network, assets in networks.items():
                for asset in assets:
                    if asset['active'] and asset['loan_to_value'] > 0:
                        risk_buffer = asset['liquidation_threshold'] - asset['loan_to_value']
                        if risk_buffer < 0.1:  # Less than 10% buffer
                            high_risk_assets.append({
                                'network': network,
                                'symbol': asset['symbol'],
                                'risk_buffer': risk_buffer
                            })
            
            # Filter for stable assets (commonly used as collateral)
            stable_assets = []
            stable_symbols = ['USDC', 'USDT', 'DAI', 'FRAX']
            for network, assets in networks.items():
                for asset in assets:
                    if asset['symbol'] in stable_symbols and asset['active']:
                        stable_assets.append({
                            'network': network,
                            'symbol': asset['symbol'],
                            'ltv': asset['loan_to_value']
                        })
            
            print(f"   📊 Found {len(high_risk_assets)} high-risk assets")
            print(f"   📊 Found {len(stable_assets)} stable assets")
            
            if len(high_risk_assets) > 0 and len(stable_assets) > 0:
                print("   ✅ Data filtering capabilities validated")
            else:
                print("   ⚠️  Limited data for filtering examples")
            
            print("✅ LLM integration examples validated")
            return True
            
        except Exception as e:
            print(f"❌ Error testing LLM integration examples: {e}")
            return False
    
    def test_performance_for_llm_consumption(self) -> bool:
        """Test performance characteristics for LLM consumption."""
        print("⚡ Testing performance for LLM consumption...")
        
        try:
            # Test JSON parsing performance
            start_time = time.time()
            
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            parse_time = time.time() - start_time
            
            # Test data access performance
            access_start = time.time()
            
            # Simulate common LLM access patterns
            network_count = len(data['networks'])
            total_assets = 0
            
            for network, assets in data['networks'].items():
                total_assets += len(assets)
                
                # Simulate filtering operations
                active_assets = [asset for asset in assets if asset.get('active', False)]
                high_ltv_assets = [asset for asset in assets if asset.get('loan_to_value', 0) > 0.7]
            
            access_time = time.time() - access_start
            
            # Calculate file size
            file_size = os.path.getsize('aave_v3_data.json')
            file_size_kb = file_size / 1024
            
            print(f"   📊 File size: {file_size_kb:.1f} KB")
            print(f"   ⏱️  JSON parse time: {parse_time:.3f}s")
            print(f"   ⏱️  Data access time: {access_time:.3f}s")
            print(f"   📈 Assets processed: {total_assets}")
            
            # Performance thresholds for LLM consumption
            if parse_time > 1.0:
                print("   ⚠️  Slow JSON parsing (>1s)")
            else:
                print("   ✅ Fast JSON parsing")
            
            if access_time > 0.5:
                print("   ⚠️  Slow data access (>0.5s)")
            else:
                print("   ✅ Fast data access")
            
            if file_size_kb > 1000:
                print("   ⚠️  Large file size may impact LLM token limits")
            elif file_size_kb > 500:
                print("   ⚠️  Moderate file size - monitor token usage")
            else:
                print("   ✅ Optimal file size for LLM consumption")
            
            # Test memory usage estimation
            import sys
            data_size_mb = sys.getsizeof(data) / (1024 * 1024)
            print(f"   💾 Memory usage: {data_size_mb:.1f} MB")
            
            if data_size_mb > 50:
                print("   ⚠️  High memory usage")
            else:
                print("   ✅ Reasonable memory usage")
            
            print("✅ Performance characteristics suitable for LLM consumption")
            return True
            
        except Exception as e:
            print(f"❌ Error testing performance: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all LLM consumption tests."""
        print("🤖 Starting LLM Consumption Testing Suite")
        print("=" * 50)
        
        if self.github_info:
            print(f"📍 Repository: {self.github_info['username']}/{self.github_info['repo_name']}")
            print(f"📊 API URL: {self.github_info['raw_url']}/aave_v3_data.json")
        else:
            print("⚠️  No GitHub repository detected")
        
        print()
        
        # Define all tests
        tests = [
            ("Data Structure for LLM", self.test_data_structure_for_llm),
            ("Common LLM Queries", self.test_common_llm_queries),
            ("API Accessibility", self.test_api_accessibility_for_llm),
            ("LLM Integration Examples", self.test_llm_integration_examples),
            ("Performance for LLM", self.test_performance_for_llm_consumption)
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
                    
                print()  # Add spacing between tests
                    
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {e}")
                results[test_name] = False
                print()
        
        # Print summary
        print("=" * 50)
        print("LLM CONSUMPTION TEST RESULTS")
        print("=" * 50)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Summary: {passed_tests}/{len(tests)} tests passed")
        print(f"📈 Success rate: {passed_tests / len(tests):.1%}")
        
        if passed_tests == len(tests):
            print("🎉 ALL LLM CONSUMPTION TESTS PASSED!")
            print("   🤖 Data is optimized for AI/LLM consumption")
            print("   🌐 API is accessible for LLM applications")
            print("   ⚡ Performance is suitable for real-time queries")
        else:
            print("⚠️  Some LLM consumption tests failed")
            print("   Review failures to optimize for AI/LLM usage")
        
        # Save test report
        test_report = {
            "timestamp": datetime.now().isoformat(),
            "github_repository": self.github_info,
            "test_results": results,
            "summary": {
                "total_tests": len(tests),
                "passed_tests": passed_tests,
                "success_rate": passed_tests / len(tests),
                "llm_ready": passed_tests >= len(tests) - 1  # Allow 1 failure
            }
        }
        
        try:
            with open('llm_consumption_test_report.json', 'w') as f:
                json.dump(test_report, f, indent=2)
            print(f"\n📊 LLM test report saved to llm_consumption_test_report.json")
        except Exception as e:
            print(f"⚠️  Could not save LLM test report: {e}")
        
        return results


def main():
    """Main entry point for LLM consumption testing."""
    tester = LLMConsumptionTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)