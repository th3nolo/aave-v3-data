"""
Integration test for network error handling with actual network configurations.
Tests the integration between network configuration and error handling.
"""

import unittest
import sys
import os
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from networks import (
    get_fallback_urls,
    test_rpc_connectivity,
    AAVE_V3_NETWORKS
)
from utils import rpc_call_with_retry, RPCError, NetworkError


class TestNetworkIntegration(unittest.TestCase):
    """Test integration between network configuration and error handling."""
    
    def test_fallback_url_extraction(self):
        """Test extraction of fallback URLs from network configuration."""
        # Test with list of fallback URLs
        config_with_list = {
            'rpc': 'https://primary.com',
            'rpc_fallback': ['https://fallback1.com', 'https://fallback2.com']
        }
        fallbacks = get_fallback_urls(config_with_list)
        self.assertEqual(fallbacks, ['https://fallback1.com', 'https://fallback2.com'])
        
        # Test with single fallback URL
        config_with_string = {
            'rpc': 'https://primary.com',
            'rpc_fallback': 'https://fallback.com'
        }
        fallbacks = get_fallback_urls(config_with_string)
        self.assertEqual(fallbacks, ['https://fallback.com'])
        
        # Test with no fallback URLs
        config_no_fallback = {
            'rpc': 'https://primary.com'
        }
        fallbacks = get_fallback_urls(config_no_fallback)
        self.assertIsNone(fallbacks)
    
    def test_network_config_has_fallbacks(self):
        """Test that critical networks have fallback URLs configured."""
        critical_networks = ['ethereum', 'polygon', 'arbitrum']
        
        for network_key in critical_networks:
            if network_key in AAVE_V3_NETWORKS:
                config = AAVE_V3_NETWORKS[network_key]
                fallbacks = get_fallback_urls(config)
                
                # Critical networks should have fallback URLs
                self.assertIsNotNone(fallbacks, f"Network {network_key} should have fallback URLs")
                self.assertGreater(len(fallbacks), 0, f"Network {network_key} should have at least one fallback URL")
    
    def test_rpc_connectivity_with_fallbacks(self):
        """Test RPC connectivity testing with fallback logic."""
        test_config = {
            'name': 'Test Network',
            'chain_id': 1,
            'rpc': 'https://invalid-primary.example.com',
            'rpc_fallback': ['https://invalid-fallback.example.com'],
            'pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
            'pool_data_provider': '0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3',
            'active': True
        }
        
        # This should fail gracefully and return False with error message
        is_accessible, error_message = test_rpc_connectivity('test', test_config)
        
        self.assertFalse(is_accessible)
        self.assertIn("RPC connection failed", error_message)
    
    def test_network_config_validation(self):
        """Test that network configurations are valid."""
        from networks import validate_network_config
        
        for network_key, config in AAVE_V3_NETWORKS.items():
            with self.subTest(network=network_key):
                is_valid, errors = validate_network_config(network_key, config)
                
                if not is_valid:
                    self.fail(f"Network {network_key} has invalid configuration: {errors}")
    
    def test_error_handling_integration(self):
        """Test integration of error handling with network functions."""
        # Test with mock network that will fail
        with patch('utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = NetworkError("Network unreachable")
            
            # Test that functions handle errors gracefully
            from utils import get_reserves, get_asset_symbol
            
            # get_reserves should propagate the error
            with self.assertRaises(Exception) as context:
                get_reserves(
                    "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
                    "https://invalid.com",
                    ["https://invalid-fallback.com"]
                )
            self.assertIn("Failed to get reserves", str(context.exception))
            
            # get_asset_symbol should handle errors gracefully
            result = get_asset_symbol(
                "0x1234567890123456789012345678901234567890",
                "https://invalid.com",
                ["https://invalid-fallback.com"]
            )
            self.assertTrue(result.startswith("TOKEN_"))


class TestErrorHandlingConfiguration(unittest.TestCase):
    """Test error handling configuration and behavior."""
    
    def test_retry_parameters(self):
        """Test that retry parameters are reasonable."""
        # Test with mock that counts calls
        call_count = 0
        
        def mock_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise NetworkError("Persistent network error")
        
        with patch('utils._make_single_rpc_call', side_effect=mock_side_effect):
            with patch('time.sleep'):  # Speed up test
                with self.assertRaises((RPCError, NetworkError)):
                    rpc_call_with_retry(
                        "https://test.com",
                        "eth_call",
                        [],
                        max_retries=3,
                        fallback_urls=["https://fallback.com"]
                    )
        
        # Should try primary 3 times + fallback 3 times = 6 total calls
        self.assertEqual(call_count, 6)
    
    def test_error_classification_coverage(self):
        """Test that error classification covers common scenarios."""
        from utils import _make_single_rpc_call
        import urllib.error
        
        # Test different HTTP error codes
        error_scenarios = [
            (429, "rate_limit"),
            (500, "server_error"),
            (502, "server_error"),
            (503, "server_error"),
            (400, "client_error"),
            (404, "client_error"),
        ]
        
        for status_code, expected_type in error_scenarios:
            with self.subTest(status_code=status_code):
                with patch('urllib.request.urlopen') as mock_urlopen:
                    error = urllib.error.HTTPError(
                        url="https://test.com",
                        code=status_code,
                        msg="Test error",
                        hdrs={},
                        fp=None
                    )
                    mock_urlopen.side_effect = error
                    
                    with self.assertRaises(RPCError) as context:
                        _make_single_rpc_call("https://test.com", "eth_call", [])
                    
                    self.assertEqual(context.exception.error_type, expected_type)


if __name__ == '__main__':
    unittest.main(verbosity=2)