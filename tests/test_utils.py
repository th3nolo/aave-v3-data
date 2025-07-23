"""
Unit tests for core utility functions.
Tests method ID generation, RPC calls, and address parsing.
"""

import unittest
import json
from unittest.mock import patch, Mock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    get_method_id,
    rpc_call,
    parse_address,
    encode_call_data,
    decode_hex_to_int,
    format_address
)


class TestUtils(unittest.TestCase):
    
    def test_get_method_id(self):
        """Test method ID generation from function signatures."""
        # Test known method signatures
        reserves_list_id = get_method_id("getReservesList()")
        self.assertTrue(reserves_list_id.startswith('0x'))
        self.assertEqual(len(reserves_list_id), 10)  # 0x + 8 hex chars
        
        # Test another signature
        reserve_data_id = get_method_id("getReserveData(address)")
        self.assertTrue(reserve_data_id.startswith('0x'))
        self.assertEqual(len(reserve_data_id), 10)
        
        # Different signatures should produce different IDs
        self.assertNotEqual(reserves_list_id, reserve_data_id)
    
    def test_parse_address(self):
        """Test address parsing from hex strings."""
        # Test with 0x prefix and padding (64 char response from contract)
        hex_with_prefix = "0x000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        expected = "0xa0b86a33e6441e8e421b27d6c5a9c7157bf77fb0"
        result = parse_address(hex_with_prefix)
        self.assertEqual(result.lower(), expected.lower())
        
        # Test without 0x prefix
        hex_without_prefix = "000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        result = parse_address(hex_without_prefix)
        self.assertEqual(result.lower(), expected.lower())
        
        # Test with exact 40 character address
        exact_hex = "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        result = parse_address(exact_hex)
        self.assertEqual(len(result), 42)  # 0x + 40 chars
        self.assertEqual(result.lower(), expected.lower())
        
        # Test with invalid hex string
        with self.assertRaises(ValueError):
            parse_address("0x123")  # Too short
    
    def test_encode_call_data(self):
        """Test call data encoding."""
        method_id = "0x12345678"
        result = encode_call_data(method_id)
        self.assertEqual(result, method_id)
        
        # Test with empty parameters
        result = encode_call_data(method_id, [])
        self.assertEqual(result, method_id)
    
    def test_decode_hex_to_int(self):
        """Test hex string to integer conversion."""
        # Test with 0x prefix
        self.assertEqual(decode_hex_to_int("0x10"), 16)
        self.assertEqual(decode_hex_to_int("0xff"), 255)
        
        # Test without 0x prefix
        self.assertEqual(decode_hex_to_int("10"), 16)
        self.assertEqual(decode_hex_to_int("ff"), 255)
        
        # Test empty string
        self.assertEqual(decode_hex_to_int("0x"), 0)
        self.assertEqual(decode_hex_to_int(""), 0)
    
    def test_format_address(self):
        """Test address formatting."""
        # Test with 0x prefix
        address = "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB"
        result = format_address(address)
        self.assertEqual(len(result), 42)
        self.assertTrue(result.startswith('0x'))
        
        # Test without 0x prefix
        address_no_prefix = "A0b86a33E6441E8e421B27D6c5a9c7157bF77FB"
        result = format_address(address_no_prefix)
        self.assertEqual(len(result), 42)
        self.assertTrue(result.startswith('0x'))
        
        # Test short address (should be padded)
        short_address = "0x123"
        result = format_address(short_address)
        self.assertEqual(len(result), 42)
        self.assertTrue(result.startswith('0x'))
        self.assertTrue(result.endswith('123'))
    
    @patch('urllib.request.urlopen')
    def test_rpc_call_success(self, mock_urlopen):
        """Test successful RPC call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }).encode('utf-8')
        
        # Create context manager mock
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_response)
        mock_context.__exit__ = Mock(return_value=None)
        mock_urlopen.return_value = mock_context
        
        result = rpc_call("http://test.com", "eth_call", [])
        
        self.assertEqual(result["result"], "0x123456")
        self.assertEqual(result["jsonrpc"], "2.0")
    
    @patch('urllib.request.urlopen')
    def test_rpc_call_error(self, mock_urlopen):
        """Test RPC call with error response."""
        # Mock error response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32000, "message": "Test error"}
        }).encode('utf-8')
        
        # Create context manager mock
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_response)
        mock_context.__exit__ = Mock(return_value=None)
        mock_urlopen.return_value = mock_context
        
        with self.assertRaises(Exception) as context:
            rpc_call("http://test.com", "eth_call", [])
        
        self.assertIn("RPC Error", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_rpc_call_network_error(self, mock_urlopen):
        """Test RPC call with network error."""
        mock_urlopen.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception) as context:
            rpc_call("http://test.com", "eth_call", [])
        
        self.assertIn("Network error", str(context.exception))


if __name__ == '__main__':
    unittest.main()