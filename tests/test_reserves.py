"""
Tests for reserve data fetching functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import get_reserves, _decode_address_array


class TestReserves(unittest.TestCase):
    """Test cases for reserve list retrieval."""
    
    def test_decode_address_array_empty(self):
        """Test decoding empty address array."""
        # Empty response
        result = _decode_address_array('0x')
        self.assertEqual(result, [])
        
        # Response with zero length
        empty_array = '0x' + '0' * 64 + '0' * 64  # offset + length=0
        result = _decode_address_array(empty_array)
        self.assertEqual(result, [])
    
    def test_decode_address_array_single(self):
        """Test decoding single address array."""
        # Mock response for single address array
        # offset (32 bytes) + length=1 (32 bytes) + address (32 bytes padded)
        single_address = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000001'  # length = 1
            '000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'  # address padded
        )
        
        result = _decode_address_array(single_address)
        expected = ['0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0']
        self.assertEqual(result, expected)
    
    def test_decode_address_array_multiple(self):
        """Test decoding multiple address array."""
        # Mock response for two addresses
        multiple_addresses = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000002'  # length = 2
            '000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'  # address 1
            '0000000000000000000000002260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'  # address 2 (WBTC)
        )
        
        result = _decode_address_array(multiple_addresses)
        expected = [
            '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0',
            '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
        ]
        self.assertEqual(result, expected)
    
    def test_decode_address_array_invalid(self):
        """Test decoding invalid address array."""
        # Too short data
        with self.assertRaises(Exception):
            _decode_address_array('0x1234')
        
        # Invalid hex
        with self.assertRaises(Exception):
            _decode_address_array('0xGGGG')
    
    @patch('utils.rpc_call')
    def test_get_reserves_success(self, mock_rpc_call):
        """Test successful reserve list retrieval."""
        # Mock successful RPC response
        mock_response = {
            'result': (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                '0000000000000000000000000000000000000000000000000000000000000002'  # length = 2
                '000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'  # USDC
                '0000000000000000000000002260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'  # WBTC
            )
        }
        mock_rpc_call.return_value = mock_response
        
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_reserves(pool_address, rpc_url)
        
        expected = [
            '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0',
            '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
        ]
        self.assertEqual(result, expected)
        
        # Verify RPC call was made correctly
        mock_rpc_call.assert_called_once()
        call_args = mock_rpc_call.call_args
        self.assertEqual(call_args[0][1], 'eth_call')  # method
        self.assertEqual(call_args[0][2][0]['to'], pool_address)  # to address
        self.assertTrue(call_args[0][2][0]['data'].startswith('0x'))  # method data
    
    @patch('utils.rpc_call')
    def test_get_reserves_no_result(self, mock_rpc_call):
        """Test reserve list retrieval with no result."""
        # Mock RPC response without result
        mock_rpc_call.return_value = {'error': 'Some error'}
        
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        with self.assertRaises(Exception) as context:
            get_reserves(pool_address, rpc_url)
        
        self.assertIn('No result in RPC response', str(context.exception))
    
    @patch('utils.rpc_call')
    def test_get_reserves_empty_result(self, mock_rpc_call):
        """Test reserve list retrieval with empty result."""
        # Mock RPC response with empty array
        mock_response = {
            'result': (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                '0000000000000000000000000000000000000000000000000000000000000000'  # length = 0
            )
        }
        mock_rpc_call.return_value = mock_response
        
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_reserves(pool_address, rpc_url)
        self.assertEqual(result, [])
    
    @patch('utils.rpc_call')
    def test_get_reserves_rpc_exception(self, mock_rpc_call):
        """Test reserve list retrieval with RPC exception."""
        # Mock RPC call raising exception
        mock_rpc_call.side_effect = Exception('Network error')
        
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        with self.assertRaises(Exception) as context:
            get_reserves(pool_address, rpc_url)
        
        self.assertIn('Network error', str(context.exception))


class TestAssetSymbol(unittest.TestCase):
    """Test cases for ERC20 symbol fetching."""
    
    def test_decode_string_response_empty(self):
        """Test decoding empty string response."""
        from utils import _decode_string_response
        
        # Empty response
        result = _decode_string_response('0x')
        self.assertEqual(result, 'UNKNOWN')
        
        # Response with zero length
        empty_string = '0x' + '0' * 64 + '0' * 64  # offset + length=0
        result = _decode_string_response(empty_string)
        self.assertEqual(result, 'EMPTY')
    
    def test_decode_string_response_valid(self):
        """Test decoding valid string responses."""
        from utils import _decode_string_response
        
        # Mock response for "USDC" (4 characters)
        usdc_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
            '5553444300000000000000000000000000000000000000000000000000000000'  # "USDC" padded
        )
        
        result = _decode_string_response(usdc_response)
        self.assertEqual(result, 'USDC')
        
        # Mock response for "WETH" (4 characters)
        weth_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
            '5745544800000000000000000000000000000000000000000000000000000000'  # "WETH" padded
        )
        
        result = _decode_string_response(weth_response)
        self.assertEqual(result, 'WETH')
    
    def test_decode_string_response_long_symbol(self):
        """Test decoding longer symbol."""
        from utils import _decode_string_response
        
        # Mock response for "AAVE" (4 characters)
        aave_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
            '4141564500000000000000000000000000000000000000000000000000000000'  # "AAVE" padded
        )
        
        result = _decode_string_response(aave_response)
        self.assertEqual(result, 'AAVE')
    
    def test_decode_string_response_invalid(self):
        """Test decoding invalid string responses."""
        from utils import _decode_string_response
        
        # Too short data
        result = _decode_string_response('0x1234')
        self.assertEqual(result, 'UNKNOWN')
        
        # Invalid length (very large number)
        invalid_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'  # invalid length
        )
        
        result = _decode_string_response(invalid_response)
        # This should return INVALID because the length is too large
        self.assertEqual(result, 'INVALID')
    
    def test_decode_string_response_utf8_edge_cases(self):
        """Test UTF-8 decoding with various edge cases and non-standard symbols."""
        from utils import _decode_string_response
        
        # Test with null bytes in symbol (should be stripped)
        symbol_with_nulls = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000008'  # length = 8
            '555344430000000000000000000000000000000000000000000000000000000'  # "USDC" + nulls
        )
        result = _decode_string_response(symbol_with_nulls)
        self.assertEqual(result, 'USDC')
        
        # Test with symbol containing underscores and dashes (valid)
        underscore_symbol = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000008'  # length = 8
            '544F4B454E5F3100000000000000000000000000000000000000000000000000'  # "TOKEN_1"
        )
        result = _decode_string_response(underscore_symbol)
        self.assertEqual(result, 'TOKEN_1')
        
        # Test with very long symbol (should return INVALID)
        long_symbol = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000030'  # length = 48 (too long)
            + '41' * 96  # 48 'A' characters (96 hex chars)
        )
        result = _decode_string_response(long_symbol)
        self.assertEqual(result, 'INVALID')
        
        # Test with non-alphanumeric characters (should return INVALID)
        special_chars = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
            '24242424000000000000000000000000000000000000000000000000000000000'  # "$$$$"
        )
        result = _decode_string_response(special_chars)
        self.assertEqual(result, 'INVALID')
    
    def test_decode_string_response_non_utf8(self):
        """Test decoding with non-UTF8 bytes that require latin-1 fallback."""
        from utils import _decode_string_response
        
        # Create a response with bytes that are invalid UTF-8 but valid latin-1
        # Using bytes 0xFF which is invalid in UTF-8 but valid in latin-1
        non_utf8_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
            'FF555344000000000000000000000000000000000000000000000000000000000'  # 0xFF + "USD"
        )
        result = _decode_string_response(non_utf8_response)
        # Should fall back to latin-1 and filter out non-printable characters
        self.assertEqual(result, 'USD')
        
        # Test with completely invalid bytes that can't be decoded
        invalid_bytes = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '0000000000000000000000000000000000000000000000000000000000000002'  # length = 2
            'FFFF000000000000000000000000000000000000000000000000000000000000'  # Invalid bytes
        )
        result = _decode_string_response(invalid_bytes)
        # Should return NON_UTF8 after latin-1 processing
        self.assertEqual(result, 'NON_UTF8')
    
    def test_decode_string_response_truncated_data(self):
        """Test decoding with truncated response data."""
        from utils import _decode_string_response
        
        # Response claims length 10 but only has 4 bytes of data
        truncated_response = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            '000000000000000000000000000000000000000000000000000000000000000A'  # length = 10
            '5553444300000000'  # Only 4 bytes instead of 10
        )
        result = _decode_string_response(truncated_response)
        # Should handle truncation gracefully and return what it can decode
        self.assertEqual(result, 'USDC')
    
    def test_decode_string_response_parse_errors(self):
        """Test decoding with various parsing errors."""
        from utils import _decode_string_response
        
        # Test with malformed hex data
        malformed_hex = '0xGGGGGGGG'  # Invalid hex characters
        result = _decode_string_response(malformed_hex)
        self.assertEqual(result, 'UNKNOWN')
        
        # Test with response that causes ValueError in int conversion
        bad_length = (
            '0x'
            '0000000000000000000000000000000000000000000000000000000000000020'  # offset = 32
            'ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ'  # Invalid hex for length
        )
        result = _decode_string_response(bad_length)
        self.assertEqual(result, 'PARSE_ERROR')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_success(self, mock_rpc_call):
        """Test successful asset symbol retrieval."""
        from utils import get_asset_symbol
        
        # Mock successful RPC response for USDC
        mock_response = {
            'result': (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
                '5553444300000000000000000000000000000000000000000000000000000000'  # "USDC"
            )
        }
        mock_rpc_call.return_value = mock_response
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        self.assertEqual(result, 'USDC')
        
        # Verify RPC call was made correctly
        mock_rpc_call.assert_called_once()
        call_args = mock_rpc_call.call_args
        self.assertEqual(call_args[0][1], 'eth_call')  # method
        self.assertEqual(call_args[0][2][0]['to'], asset_address)  # to address
        self.assertTrue(call_args[0][2][0]['data'].startswith('0x'))  # method data
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_fallback(self, mock_rpc_call):
        """Test asset symbol retrieval with fallback."""
        from utils import get_asset_symbol
        
        # Mock RPC call raising exception
        mock_rpc_call.side_effect = Exception('Network error')
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format
        self.assertEqual(result, 'TOKEN_7BF77FB0')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_no_result(self, mock_rpc_call):
        """Test asset symbol retrieval with no result."""
        from utils import get_asset_symbol
        
        # Mock RPC response without result
        mock_rpc_call.return_value = {'error': 'Some error'}
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format
        self.assertEqual(result, 'TOKEN_7BF77FB0')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_various_token_types(self, mock_rpc_call):
        """Test asset symbol retrieval for various token types."""
        from utils import get_asset_symbol
        
        # Test different token symbols and their expected responses
        test_cases = [
            # (symbol, hex_response, expected_result)
            ('WETH', '5745544800000000000000000000000000000000000000000000000000000000', 'WETH'),
            ('DAI', '4441490000000000000000000000000000000000000000000000000000000000', 'DAI'),
            ('AAVE', '4141564500000000000000000000000000000000000000000000000000000000', 'AAVE'),
            ('LINK', '4C494E4B00000000000000000000000000000000000000000000000000000000', 'LINK'),
            ('UNI', '554E490000000000000000000000000000000000000000000000000000000000', 'UNI'),
        ]
        
        for symbol, hex_data, expected in test_cases:
            with self.subTest(symbol=symbol):
                # Create mock response
                mock_response = {
                    'result': (
                        '0x'
                        '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                        f'{len(symbol):064x}'  # length
                        f'{hex_data}'
                    )
                }
                mock_rpc_call.return_value = mock_response
                
                asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
                rpc_url = 'https://rpc.ankr.com/eth'
                
                result = get_asset_symbol(asset_address, rpc_url)
                self.assertEqual(result, expected)
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_empty_response(self, mock_rpc_call):
        """Test asset symbol retrieval with empty response."""
        from utils import get_asset_symbol
        
        # Mock empty response
        mock_response = {'result': '0x'}
        mock_rpc_call.return_value = mock_response
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format
        self.assertEqual(result, 'TOKEN_7BF77FB0')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_invalid_symbol(self, mock_rpc_call):
        """Test asset symbol retrieval with invalid symbol data."""
        from utils import get_asset_symbol
        
        # Mock response with invalid symbol (too long)
        mock_response = {
            'result': (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                '0000000000000000000000000000000000000000000000000000000000000030'  # length = 48 (too long)
                '41' * 96  # 48 'A' characters
            )
        }
        mock_rpc_call.return_value = mock_response
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format when symbol is invalid
        self.assertEqual(result, 'TOKEN_7BF77FB0')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_non_utf8_handling(self, mock_rpc_call):
        """Test asset symbol retrieval with non-UTF8 characters."""
        from utils import get_asset_symbol
        
        # Mock response with non-UTF8 bytes
        mock_response = {
            'result': (
                '0x'
                '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
                'FF555344000000000000000000000000000000000000000000000000000000000'  # 0xFF + "USD"
            )
        }
        mock_rpc_call.return_value = mock_response
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should handle non-UTF8 gracefully and return processed symbol
        self.assertEqual(result, 'USD')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_rpc_timeout(self, mock_rpc_call):
        """Test asset symbol retrieval with RPC timeout."""
        from utils import get_asset_symbol
        import urllib.error
        
        # Mock RPC call raising timeout error
        mock_rpc_call.side_effect = urllib.error.URLError('timeout')
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format on timeout
        self.assertEqual(result, 'TOKEN_7BF77FB0')
    
    @patch('utils.rpc_call')
    def test_get_asset_symbol_contract_not_found(self, mock_rpc_call):
        """Test asset symbol retrieval when contract doesn't exist."""
        from utils import get_asset_symbol
        
        # Mock RPC response for non-existent contract
        mock_rpc_call.return_value = {'result': '0x'}
        
        asset_address = '0x0000000000000000000000000000000000000000'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_asset_symbol(asset_address, rpc_url)
        # Should return fallback format
        self.assertEqual(result, 'TOKEN_00000000')


