"""
Test suite for RPC error handling and resilience functionality.
Tests retry logic, fallback endpoints, and error classification.
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, Mock, MagicMock
import urllib.error
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    rpc_call_with_retry, 
    _make_single_rpc_call,
    RPCError, 
    NetworkError,
    get_reserves,
    get_asset_symbol,
    get_reserve_data
)


class TestRPCErrorHandling(unittest.TestCase):
    """Test RPC error handling and retry logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_url = "https://test-rpc.example.com"
        self.fallback_urls = ["https://fallback1.example.com", "https://fallback2.example.com"]
        self.test_method = "eth_call"
        self.test_params = [{"to": "0x123", "data": "0xabc"}, "latest"]
    
    def test_successful_call_first_attempt(self):
        """Test successful RPC call on first attempt."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response_obj = MagicMock()
            mock_response_obj.status = 200
            mock_response_obj.read.return_value = json.dumps(mock_response).encode('utf-8')
            mock_response_obj.__enter__.return_value = mock_response_obj
            mock_response_obj.__exit__.return_value = None
            mock_urlopen.return_value = mock_response_obj
            
            result = rpc_call_with_retry(self.test_url, self.test_method, self.test_params)
            
            self.assertEqual(result, mock_response)
            self.assertEqual(mock_urlopen.call_count, 1)
    
    def test_retry_on_network_error(self):
        """Test retry logic on network errors."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # First two calls fail with network error, third succeeds
            success_mock = MagicMock()
            success_mock.status = 200
            success_mock.read.return_value = json.dumps(mock_response).encode('utf-8')
            success_mock.__enter__.return_value = success_mock
            success_mock.__exit__.return_value = None
            
            mock_urlopen.side_effect = [
                urllib.error.URLError("Connection timeout"),
                urllib.error.URLError("Connection refused"),
                success_mock
            ]
            
            with patch('time.sleep'):  # Speed up test by mocking sleep
                result = rpc_call_with_retry(self.test_url, self.test_method, self.test_params)
            
            self.assertEqual(result, mock_response)
            self.assertEqual(mock_urlopen.call_count, 3)
    
    def test_fallback_endpoint_usage(self):
        """Test fallback endpoint usage when primary fails."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # Primary endpoint fails all retries, fallback succeeds
            def side_effect(*args, **kwargs):
                request = args[0]
                if self.test_url in request.full_url:
                    raise urllib.error.URLError("Primary endpoint down")
                else:
                    # Fallback endpoint succeeds
                    mock_resp = MagicMock()
                    mock_resp.status = 200
                    mock_resp.read.return_value = json.dumps(mock_response).encode('utf-8')
                    mock_resp.__enter__.return_value = mock_resp
                    mock_resp.__exit__.return_value = None
                    return mock_resp
            
            mock_urlopen.side_effect = side_effect
            
            with patch('time.sleep'):  # Speed up test
                result = rpc_call_with_retry(
                    self.test_url, 
                    self.test_method, 
                    self.test_params,
                    fallback_urls=self.fallback_urls
                )
            
            self.assertEqual(result, mock_response)
            # Should try primary 3 times, then fallback once
            self.assertEqual(mock_urlopen.call_count, 4)
    
    def test_rate_limiting_handling(self):
        """Test rate limiting error handling with retry-after."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # First call gets rate limited, second succeeds
            rate_limit_error = urllib.error.HTTPError(
                url=self.test_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "2"},
                fp=None
            )
            
            success_response = Mock()
            success_response.status = 200
            success_response.read.return_value = json.dumps(mock_response).encode('utf-8')
            success_response.__enter__.return_value = success_response
            
            mock_urlopen.side_effect = [rate_limit_error, success_response]
            
            with patch('time.sleep') as mock_sleep:
                result = rpc_call_with_retry(self.test_url, self.test_method, self.test_params)
            
            self.assertEqual(result, mock_response)
            mock_sleep.assert_called_once()  # Should sleep due to rate limiting
    
    def test_server_error_retry(self):
        """Test server error retry with exponential backoff."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x123456"
        }
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # First call gets server error, second succeeds
            server_error = urllib.error.HTTPError(
                url=self.test_url,
                code=500,
                msg="Internal Server Error",
                hdrs={},
                fp=None
            )
            
            success_response = Mock()
            success_response.status = 200
            success_response.read.return_value = json.dumps(mock_response).encode('utf-8')
            success_response.__enter__.return_value = success_response
            
            mock_urlopen.side_effect = [server_error, success_response]
            
            with patch('time.sleep') as mock_sleep:
                result = rpc_call_with_retry(self.test_url, self.test_method, self.test_params)
            
            self.assertEqual(result, mock_response)
            mock_sleep.assert_called_once()  # Should sleep due to server error
    
    def test_rpc_error_classification(self):
        """Test RPC error classification and handling."""
        rpc_errors = [
            {"code": -32602, "message": "Invalid params"},  # Should not retry
            {"code": -32000, "message": "Server error"},    # Should retry
            {"code": -32001, "message": "Rate limited"},    # Should retry with backoff
        ]
        
        for error_info in rpc_errors:
            with self.subTest(error=error_info):
                mock_error_response = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": error_info
                }
                
                with patch('urllib.request.urlopen') as mock_urlopen:
                    mock_response_obj = Mock()
                    mock_response_obj.status = 200
                    mock_response_obj.read.return_value = json.dumps(mock_error_response).encode('utf-8')
                    mock_response_obj.__enter__.return_value = mock_response_obj
                    mock_urlopen.return_value = mock_response_obj
                    
                    with self.assertRaises(RPCError) as context:
                        rpc_call_with_retry(self.test_url, self.test_method, self.test_params)
                    
                    # Check error classification
                    if error_info["code"] == -32602:
                        self.assertEqual(context.exception.error_type, "invalid_request")
                    elif error_info["code"] == -32000:
                        self.assertEqual(context.exception.error_type, "server_error")
    
    def test_all_endpoints_fail(self):
        """Test behavior when all endpoints and retries fail."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("All endpoints down")
            
            with patch('time.sleep'):  # Speed up test
                with self.assertRaises(RPCError) as context:
                    rpc_call_with_retry(
                        self.test_url, 
                        self.test_method, 
                        self.test_params,
                        fallback_urls=self.fallback_urls
                    )
                
                # Should try all URLs with all retries
                expected_calls = 3 * (1 + len(self.fallback_urls))  # 3 retries * 3 URLs
                self.assertEqual(mock_urlopen.call_count, expected_calls)
    
    def test_exponential_backoff_timing(self):
        """Test exponential backoff timing."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Network error")
            
            with patch('time.sleep') as mock_sleep:
                with self.assertRaises(RPCError):
                    rpc_call_with_retry(self.test_url, self.test_method, self.test_params, max_retries=3)
                
                # Check that sleep was called with increasing delays
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                self.assertEqual(len(sleep_calls), 2)  # 2 sleeps for 3 attempts
                
                # Each sleep should be longer than the previous (exponential backoff)
                for i in range(1, len(sleep_calls)):
                    self.assertGreater(sleep_calls[i], sleep_calls[i-1] * 0.8)  # Allow some randomness


class TestHighLevelFunctionErrorHandling(unittest.TestCase):
    """Test error handling in high-level functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pool_address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
        self.asset_address = "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        self.rpc_url = "https://test-rpc.example.com"
        self.fallback_urls = ["https://fallback.example.com"]
    
    def test_get_reserves_with_retry(self):
        """Test get_reserves function with retry logic."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000100000000000000000000000087870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
        }
        
        with patch('src.utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.return_value = mock_response
            
            result = get_reserves(self.pool_address, self.rpc_url, self.fallback_urls)
            
            # Should call RPC with fallback URLs
            mock_rpc.assert_called_once()
            call_args = mock_rpc.call_args
            self.assertEqual(call_args[1]['fallback_urls'], self.fallback_urls)
    
    def test_get_asset_symbol_graceful_failure(self):
        """Test get_asset_symbol graceful failure handling."""
        with patch('src.utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = RPCError("RPC failed", error_type="network")
            
            # Should return fallback symbol instead of raising exception
            result = get_asset_symbol(self.asset_address, self.rpc_url, self.fallback_urls)
            
            expected_fallback = f"TOKEN_{self.asset_address[-8:].upper()}"
            self.assertEqual(result, expected_fallback)
    
    def test_get_reserve_data_error_propagation(self):
        """Test get_reserve_data error propagation."""
        with patch('src.utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = NetworkError("Network down")
            
            with self.assertRaises(Exception) as context:
                get_reserve_data(self.asset_address, self.pool_address, self.rpc_url)
            
            self.assertIn("Failed to get reserve data", str(context.exception))
    
    def test_fallback_url_propagation(self):
        """Test that fallback URLs are properly propagated to RPC calls."""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000455534443000000000000000000000000000000000000000000000000000000"
        }
        
        with patch('src.utils.rpc_call_with_retry') as mock_rpc:
            mock_rpc.return_value = mock_response
            
            # Test all functions that should accept fallback URLs
            get_asset_symbol(self.asset_address, self.rpc_url, self.fallback_urls)
            
            # Verify fallback URLs were passed
            call_args = mock_rpc.call_args
            self.assertEqual(call_args[1]['fallback_urls'], self.fallback_urls)


class TestErrorClassification(unittest.TestCase):
    """Test error classification and custom exceptions."""
    
    def test_rpc_error_creation(self):
        """Test RPCError creation and attributes."""
        error = RPCError("Test error", error_type="rate_limit", retry_after=30)
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.error_type, "rate_limit")
        self.assertEqual(error.retry_after, 30)
    
    def test_network_error_creation(self):
        """Test NetworkError creation and attributes."""
        error = NetworkError("Network down", error_type="timeout")
        
        self.assertEqual(str(error), "Network down")
        self.assertEqual(error.error_type, "timeout")
    
    def test_error_type_classification(self):
        """Test error type classification in _make_single_rpc_call."""
        test_cases = [
            (429, "rate_limit"),
            (500, "server_error"),
            (502, "server_error"),
            (400, "client_error"),
            (404, "client_error"),
        ]
        
        for status_code, expected_type in test_cases:
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
    # Run tests with verbose output
    unittest.main(verbosity=2)