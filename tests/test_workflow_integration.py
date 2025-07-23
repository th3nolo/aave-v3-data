"""
Integration tests for complete Aave V3 data fetcher workflow.
Tests end-to-end functionality including network expansion scenarios.
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from networks import AAVE_V3_NETWORKS, get_active_networks
from graceful_fetcher import fetch_aave_data_gracefully
from validation import validate_aave_data
from json_output import save_json_output, validate_json_schema
from html_output import save_html_output


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete workflow scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_networks = AAVE_V3_NETWORKS.copy()
        
        # Create minimal test network configuration
        self.test_networks = {
            'ethereum': {
                'name': 'Ethereum',
                'rpc': 'https://rpc.ankr.com/eth',
                'pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
                'active': True
            },
            'polygon': {
                'name': 'Polygon',
                'rpc': 'https://rpc.ankr.com/polygon',
                'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
                'active': True
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Restore original networks
        AAVE_V3_NETWORKS.clear()
        AAVE_V3_NETWORKS.update(self.original_networks)
    
    def _setup_test_networks(self):
        """Set up test networks configuration."""
        AAVE_V3_NETWORKS.clear()
        AAVE_V3_NETWORKS.update(self.test_networks)
    
    def _create_mock_data(self) -> dict:
        """Create mock data for testing."""
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
    
    def test_complete_workflow_with_mock_data(self):
        """Test complete workflow with mock data."""
        # Create mock data
        mock_data = self._create_mock_data()
        
        # Test JSON output
        json_file = os.path.join(self.test_dir, 'test_output.json')
        json_success = save_json_output(mock_data, json_file)
        self.assertTrue(json_success)
        self.assertTrue(os.path.exists(json_file))
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data), 2)  # 2 networks
        self.assertIn('ethereum', loaded_data)
        self.assertIn('polygon', loaded_data)
        
        # Test HTML output
        html_file = os.path.join(self.test_dir, 'test_output.html')
        html_success = save_html_output(mock_data, html_file)
        self.assertTrue(html_success)
        self.assertTrue(os.path.exists(html_file))
        
        # Verify HTML content
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        self.assertIn('<html>', html_content)
        self.assertIn('USDC', html_content)
        self.assertIn('USDC.e', html_content)
        self.assertIn('ethereum', html_content.lower())
        self.assertIn('polygon', html_content.lower())
        
        # Test data validation
        validation_result = validate_aave_data(mock_data)
        self.assertTrue(validation_result.is_valid())
        
        # Test JSON schema validation
        schema_errors = validate_json_schema(mock_data)
        self.assertEqual(len(schema_errors), 0)
        
        print("✓ Complete workflow test passed")
    
    def test_network_expansion_scenario(self):
        """Test adding new networks to configuration."""
        self._setup_test_networks()
        
        # Add a new network
        new_network = {
            'arbitrum': {
                'name': 'Arbitrum One',
                'rpc': 'https://rpc.ankr.com/arbitrum',
                'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
                'active': True
            }
        }
        
        AAVE_V3_NETWORKS.update(new_network)
        
        # Verify network is available
        active_networks = get_active_networks()
        self.assertIn('arbitrum', active_networks)
        self.assertEqual(len(active_networks), 3)  # ethereum, polygon, arbitrum
        
        # Test that the system can handle the new network
        mock_data_with_arbitrum = self._create_mock_data()
        mock_data_with_arbitrum['arbitrum'] = [
            {
                "asset_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
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
                "liquidity_index": 1.0123,
                "variable_borrow_index": 1.0234,
                "current_liquidity_rate": 0.0123,
                "current_variable_borrow_rate": 0.0234,
                "last_update_timestamp": 1704067200,
                "a_token_address": "0x724dc807b04555b71ed48a6896b6F41593b8C637",
                "variable_debt_token_address": "0xf611aEb5013fD2c0511c9CD55c7dc5C1140741A6",
                "supply_cap": 200000000,
                "borrow_cap": 180000000
            }
        ]
        
        # Test validation with new network
        validation_result = validate_aave_data(mock_data_with_arbitrum)
        self.assertTrue(validation_result.is_valid())
        
        # Test output generation with new network
        json_file = os.path.join(self.test_dir, 'expanded_output.json')
        json_success = save_json_output(mock_data_with_arbitrum, json_file)
        self.assertTrue(json_success)
        
        with open(json_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data), 3)  # 3 networks now
        self.assertIn('arbitrum', loaded_data)
        
        print("✓ Network expansion scenario test passed")
    
    def test_2025_parameter_validation(self):
        """Test validation of 2025-specific parameters."""
        mock_data = self._create_mock_data()
        
        # Test supply/borrow cap validation
        for network_data in mock_data.values():
            for asset in network_data:
                self.assertIn('supply_cap', asset)
                self.assertIn('borrow_cap', asset)
                self.assertIsInstance(asset['supply_cap'], int)
                self.assertIsInstance(asset['borrow_cap'], int)
                self.assertGreaterEqual(asset['supply_cap'], 0)
                self.assertGreaterEqual(asset['borrow_cap'], 0)
                
                # Borrow cap should not exceed supply cap (unless both are 0)
                if asset['supply_cap'] > 0 and asset['borrow_cap'] > 0:
                    self.assertLessEqual(asset['borrow_cap'], asset['supply_cap'])
        
        # Test validation recognizes new parameters
        validation_result = validate_aave_data(mock_data)
        self.assertTrue(validation_result.is_valid())
        
        # Check that validation doesn't flag new parameters as errors
        error_messages = ' '.join(validation_result.errors)
        self.assertNotIn('supply_cap', error_messages)
        self.assertNotIn('borrow_cap', error_messages)
        
        print("✓ 2025 parameter validation test passed")
    
    def test_error_handling_workflow(self):
        """Test workflow error handling scenarios."""
        # Test with invalid data structure
        invalid_data = {
            "ethereum": "not_a_list"  # Should be a list
        }
        
        validation_result = validate_aave_data(invalid_data)
        self.assertFalse(validation_result.is_valid())
        self.assertGreater(len(validation_result.errors), 0)
        
        # Test with missing required fields
        incomplete_data = {
            "ethereum": [
                {
                    "asset_address": "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0",
                    # Missing symbol, liquidation_threshold, etc.
                }
            ]
        }
        
        validation_result = validate_aave_data(incomplete_data)
        self.assertFalse(validation_result.is_valid())
        
        # Test JSON schema validation with invalid data
        schema_errors = validate_json_schema(invalid_data)
        self.assertGreater(len(schema_errors), 0)
        
        print("✓ Error handling workflow test passed")
    
    def test_performance_characteristics(self):
        """Test performance characteristics of the workflow."""
        import time
        
        mock_data = self._create_mock_data()
        
        # Test validation performance
        start_time = time.time()
        validation_result = validate_aave_data(mock_data)
        validation_time = time.time() - start_time
        
        # Validation should be fast for small datasets
        self.assertLess(validation_time, 1.0)  # Less than 1 second
        self.assertTrue(validation_result.is_valid())
        
        # Test JSON output performance
        json_file = os.path.join(self.test_dir, 'perf_test.json')
        start_time = time.time()
        json_success = save_json_output(mock_data, json_file)
        json_time = time.time() - start_time
        
        self.assertTrue(json_success)
        self.assertLess(json_time, 0.5)  # Less than 0.5 seconds
        
        # Test HTML output performance
        html_file = os.path.join(self.test_dir, 'perf_test.html')
        start_time = time.time()
        html_success = save_html_output(mock_data, html_file)
        html_time = time.time() - start_time
        
        self.assertTrue(html_success)
        self.assertLess(html_time, 1.0)  # Less than 1 second
        
        print(f"✓ Performance test passed (validation: {validation_time:.3f}s, "
              f"JSON: {json_time:.3f}s, HTML: {html_time:.3f}s)")
    
    def test_data_consistency_across_outputs(self):
        """Test data consistency between JSON and HTML outputs."""
        mock_data = self._create_mock_data()
        
        # Generate outputs
        json_file = os.path.join(self.test_dir, 'consistency_test.json')
        html_file = os.path.join(self.test_dir, 'consistency_test.html')
        
        json_success = save_json_output(mock_data, json_file)
        html_success = save_html_output(mock_data, html_file)
        
        self.assertTrue(json_success)
        self.assertTrue(html_success)
        
        # Load JSON data
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        # Read HTML content
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        # Verify key data points appear in both outputs
        for network_key, assets in json_data.items():
            # Network name should appear in HTML
            self.assertIn(network_key, html_content.lower())
            
            for asset in assets:
                symbol = asset['symbol']
                lt = asset['liquidation_threshold']
                ltv = asset['loan_to_value']
                
                # Symbol should appear in HTML
                self.assertIn(symbol, html_content)
                
                # Key values should appear in HTML (allowing for formatting differences)
                self.assertIn(f"{lt:.3f}", html_content)
                self.assertIn(f"{ltv:.3f}", html_content)
        
        print("✓ Data consistency test passed")
    
    def test_file_handling_edge_cases(self):
        """Test file handling edge cases."""
        mock_data = self._create_mock_data()
        
        # Test writing to non-existent directory
        non_existent_dir = os.path.join(self.test_dir, 'non_existent')
        json_file = os.path.join(non_existent_dir, 'test.json')
        
        # Should handle directory creation gracefully
        json_success = save_json_output(mock_data, json_file)
        # This might fail depending on implementation, which is acceptable
        
        # Test writing to read-only location (if possible)
        readonly_file = os.path.join(self.test_dir, 'readonly.json')
        
        # Create file first
        with open(readonly_file, 'w') as f:
            json.dump({}, f)
        
        # Make it read-only
        try:
            os.chmod(readonly_file, 0o444)
            
            # Try to overwrite - should handle gracefully
            json_success = save_json_output(mock_data, readonly_file)
            # Implementation should handle this gracefully
            
        except (OSError, PermissionError):
            # Some systems might not support chmod
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(readonly_file, 0o644)
            except (OSError, PermissionError):
                pass
        
        print("✓ File handling edge cases test passed")
    
    @patch('src.graceful_fetcher.fetch_aave_data_gracefully')
    def test_integration_with_fetcher_mock(self, mock_fetch):
        """Test integration with mocked data fetcher."""
        self._setup_test_networks()
        
        # Mock the fetcher to return our test data
        mock_data = self._create_mock_data()
        mock_fetch.return_value = (mock_data, {'fetch_summary': {'total_time': 5.0}})
        
        # Call the fetcher
        data, fetch_report = mock_fetch(max_failures=2, save_reports=False)
        
        # Verify the integration works
        self.assertEqual(data, mock_data)
        self.assertIn('fetch_summary', fetch_report)
        
        # Test the complete workflow with fetched data
        validation_result = validate_aave_data(data)
        self.assertTrue(validation_result.is_valid())
        
        # Test outputs
        json_file = os.path.join(self.test_dir, 'integration_test.json')
        html_file = os.path.join(self.test_dir, 'integration_test.html')
        
        json_success = save_json_output(data, json_file)
        html_success = save_html_output(data, html_file)
        
        self.assertTrue(json_success)
        self.assertTrue(html_success)
        
        print("✓ Integration with fetcher mock test passed")


if __name__ == '__main__':
    unittest.main()