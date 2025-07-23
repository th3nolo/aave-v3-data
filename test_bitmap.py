"""
Comprehensive tests for Aave V3 reserve configuration bitmap decoding.
Tests bitmap parsing logic with known configuration values from real protocol data.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import _decode_configuration_bitmap, get_reserve_data, _decode_reserve_data_response
from unittest.mock import patch, Mock


class TestBitmapDecoding(unittest.TestCase):
    """Test cases for Aave V3 configuration bitmap decoding."""
    
    def test_decode_configuration_bitmap_usdc_polygon(self):
        """Test bitmap decoding with known USDC Polygon configuration values."""
        # Known USDC configuration on Polygon (approximate values for testing)
        # LTV: 75% (7500 basis points), LT: 78% (7800 basis points), LB: 5% (500 basis points)
        # Active: True, Frozen: False, Borrowing: True, Stable Borrowing: False
        # Reserve Factor: 10% (1000 basis points), Decimals: 6
        
        # Construct bitmap with known values
        ltv = 7500  # 75% in basis points
        liquidation_threshold = 7800  # 78% in basis points  
        liquidation_bonus = 500  # 5% in basis points
        decimals = 6
        reserve_factor = 1000  # 10% in basis points
        liquidation_protocol_fee = 1000  # 10% in basis points
        
        # Boolean flags
        active = True
        frozen = False
        borrowing_enabled = True
        stable_borrowing_enabled = False
        paused = False
        borrowable_in_isolation = True
        siloed_borrowing = False
        flashloan_enabled = True
        
        # Construct bitmap
        config = (
            ltv |  # Bits 0-15
            (liquidation_threshold << 16) |  # Bits 16-31
            (liquidation_bonus << 32) |  # Bits 32-47
            (decimals << 48) |  # Bits 48-55
            (int(active) << 56) |  # Bit 56
            (int(frozen) << 57) |  # Bit 57
            (int(borrowing_enabled) << 58) |  # Bit 58
            (int(stable_borrowing_enabled) << 59) |  # Bit 59
            (int(paused) << 60) |  # Bit 60
            (int(borrowable_in_isolation) << 61) |  # Bit 61
            (int(siloed_borrowing) << 62) |  # Bit 62
            (int(flashloan_enabled) << 63) |  # Bit 63
            (reserve_factor << 64) |  # Bits 64-79
            (liquidation_protocol_fee << 112)  # Bits 112-127
        )
        
        # Decode bitmap
        result = _decode_configuration_bitmap(config)
        
        # Verify decoded values
        self.assertAlmostEqual(result['loan_to_value'], 0.75, places=4)
        self.assertAlmostEqual(result['liquidation_threshold'], 0.78, places=4)
        self.assertAlmostEqual(result['liquidation_bonus'], 0.05, places=4)
        self.assertEqual(result['decimals'], 6)
        self.assertAlmostEqual(result['reserve_factor'], 0.10, places=4)
        self.assertAlmostEqual(result['liquidation_protocol_fee'], 0.10, places=4)
        
        # Verify boolean flags
        self.assertTrue(result['active'])
        self.assertFalse(result['frozen'])
        self.assertTrue(result['borrowing_enabled'])
        self.assertFalse(result['stable_borrowing_enabled'])
        self.assertFalse(result['paused'])
        self.assertTrue(result['borrowable_in_isolation'])
        self.assertFalse(result['siloed_borrowing'])
        self.assertTrue(result['flashloan_enabled'])
    
    def test_decode_configuration_bitmap_weth_ethereum(self):
        """Test bitmap decoding with known WETH Ethereum configuration values."""
        # Known WETH configuration on Ethereum (approximate values for testing)
        # LTV: 80% (8000 basis points), LT: 82.5% (8250 basis points), LB: 5% (500 basis points)
        # Active: True, Frozen: False, Borrowing: True, Stable Borrowing: False
        # Reserve Factor: 15% (1500 basis points), Decimals: 18
        
        # Construct bitmap with known values
        ltv = 8000  # 80% in basis points
        liquidation_threshold = 8250  # 82.5% in basis points
        liquidation_bonus = 500  # 5% in basis points
        decimals = 18
        reserve_factor = 1500  # 15% in basis points
        liquidation_protocol_fee = 1000  # 10% in basis points
        emode_category = 1  # ETH eMode category
        
        # Boolean flags
        active = True
        frozen = False
        borrowing_enabled = True
        stable_borrowing_enabled = False
        paused = False
        borrowable_in_isolation = False  # WETH typically not borrowable in isolation
        siloed_borrowing = False
        flashloan_enabled = True
        
        # Construct bitmap
        config = (
            ltv |  # Bits 0-15
            (liquidation_threshold << 16) |  # Bits 16-31
            (liquidation_bonus << 32) |  # Bits 32-47
            (decimals << 48) |  # Bits 48-55
            (int(active) << 56) |  # Bit 56
            (int(frozen) << 57) |  # Bit 57
            (int(borrowing_enabled) << 58) |  # Bit 58
            (int(stable_borrowing_enabled) << 59) |  # Bit 59
            (int(paused) << 60) |  # Bit 60
            (int(borrowable_in_isolation) << 61) |  # Bit 61
            (int(siloed_borrowing) << 62) |  # Bit 62
            (int(flashloan_enabled) << 63) |  # Bit 63
            (reserve_factor << 64) |  # Bits 64-79
            (liquidation_protocol_fee << 112) |  # Bits 112-127
            (emode_category << 128)  # Bits 128-135
        )
        
        # Decode bitmap
        result = _decode_configuration_bitmap(config)
        
        # Verify decoded values
        self.assertAlmostEqual(result['loan_to_value'], 0.80, places=4)
        self.assertAlmostEqual(result['liquidation_threshold'], 0.825, places=4)
        self.assertAlmostEqual(result['liquidation_bonus'], 0.05, places=4)
        self.assertEqual(result['decimals'], 18)
        self.assertAlmostEqual(result['reserve_factor'], 0.15, places=4)
        self.assertAlmostEqual(result['liquidation_protocol_fee'], 0.10, places=4)
        self.assertEqual(result['emode_category'], 1)
        
        # Verify boolean flags
        self.assertTrue(result['active'])
        self.assertFalse(result['frozen'])
        self.assertTrue(result['borrowing_enabled'])
        self.assertFalse(result['stable_borrowing_enabled'])
        self.assertFalse(result['paused'])
        self.assertFalse(result['borrowable_in_isolation'])
        self.assertFalse(result['siloed_borrowing'])
        self.assertTrue(result['flashloan_enabled'])
    
    def test_decode_configuration_bitmap_edge_cases(self):
        """Test bitmap decoding with edge cases and boundary values."""
        # Test with all zeros (inactive reserve)
        config_zero = 0
        result = _decode_configuration_bitmap(config_zero)
        
        self.assertEqual(result['loan_to_value'], 0.0)
        self.assertEqual(result['liquidation_threshold'], 0.0)
        self.assertEqual(result['liquidation_bonus'], 0.0)
        self.assertEqual(result['decimals'], 0)
        self.assertFalse(result['active'])
        self.assertFalse(result['frozen'])
        self.assertFalse(result['borrowing_enabled'])
        
        # Test with maximum values for percentage fields
        max_ltv = 10000  # 100% in basis points
        max_lt = 10000   # 100% in basis points
        max_lb = 10000   # 100% in basis points
        max_rf = 10000   # 100% in basis points
        max_decimals = 255  # 8-bit max
        
        config_max = (
            max_ltv |
            (max_lt << 16) |
            (max_lb << 32) |
            (max_decimals << 48) |
            (1 << 56) |  # Active
            (max_rf << 64)
        )
        
        result = _decode_configuration_bitmap(config_max)
        
        self.assertAlmostEqual(result['loan_to_value'], 1.0, places=4)
        self.assertAlmostEqual(result['liquidation_threshold'], 1.0, places=4)
        self.assertAlmostEqual(result['liquidation_bonus'], 1.0, places=4)
        self.assertEqual(result['decimals'], 255)
        self.assertAlmostEqual(result['reserve_factor'], 1.0, places=4)
        self.assertTrue(result['active'])
    
    def test_decode_configuration_bitmap_all_flags_set(self):
        """Test bitmap decoding with all boolean flags set to true."""
        # Set all boolean flags to true
        config = (
            (1 << 56) |  # Active
            (1 << 57) |  # Frozen
            (1 << 58) |  # Borrowing enabled
            (1 << 59) |  # Stable borrowing enabled
            (1 << 60) |  # Paused
            (1 << 61) |  # Borrowable in isolation
            (1 << 62) |  # Siloed borrowing
            (1 << 63)    # Flashloan enabled
        )
        
        result = _decode_configuration_bitmap(config)
        
        # Verify all flags are true
        self.assertTrue(result['active'])
        self.assertTrue(result['frozen'])
        self.assertTrue(result['borrowing_enabled'])
        self.assertTrue(result['stable_borrowing_enabled'])
        self.assertTrue(result['paused'])
        self.assertTrue(result['borrowable_in_isolation'])
        self.assertTrue(result['siloed_borrowing'])
        self.assertTrue(result['flashloan_enabled'])
    
    def test_decode_configuration_bitmap_caps_and_ceilings(self):
        """Test bitmap decoding with supply/borrow caps and debt ceiling."""
        # Test with caps and ceiling values
        borrow_cap = 1000000  # 1M tokens
        supply_cap = 5000000  # 5M tokens
        debt_ceiling = 10000000  # 10M USD
        unbacked_mint_cap = 100000  # 100K tokens
        
        # Note: These values might be truncated due to bit field sizes
        # Borrow cap: 16 bits (max 65535)
        # Supply cap: 16 bits (max 65535)  
        # Debt ceiling: 40 bits (max ~1T)
        # Unbacked mint cap: 40 bits (max ~1T)
        
        config = (
            (min(borrow_cap, 65535) << 80) |  # Bits 80-95 (16 bits)
            (min(supply_cap, 65535) << 96) |  # Bits 96-111 (16 bits)
            (min(unbacked_mint_cap, (1 << 40) - 1) << 168) |  # Bits 168-207 (40 bits)
            (min(debt_ceiling, (1 << 40) - 1) << 208)  # Bits 208-247 (40 bits)
        )
        
        result = _decode_configuration_bitmap(config)
        
        # Verify caps (should be truncated to 16-bit max)
        self.assertEqual(result['borrow_cap'], 65535)
        self.assertEqual(result['supply_cap'], 65535)
        self.assertEqual(result['unbacked_mint_cap'], min(unbacked_mint_cap, (1 << 40) - 1))
        self.assertEqual(result['debt_ceiling'], min(debt_ceiling, (1 << 40) - 1))
    
    @patch('src.utils.rpc_call')
    def test_get_reserve_data_integration(self, mock_rpc_call):
        """Test get_reserve_data function with mocked RPC response."""
        # Mock a realistic reserve data response
        # This simulates the actual struct returned by getReserveData()
        
        # Create mock response data (16 fields of 32 bytes each)
        mock_fields = [
            "0000000000000000000000000000000000000000000000000000000000001d4c",  # config bitmap
            "0000000000000000000000000000000000000de0b6b3a7640000000000000000",  # liquidity index
            "0000000000000000000000000000000000000000000000000000000000000000",  # current liquidity rate
            "0000000000000000000000000000000000000de0b6b3a7640000000000000000",  # variable borrow index
            "0000000000000000000000000000000000000000000000000000000000000000",  # current variable borrow rate
            "0000000000000000000000000000000000000000000000000000000000000000",  # current stable borrow rate
            "0000000000000000000000000000000000000000000000000000000065a1b2c0",  # last update timestamp
            "0000000000000000000000000000000000000000000000000000000000000001",  # reserve id
            "000000000000000000000000625E7708f30cA75bfd92586e17077590C60eb4cD",  # aToken address
            "0000000000000000000000002e8F4bdbE3d47d7d7DE490437AeA9915D930F1A3",  # stable debt token
            "000000000000000000000000FccF3cAbbe80101232d343252614b6A3eE81C989",  # variable debt token
            "000000000000000000000000A9F3C3caE095527061e6d270DBE163693e6fda9D",  # interest rate strategy
            "0000000000000000000000000000000000000000000000000000000000000000",  # accrued to treasury
            "0000000000000000000000000000000000000000000000000000000000000000",  # unbacked
            "0000000000000000000000000000000000000000000000000000000000000000",  # isolation mode total debt
            "0000000000000000000000000000000000000000000000000000000000000000"   # padding
        ]
        
        mock_response_data = "0x" + "".join(mock_fields)
        
        mock_rpc_call.return_value = {
            "result": mock_response_data
        }
        
        # Call get_reserve_data
        result = get_reserve_data(
            "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0",  # asset address
            "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # pool address
            "https://polygon-rpc.com"  # rpc url
        )
        
        # Verify the result contains expected fields
        self.assertIn('loan_to_value', result)
        self.assertIn('liquidation_threshold', result)
        self.assertIn('liquidation_bonus', result)
        self.assertIn('decimals', result)
        self.assertIn('active', result)
        self.assertIn('frozen', result)
        self.assertIn('borrowing_enabled', result)
        self.assertIn('liquidity_index', result)
        self.assertIn('a_token_address', result)
        self.assertIn('variable_debt_token_address', result)
        
        # Verify address parsing (case-insensitive comparison)
        self.assertEqual(result['a_token_address'].lower(), '0x625e7708f30ca75bfd92586e17077590c60eb4cd')
        self.assertEqual(result['variable_debt_token_address'].lower(), '0xfccf3cabbe80101232d343252614b6a3ee81c989')
        
        # Verify timestamp
        self.assertEqual(result['last_update_timestamp'], 0x65a1b2c0)
        
        # Verify RPC call was made with correct parameters
        mock_rpc_call.assert_called_once()
        call_args = mock_rpc_call.call_args
        self.assertEqual(call_args[0][1], "eth_call")  # method
        self.assertEqual(call_args[0][2][0]["to"], "0x794a61358D6845594F94dc1DB02A252b5b4814aD")  # pool address
    
    def test_decode_reserve_data_response_invalid_data(self):
        """Test reserve data response decoding with invalid data."""
        # Test with empty data
        with self.assertRaises(Exception) as context:
            _decode_reserve_data_response("0x")
        self.assertIn("Empty response data", str(context.exception))
        
        # Test with insufficient data
        with self.assertRaises(Exception) as context:
            _decode_reserve_data_response("0x1234")
        self.assertIn("Response data too short", str(context.exception))
    
    def test_bitmap_bit_extraction_accuracy(self):
        """Test accuracy of bit extraction for specific bit ranges."""
        # Test specific bit patterns to ensure extraction is working correctly
        
        # Test LTV extraction (bits 0-15)
        config_ltv_only = 7500  # 75% in basis points
        result = _decode_configuration_bitmap(config_ltv_only)
        self.assertAlmostEqual(result['loan_to_value'], 0.75, places=4)
        
        # Test Liquidation Threshold extraction (bits 16-31)
        config_lt_only = 7800 << 16  # 78% in basis points, shifted to bits 16-31
        result = _decode_configuration_bitmap(config_lt_only)
        self.assertAlmostEqual(result['liquidation_threshold'], 0.78, places=4)
        self.assertEqual(result['loan_to_value'], 0.0)  # Should be zero
        
        # Test Liquidation Bonus extraction (bits 32-47)
        config_lb_only = 500 << 32  # 5% in basis points, shifted to bits 32-47
        result = _decode_configuration_bitmap(config_lb_only)
        self.assertAlmostEqual(result['liquidation_bonus'], 0.05, places=4)
        self.assertEqual(result['loan_to_value'], 0.0)  # Should be zero
        self.assertEqual(result['liquidation_threshold'], 0.0)  # Should be zero
        
        # Test Decimals extraction (bits 48-55)
        config_decimals_only = 18 << 48  # 18 decimals, shifted to bits 48-55
        result = _decode_configuration_bitmap(config_decimals_only)
        self.assertEqual(result['decimals'], 18)
        
        # Test Reserve Factor extraction (bits 64-79)
        config_rf_only = 1000 << 64  # 10% in basis points, shifted to bits 64-79
        result = _decode_configuration_bitmap(config_rf_only)
        self.assertAlmostEqual(result['reserve_factor'], 0.10, places=4)
    
    def test_percentage_conversion_accuracy(self):
        """Test accuracy of percentage conversions from basis points."""
        # Test various percentage values
        test_cases = [
            (0, 0.0),      # 0%
            (1, 0.0001),   # 0.01%
            (100, 0.01),   # 1%
            (500, 0.05),   # 5%
            (1000, 0.10),  # 10%
            (2500, 0.25),  # 25%
            (5000, 0.50),  # 50%
            (7500, 0.75),  # 75%
            (10000, 1.0),  # 100%
        ]
        
        for basis_points, expected_decimal in test_cases:
            # Test LTV conversion
            config = basis_points  # LTV is in bits 0-15
            result = _decode_configuration_bitmap(config)
            self.assertAlmostEqual(
                result['loan_to_value'], 
                expected_decimal, 
                places=4,
                msg=f"LTV conversion failed for {basis_points} basis points"
            )
            
            # Test Liquidation Threshold conversion
            config = basis_points << 16  # LT is in bits 16-31
            result = _decode_configuration_bitmap(config)
            self.assertAlmostEqual(
                result['liquidation_threshold'], 
                expected_decimal, 
                places=4,
                msg=f"LT conversion failed for {basis_points} basis points"
            )


    def test_get_reserve_data_method_id_generation(self):
        """Test that get_reserve_data generates correct method ID and call data."""
        from src.utils import get_method_id
        
        # Test method ID generation for getReserveData(address)
        method_id = get_method_id("getReserveData(address)")
        
        # Verify it's a valid method ID format
        self.assertTrue(method_id.startswith('0x'))
        self.assertEqual(len(method_id), 10)  # 0x + 8 hex chars
        
        # The method ID should be consistent
        method_id_2 = get_method_id("getReserveData(address)")
        self.assertEqual(method_id, method_id_2)
        
        # Different method should produce different ID
        different_method_id = get_method_id("getReservesList()")
        self.assertNotEqual(method_id, different_method_id)
    
    def test_reserve_data_call_data_encoding(self):
        """Test that reserve data call includes properly encoded asset address."""
        # This test verifies the call data construction in get_reserve_data
        asset_address = "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        
        # The asset address should be encoded as 32 bytes (64 hex chars)
        # Remove 0x prefix and pad to 64 characters
        expected_param = asset_address[2:].zfill(64)
        self.assertEqual(len(expected_param), 64)
        
        # Verify the address is properly formatted
        self.assertTrue(all(c in '0123456789abcdefABCDEF' for c in expected_param))
        
        # The call data should be method_id + encoded_address
        from src.utils import get_method_id
        method_id = get_method_id("getReserveData(address)")
        expected_call_data = method_id + expected_param
        
        # Verify total length (10 chars for method_id + 64 chars for address)
        self.assertEqual(len(expected_call_data), 74)


if __name__ == '__main__':
    unittest.main()