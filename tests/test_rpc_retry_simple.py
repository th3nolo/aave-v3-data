"""
Simple test for RPC retry functionality.
Tests the core error handling and retry logic.
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock
import urllib.error
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    rpc_call_with_retry, 
    RPCError, 
    NetworkError,
    get_reserves,
    get_asset_symbol
)


class TestRPCRetryBasic(unittest.TestCase):
    """Test basic RPC retry functionality."""
    
    def test_successful_call(self):
        """Test successful RPC call."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response_obj = MagicMock()
            mock_response_obj.status = 200
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_urlopen.return_value.__enter__.return_value = mock_response_obj
            
            result = rpc_call_with_retry("https://test.com", "eth_call", [])
            
            self.assertEqual(result, mock_response)
    
    def test_network_error_retry(self):
        """Test retry on network error."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # First call fails, second succeeds
            mock_success = MagicMock()
            mock_success.status = 200
            mock_success.read.return_value = json.dumps(mock_response).encode('utf-8')
            
            mock_urlopen.side_effect = [
                urllib.error.URLError("Network error"),
                MagicMock(__enter__=MagicMock(return_value=mock_success))
            ]
            
            with patch('time.sleep'):  # Speed up test
                result = rpc_call_with_retry("https://test.com", "eth_call", [])
            
            self.assertEqual(result, mock_response)
            self.assertEqual(mock_urlopen.call_count, 2)
    
    def test_fallback_endpoint(self):
        """Test fallback endpoint usage."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # Primary fails, fallback succeeds
            mock_success = MagicMock()
            mock_success.status = 200
            mock_success.read.return_value = json.dumps(mock_response).encode('utf-8')
            
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 3:  # First 3 calls to primary fail
                    raise urllib.error.URLError("Primary down")
                else:  # Fallback succeeds
                    return MagicMock(__enter__=MagicMock(return_value=mock_success))
            
            mock_urlopen.side_effect = side_effect
            
            with patch('time.sleep'):  # Speed up test
                result = rpc_call_with_retry(
                    "https://primary.com", 
                    "eth_call", 
                    [],
                    fallback_urls=["https://fallback.com"]
                )
            
            self.assertEqual(result, mock_response)
            self.assertEqual(call_count, 4)  # 3 primary + 1 fallback
    
    def test_all_endpoints_fail(self):
        """Test behavior when all endpoints fail."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("All down")
            
            with patch('time.sleep'):  # Speed up test
                with self.assertRaises((RPCError, NetworkError)):
                    rpc_call_with_retry(
                        "https://primary.com", 
                        "eth_call", 
                        [],
                        fallback_urls=["https://fallback.com"]
                    )
    
    def test_rpc_error_types(self):
        """Test RPC error classification."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            # Test rate limiting
            rate_limit_error = urllib.error.HTTPError(
                url="https://test.com",
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "2"},
                fp=None
            )
            mock_urlopen.side_effect = rate_limit_error
            
            with self.assertRaises(RPCError) as context:
                rpc_call_with_retry("https://test.com", "eth_call", [])
            
            self.assertEqual(context.exception.error_type, "rate_limit")
    
    def test_graceful_symbol_failure(self):
        """Test graceful failure in get_asset_symbol."""
        with patch('utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = NetworkError("Network down")
            
            # Should return fallback symbol instead of raising exception
            result = get_asset_symbol("0x1234567890123456789012345678901234567890", "https://test.com")
            
            self.assertTrue(result.startswith("TOKEN_"))
            self.assertIn("34567890", result)  # Last 8 chars of address


class TestErrorClassificationSimple(unittest.TestCase):
    """Test error classification."""
    
    def test_rpc_error_attributes(self):
        """Test RPCError attributes."""
        error = RPCError("Test error", error_type="rate_limit", retry_after=30)
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.error_type, "rate_limit")
        self.assertEqual(error.retry_after, 30)
    
    def test_network_error_attributes(self):
        """Test NetworkError attributes."""
        error = NetworkError("Network down")
        
        self.assertEqual(str(error), "Network down")
        self.assertEqual(error.error_type, "network")


if __name__ == '__main__':
    unittest.main(verbosity=2)