class TestReserveData(unittest.TestCase):
    """Test cases for reserve data extraction and bitmap decoding."""
    
    def test_decode_configuration_bitmap(self):
        """Test configuration bitmap decoding with known values."""
        from utils import _decode_configuration_bitmap
        
        # Test bitmap with known USDC-like configuration
        # LTV=75% (7500 bp), LT=78% (7800 bp), LB=5% (500 bp), decimals=6
        # Active=true, Frozen=false, Borrowing=true, Stable=false, etc.
        config = (
            7500 |          # LTV (bits 0-15)
            (7800 << 16) |   # LT (bits 16-31)
            (500 << 32) |    # LB (bits 32-47)
            (6 << 48) |      # Decimals (bits 48-55)
            (1 << 56) |      # Active (bit 56)
            (0 << 57) |      # Frozen (bit 57)
            (1 << 58) |      # Borrowing enabled (bit 58)
            (0 << 59) |      # Stable borrowing disabled (bit 59)
            (0 << 60) |      # Not paused (bit 60)
            (1 << 61) |      # Borrowable in isolation (bit 61)
            (0 << 62) |      # Not siloed (bit 62)
            (1 << 63) |      # Flashloan enabled (bit 63)
            (1000 << 64) |   # Reserve factor 10% (bits 64-79)
            (0 << 80) |      # No borrow cap (bits 80-95)
            (0 << 96) |      # No supply cap (bits 96-111)
            (1000 << 112) |  # Liquidation protocol fee 10% (bits 112-127)
            (1 << 128)       # eMode category 1 (bits 128-135)
        )
        
        result = _decode_configuration_bitmap(config)
        
        # Verify decoded values
        self.assertEqual(result['loan_to_value'], 0.75)
        self.assertEqual(result['liquidation_threshold'], 0.78)
        self.assertEqual(result['liquidation_bonus'], 0.05)
        self.assertEqual(result['decimals'], 6)
        self.assertTrue(result['active'])
        self.assertFalse(result['frozen'])
        self.assertTrue(result['borrowing_enabled'])
        self.assertFalse(result['stable_borrowing_enabled'])
        self.assertFalse(result['paused'])
        self.assertTrue(result['borrowable_in_isolation'])
        self.assertFalse(result['siloed_borrowing'])
        self.assertTrue(result['flashloan_enabled'])
        self.assertEqual(result['reserve_factor'], 0.10)
        self.assertEqual(result['borrow_cap'], 0)
        self.assertEqual(result['supply_cap'], 0)
        self.assertEqual(result['liquidation_protocol_fee'], 0.10)
        self.assertEqual(result['emode_category'], 1)
    
    def test_decode_configuration_bitmap_zero(self):
        """Test configuration bitmap decoding with zero value."""
        from utils import _decode_configuration_bitmap
        
        result = _decode_configuration_bitmap(0)
        
        # All values should be zero/false
        self.assertEqual(result['loan_to_value'], 0.0)
        self.assertEqual(result['liquidation_threshold'], 0.0)
        self.assertEqual(result['liquidation_bonus'], 0.0)
        self.assertEqual(result['decimals'], 0)
        self.assertFalse(result['active'])
        self.assertFalse(result['frozen'])
        self.assertFalse(result['borrowing_enabled'])
        self.assertFalse(result['stable_borrowing_enabled'])
        self.assertFalse(result['paused'])
        self.assertFalse(result['borrowable_in_isolation'])
        self.assertFalse(result['siloed_borrowing'])
        self.assertFalse(result['flashloan_enabled'])
        self.assertEqual(result['reserve_factor'], 0.0)
        self.assertEqual(result['borrow_cap'], 0)
        self.assertEqual(result['supply_cap'], 0)
        self.assertEqual(result['liquidation_protocol_fee'], 0.0)
        self.assertEqual(result['emode_category'], 0)
    
    def test_decode_reserve_data_response(self):
        """Test reserve data response decoding."""
        from utils import _decode_reserve_data_response
        
        # Mock response with realistic values
        # Configuration bitmap (USDC-like)
        config = (
            7500 |          # LTV=75%
            (7800 << 16) |   # LT=78%
            (500 << 32) |    # LB=5%
            (6 << 48) |      # decimals=6
            (1 << 56) |      # active
            (1 << 58) |      # borrowing enabled
            (1 << 61) |      # borrowable in isolation
            (1 << 63) |      # flashloan enabled
            (1000 << 64) |   # reserve factor=10%
            (1000 << 112) |  # liquidation protocol fee=10%
            (1 << 128)       # eMode category=1
        )
        
        # Create mock response (16 fields of 32 bytes each)
        RAY = 10**27
        mock_response = '0x' + ''.join([
            f"{config:064x}",                           # configuration
            f"{int(1.05 * RAY):064x}",                  # liquidity_index
            f"{int(0.02 * RAY):064x}",                  # current_liquidity_rate
            f"{int(1.08 * RAY):064x}",                  # variable_borrow_index
            f"{int(0.04 * RAY):064x}",                  # current_variable_borrow_rate
            f"{int(0.06 * RAY):064x}",                  # current_stable_borrow_rate
            f"{1704067200:064x}",                       # last_update_timestamp
            f"{1:064x}",                                # reserve_id
            f"{'A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # a_token_address
            f"{'B0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # stable_debt_token
            f"{'C0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # variable_debt_token
            f"{'D0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # interest_rate_strategy
            f"{int(0.01 * RAY):064x}",                  # accrued_to_treasury
            f"{int(0.005 * RAY):064x}",                 # unbacked
            f"{int(1000000 * RAY):064x}",               # isolation_mode_total_debt
            f"{0:064x}"                                 # padding
        ])
        
        result = _decode_reserve_data_response(mock_response)
        
        # Verify configuration data
        self.assertEqual(result['loan_to_value'], 0.75)
        self.assertEqual(result['liquidation_threshold'], 0.78)
        self.assertEqual(result['liquidation_bonus'], 0.05)
        self.assertEqual(result['decimals'], 6)
        self.assertTrue(result['active'])
        self.assertTrue(result['borrowing_enabled'])
        
        # Verify rate and index data
        self.assertAlmostEqual(result['liquidity_index'], 1.05, places=6)
        self.assertAlmostEqual(result['current_liquidity_rate'], 0.02, places=6)
        self.assertAlmostEqual(result['variable_borrow_index'], 1.08, places=6)
        self.assertAlmostEqual(result['current_variable_borrow_rate'], 0.04, places=6)
        self.assertAlmostEqual(result['current_stable_borrow_rate'], 0.06, places=6)
        
        # Verify other fields
        self.assertEqual(result['last_update_timestamp'], 1704067200)
        self.assertEqual(result['reserve_id'], 1)
        self.assertEqual(result['a_token_address'], '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0')
        self.assertEqual(result['stable_debt_token_address'], '0xB0b86a33E6441E8e421B27D6c5a9c7157bF77FB0')
        self.assertEqual(result['variable_debt_token_address'], '0xC0b86a33E6441E8e421B27D6c5a9c7157bF77FB0')
    
    def test_decode_reserve_data_response_empty(self):
        """Test reserve data response decoding with empty data."""
        from utils import _decode_reserve_data_response
        
        with self.assertRaises(Exception) as context:
            _decode_reserve_data_response('0x')
        
        self.assertIn('Empty response data', str(context.exception))
    
    def test_decode_reserve_data_response_short(self):
        """Test reserve data response decoding with insufficient data."""
        from utils import _decode_reserve_data_response
        
        # Too short response
        short_response = '0x' + '0' * 100
        
        with self.assertRaises(Exception) as context:
            _decode_reserve_data_response(short_response)
        
        self.assertIn('Response data too short', str(context.exception))
    
    @patch('utils.rpc_call')
    def test_get_reserve_data_success(self, mock_rpc_call):
        """Test successful reserve data retrieval."""
        from utils import get_reserve_data
        
        # Mock successful RPC response
        config = (
            7500 |          # LTV=75%
            (7800 << 16) |   # LT=78%
            (500 << 32) |    # LB=5%
            (6 << 48) |      # decimals=6
            (1 << 56) |      # active
            (1 << 58)        # borrowing enabled
        )
        
        RAY = 10**27
        mock_response = {
            'result': '0x' + ''.join([
                f"{config:064x}",                           # configuration
                f"{int(1.05 * RAY):064x}",                  # liquidity_index
                f"{int(0.02 * RAY):064x}",                  # current_liquidity_rate
                f"{int(1.08 * RAY):064x}",                  # variable_borrow_index
                f"{int(0.04 * RAY):064x}",                  # current_variable_borrow_rate
                f"{int(0.06 * RAY):064x}",                  # current_stable_borrow_rate
                f"{1704067200:064x}",                       # last_update_timestamp
                f"{1:064x}",                                # reserve_id
                f"{'A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # a_token_address
                f"{'B0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # stable_debt_token
                f"{'C0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # variable_debt_token
                f"{'D0b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # interest_rate_strategy
                f"{0:064x}",                                # accrued_to_treasury
                f"{0:064x}",                                # unbacked
                f"{0:064x}",                                # isolation_mode_total_debt
                f"{0:064x}"                                 # padding
            ])
        }
        mock_rpc_call.return_value = mock_response
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        result = get_reserve_data(asset_address, pool_address, rpc_url)
        
        # Verify key values
        self.assertEqual(result['loan_to_value'], 0.75)
        self.assertEqual(result['liquidation_threshold'], 0.78)
        self.assertEqual(result['liquidation_bonus'], 0.05)
        self.assertTrue(result['active'])
        self.assertTrue(result['borrowing_enabled'])
        
        # Verify RPC call was made correctly
        mock_rpc_call.assert_called_once()
        call_args = mock_rpc_call.call_args
        self.assertEqual(call_args[0][1], 'eth_call')  # method
        self.assertEqual(call_args[0][2][0]['to'], pool_address)  # to address
        # Verify call data includes method ID and asset address
        call_data = call_args[0][2][0]['data']
        self.assertTrue(call_data.startswith('0x'))
        self.assertIn(asset_address[2:].lower(), call_data.lower())
    
    @patch('utils.rpc_call')
    def test_get_reserve_data_no_result(self, mock_rpc_call):
        """Test reserve data retrieval with no result."""
        from utils import get_reserve_data
        
        # Mock RPC response without result
        mock_rpc_call.return_value = {'error': 'Some error'}
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        with self.assertRaises(Exception) as context:
            get_reserve_data(asset_address, pool_address, rpc_url)
        
        self.assertIn('No result in RPC response', str(context.exception))
    
    @patch('utils.rpc_call')
    def test_get_reserve_data_rpc_exception(self, mock_rpc_call):
        """Test reserve data retrieval with RPC exception."""
        from utils import get_reserve_data
        
        # Mock RPC call raising exception
        mock_rpc_call.side_effect = Exception('Network error')
        
        asset_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        pool_address = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
        rpc_url = 'https://rpc.ankr.com/eth'
        
        with self.assertRaises(Exception) as context:
            get_reserve_data(asset_address, pool_address, rpc_url)
        
        self.assertIn('Network error', str(context.exception))


if __name__ == '__main__':
    unittest.main()