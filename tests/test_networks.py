"""
Tests for network configuration and validation functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import urllib.error

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from networks import (
    AAVE_V3_NETWORKS,
    validate_ethereum_address,
    validate_rpc_url,
    validate_network_config,
    validate_all_networks,
    get_active_networks,
    get_network_by_chain_id,
    test_rpc_connectivity,
    get_network_summary
)


class TestNetworkConfiguration(unittest.TestCase):
    """Test network configuration structure and content."""
    
    def test_network_count(self):
        """Test that we have the expected number of networks."""
        self.assertGreaterEqual(len(AAVE_V3_NETWORKS), 15, 
                               "Should have at least 15 networks configured")
    
    def test_required_networks_present(self):
        """Test that all major Aave V3 networks are present."""
        required_networks = [
            'ethereum', 'polygon', 'arbitrum', 'optimism', 'avalanche',
            'metis', 'base', 'gnosis', 'bnb', 'scroll'
        ]
        
        for network in required_networks:
            self.assertIn(network, AAVE_V3_NETWORKS, 
                         f"Network {network} should be configured")
    
    def test_network_structure(self):
        """Test that each network has required fields."""
        required_fields = ['name', 'chain_id', 'rpc', 'pool', 'pool_data_provider', 'active']
        
        for network_key, config in AAVE_V3_NETWORKS.items():
            for field in required_fields:
                self.assertIn(field, config, 
                             f"Network {network_key} missing field {field}")
    
    def test_unique_chain_ids(self):
        """Test that all chain IDs are unique."""
        chain_ids = [config['chain_id'] for config in AAVE_V3_NETWORKS.values()]
        self.assertEqual(len(chain_ids), len(set(chain_ids)), 
                        "All chain IDs should be unique")
    
    def test_ethereum_mainnet_config(self):
        """Test specific Ethereum mainnet configuration."""
        eth_config = AAVE_V3_NETWORKS['ethereum']
        self.assertEqual(eth_config['chain_id'], 1)
        self.assertEqual(eth_config['pool'], '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2')
        self.assertTrue(eth_config['active'])


class TestAddressValidation(unittest.TestCase):
    """Test Ethereum address validation."""
    
    def test_valid_addresses(self):
        """Test validation of valid Ethereum addresses."""
        valid_addresses = [
            '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
            '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            '0x0000000000000000000000000000000000000000'
        ]
        
        for address in valid_addresses:
            self.assertTrue(validate_ethereum_address(address), 
                           f"Address {address} should be valid")
    
    def test_invalid_addresses(self):
        """Test validation of invalid Ethereum addresses."""
        invalid_addresses = [
            '87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',  # Missing 0x
            '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E',   # Too short
            '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E22',  # Too long
            '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4G2',   # Invalid hex
            '',                                              # Empty
            None,                                            # None
            123                                              # Not string
        ]
        
        for address in invalid_addresses:
            self.assertFalse(validate_ethereum_address(address), 
                            f"Address {address} should be invalid")


class TestRpcUrlValidation(unittest.TestCase):
    """Test RPC URL validation."""
    
    def test_valid_urls(self):
        """Test validation of valid RPC URLs."""
        valid_urls = [
            'https://rpc.ankr.com/eth',
            'https://mainnet.infura.io/v3/abc123',
            'http://localhost:8545',
            'https://polygon-rpc.com/',
            'https://rpc.sonic.game'
        ]
        
        for url in valid_urls:
            self.assertTrue(validate_rpc_url(url), 
                           f"URL {url} should be valid")
    
    def test_invalid_urls(self):
        """Test validation of invalid RPC URLs."""
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',
            '',
            None,
            123
        ]
        
        for url in invalid_urls:
            self.assertFalse(validate_rpc_url(url), 
                            f"URL {url} should be invalid")


class TestNetworkValidation(unittest.TestCase):
    """Test network configuration validation."""
    
    def test_valid_network_config(self):
        """Test validation of valid network configuration."""
        valid_config = {
            'name': 'Test Network',
            'chain_id': 1,
            'rpc': 'https://rpc.test.com',
            'pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
            'pool_data_provider': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
            'active': True
        }
        
        is_valid, errors = validate_network_config('test', valid_config)
        self.assertTrue(is_valid, f"Config should be valid, errors: {errors}")
        self.assertEqual(len(errors), 0)
    
    def test_invalid_network_config(self):
        """Test validation of invalid network configuration."""
        invalid_config = {
            'name': 123,  # Should be string
            'chain_id': 'not-int',  # Should be int
            'rpc': 'invalid-url',  # Invalid URL
            'pool': 'invalid-address',  # Invalid address
            'active': 'not-bool'  # Should be bool
            # Missing pool_data_provider
        }
        
        is_valid, errors = validate_network_config('test', invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_all_networks(self):
        """Test validation of all configured networks."""
        is_valid, errors = validate_all_networks()
        
        if not is_valid:
            # Print errors for debugging
            for network, network_errors in errors.items():
                print(f"Network {network} errors: {network_errors}")
        
        self.assertTrue(is_valid, f"All networks should be valid, errors: {errors}")


class TestNetworkUtilities(unittest.TestCase):
    """Test network utility functions."""
    
    def test_get_active_networks(self):
        """Test getting active networks only."""
        active_networks = get_active_networks()
        
        for network_key, config in active_networks.items():
            self.assertTrue(config['active'], 
                           f"Network {network_key} should be active")
    
    def test_get_network_by_chain_id(self):
        """Test finding network by chain ID."""
        # Test Ethereum mainnet
        result = get_network_by_chain_id(1)
        self.assertIsNotNone(result)
        network_key, config = result
        self.assertEqual(network_key, 'ethereum')
        self.assertEqual(config['chain_id'], 1)
        
        # Test non-existent chain ID
        result = get_network_by_chain_id(99999)
        self.assertIsNone(result)
    
    def test_get_network_summary(self):
        """Test network summary statistics."""
        summary = get_network_summary()
        
        self.assertIn('total_networks', summary)
        self.assertIn('active_networks', summary)
        self.assertIn('inactive_networks', summary)
        
        self.assertGreaterEqual(summary['total_networks'], 15)
        self.assertEqual(
            summary['total_networks'],
            summary['active_networks'] + summary['inactive_networks']
        )


class TestRpcConnectivity(unittest.TestCase):
    """Test RPC connectivity testing functions."""
    
    @patch('networks.rpc_call')
    def test_rpc_connectivity_success(self, mock_rpc_call):
        """Test successful RPC connectivity test."""
        # Mock successful RPC response
        mock_rpc_call.return_value = {'result': '0x1'}  # Chain ID 1 in hex
        
        config = {
            'rpc': 'https://test-rpc.com',
            'chain_id': 1
        }
        
        is_accessible, message = test_rpc_connectivity('test', config)
        self.assertTrue(is_accessible)
        self.assertEqual(message, "RPC endpoint accessible")
    
    @patch('networks.rpc_call')
    def test_rpc_connectivity_chain_id_mismatch(self, mock_rpc_call):
        """Test RPC connectivity with chain ID mismatch."""
        # Mock RPC response with wrong chain ID
        mock_rpc_call.return_value = {'result': '0x89'}  # Chain ID 137 in hex
        
        config = {
            'rpc': 'https://test-rpc.com',
            'chain_id': 1  # Expecting chain ID 1
        }
        
        is_accessible, message = test_rpc_connectivity('test', config)
        self.assertFalse(is_accessible)
        self.assertIn("Chain ID mismatch", message)
    
    @patch('networks.rpc_call')
    def test_rpc_connectivity_failure(self, mock_rpc_call):
        """Test RPC connectivity failure."""
        # Mock RPC call exception
        mock_rpc_call.side_effect = Exception("Connection timeout")
        
        config = {
            'rpc': 'https://test-rpc.com',
            'chain_id': 1
        }
        
        is_accessible, message = test_rpc_connectivity('test', config)
        self.assertFalse(is_accessible)
        self.assertIn("Connection timeout", message)


class TestAutoUpdateFunctionality(unittest.TestCase):
    """Test auto-update functionality from aave-address-book."""
    
    @patch('networks.urllib.request.urlopen')
    def test_fetch_address_book_networks_success(self, mock_urlopen):
        """Test successful fetch from address book."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b'contract content here'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        from networks import fetch_address_book_networks
        result = fetch_address_book_networks()
        
        # Should return discovered networks (even if simplified)
        self.assertIsInstance(result, dict)
    
    @patch('networks.urllib.request.urlopen')
    def test_fetch_address_book_networks_failure(self, mock_urlopen):
        """Test fetch failure from address book."""
        # Mock HTTP error
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        from networks import fetch_address_book_networks
        result = fetch_address_book_networks()
        
        self.assertIsNone(result)
    
    def test_parse_address_book_content(self):
        """Test parsing of address book content."""
        from networks import parse_address_book_content
        
        # Test with sample content
        sample_content = "contract sample { address POOL = 0x123...; }"
        result = parse_address_book_content(sample_content)
        
        self.assertIsInstance(result, dict)
    
    @patch('networks.urllib.request.urlopen')
    def test_fetch_network_from_github_api(self, mock_urlopen):
        """Test fetching specific network from GitHub API."""
        # Mock GitHub API response
        mock_response = MagicMock()
        api_response = {
            'content': 'Y29udHJhY3QgY29udGVudA=='  # base64 encoded "contract content"
        }
        mock_response.read.return_value = json.dumps(api_response).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        from networks import fetch_network_from_github_api
        result = fetch_network_from_github_api('ethereum')
        
        # Should handle the request without error
        self.assertTrue(True)  # Test passes if no exception
    
    def test_update_networks_from_address_book(self):
        """Test updating networks from address book."""
        from networks import update_networks_from_address_book
        
        updated_networks, errors = update_networks_from_address_book()
        
        # Should return a dictionary and list
        self.assertIsInstance(updated_networks, dict)
        self.assertIsInstance(errors, list)
        
        # Should contain at least the original networks
        self.assertGreaterEqual(len(updated_networks), len(AAVE_V3_NETWORKS))
    
    def test_get_networks_with_fallback(self):
        """Test getting networks with fallback mechanism."""
        from networks import get_networks_with_fallback
        
        result = get_networks_with_fallback()
        
        # Should always return a valid networks dictionary
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
    
    def test_discover_new_networks(self):
        """Test discovering new networks."""
        from networks import discover_new_networks
        
        result = discover_new_networks()
        
        # Should return a list (may be empty)
        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()