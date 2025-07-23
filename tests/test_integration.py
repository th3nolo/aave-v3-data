"""
Integration tests for reserve data fetching functionality.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import get_reserves, get_asset_symbol, get_reserve_data
from networks import AAVE_V3_NETWORKS


class TestIntegration(unittest.TestCase):
    """Integration tests for complete reserve data fetching workflow."""
    
    @patch('utils.rpc_call')
    def test_complete_reserve_workflow(self, mock_rpc_call):
        """Test complete workflow: get reserves -> get symbols -> get reserve data."""
        
        # Mock network configuration
        network = AAVE_V3_NETWORKS['ethereum']
        pool_address = network['pool']
        rpc_url = network['rpc']
        
        # Mock asset addresses
        usdc_address = '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'
        weth_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        
        # Setup mock responses for different calls
        def mock_rpc_side_effect(url, method, params):
            call_data = params[0]['data']
            
            # getReservesList() call
            if call_data.startswith('0x226210f0'):
                return {
                    'result': (
                        '0x'
                        '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                        '0000000000000000000000000000000000000000000000000000000000000002'  # length = 2
                        '000000000000000000000000A0b86a33E6441E8e421B27D6c5a9c7157bF77FB0'  # USDC
                        '000000000000000000000000C02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'  # WETH
                    )
                }
            
            # symbol() call for USDC
            elif params[0]['to'] == usdc_address and call_data.startswith('0x231782d8'):
                return {
                    'result': (
                        '0x'
                        '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                        '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
                        '5553444300000000000000000000000000000000000000000000000000000000'  # "USDC"
                    )
                }
            
            # symbol() call for WETH
            elif params[0]['to'] == weth_address and call_data.startswith('0x231782d8'):
                return {
                    'result': (
                        '0x'
                        '0000000000000000000000000000000000000000000000000000000000000020'  # offset
                        '0000000000000000000000000000000000000000000000000000000000000004'  # length = 4
                        '5745544800000000000000000000000000000000000000000000000000000000'  # "WETH"
                    )
                }
            
            # getReserveData() call for USDC
            elif params[0]['to'] == pool_address and call_data.startswith('0xb78c2913') and usdc_address[2:].lower() in call_data.lower():
                config = (
                    7500 |          # LTV=75%
                    (7800 << 16) |   # LT=78%
                    (500 << 32) |    # LB=5%
                    (6 << 48) |      # decimals=6
                    (1 << 56) |      # active
                    (1 << 58) |      # borrowing enabled
                    (1 << 61) |      # borrowable in isolation
                    (1000 << 64)     # reserve factor=10%
                )
                
                RAY = 10**27
                return {
                    'result': '0x' + ''.join([
                        f"{config:064x}",                           # configuration
                        f"{int(1.05 * RAY):064x}",                  # liquidity_index
                        f"{int(0.02 * RAY):064x}",                  # current_liquidity_rate
                        f"{int(1.08 * RAY):064x}",                  # variable_borrow_index
                        f"{int(0.04 * RAY):064x}",                  # current_variable_borrow_rate
                        f"{int(0.06 * RAY):064x}",                  # current_stable_borrow_rate
                        f"{1704067200:064x}",                       # last_update_timestamp
                        f"{1:064x}",                                # reserve_id
                        f"{'A1b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # a_token_address
                        f"{'A2b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # stable_debt_token
                        f"{'A3b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # variable_debt_token
                        f"{'A4b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # interest_rate_strategy
                        f"{0:064x}",                                # accrued_to_treasury
                        f"{0:064x}",                                # unbacked
                        f"{0:064x}",                                # isolation_mode_total_debt
                        f"{0:064x}"                                 # padding
                    ])
                }
            
            # getReserveData() call for WETH
            elif params[0]['to'] == pool_address and call_data.startswith('0xb78c2913') and weth_address[2:].lower() in call_data.lower():
                config = (
                    8000 |          # LTV=80%
                    (8250 << 16) |   # LT=82.5%
                    (500 << 32) |    # LB=5%
                    (18 << 48) |     # decimals=18
                    (1 << 56) |      # active
                    (1 << 58) |      # borrowing enabled
                    (1500 << 64)     # reserve factor=15%
                )
                
                RAY = 10**27
                return {
                    'result': '0x' + ''.join([
                        f"{config:064x}",                           # configuration
                        f"{int(1.03 * RAY):064x}",                  # liquidity_index
                        f"{int(0.015 * RAY):064x}",                 # current_liquidity_rate
                        f"{int(1.06 * RAY):064x}",                  # variable_borrow_index
                        f"{int(0.035 * RAY):064x}",                 # current_variable_borrow_rate
                        f"{int(0.055 * RAY):064x}",                 # current_stable_borrow_rate
                        f"{1704067200:064x}",                       # last_update_timestamp
                        f"{2:064x}",                                # reserve_id
                        f"{'B1b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # a_token_address
                        f"{'B2b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # stable_debt_token
                        f"{'B3b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # variable_debt_token
                        f"{'B4b86a33E6441E8e421B27D6c5a9c7157bF77FB0':>064}",  # interest_rate_strategy
                        f"{0:064x}",                                # accrued_to_treasury
                        f"{0:064x}",                                # unbacked
                        f"{0:064x}",                                # isolation_mode_total_debt
                        f"{0:064x}"                                 # padding
                    ])
                }
            
            # Default fallback
            return {'error': 'Unknown call'}
        
        mock_rpc_call.side_effect = mock_rpc_side_effect
        
        # Step 1: Get list of reserves
        reserves = get_reserves(pool_address, rpc_url)
        self.assertEqual(len(reserves), 2)
        self.assertIn(usdc_address, reserves)
        self.assertIn(weth_address, reserves)
        
        # Step 2: Get symbols for each reserve
        usdc_symbol = get_asset_symbol(usdc_address, rpc_url)
        weth_symbol = get_asset_symbol(weth_address, rpc_url)
        
        self.assertEqual(usdc_symbol, 'USDC')
        self.assertEqual(weth_symbol, 'WETH')
        
        # Step 3: Get reserve data for each asset
        usdc_data = get_reserve_data(usdc_address, pool_address, rpc_url)
        weth_data = get_reserve_data(weth_address, pool_address, rpc_url)
        
        # Verify USDC data
        self.assertEqual(usdc_data['loan_to_value'], 0.75)
        self.assertEqual(usdc_data['liquidation_threshold'], 0.78)
        self.assertEqual(usdc_data['liquidation_bonus'], 0.05)
        self.assertEqual(usdc_data['decimals'], 6)
        self.assertTrue(usdc_data['active'])
        self.assertTrue(usdc_data['borrowing_enabled'])
        self.assertTrue(usdc_data['borrowable_in_isolation'])
        self.assertEqual(usdc_data['reserve_factor'], 0.10)
        
        # Verify WETH data
        self.assertEqual(weth_data['loan_to_value'], 0.80)
        self.assertEqual(weth_data['liquidation_threshold'], 0.825)
        self.assertEqual(weth_data['liquidation_bonus'], 0.05)
        self.assertEqual(weth_data['decimals'], 18)
        self.assertTrue(weth_data['active'])
        self.assertTrue(weth_data['borrowing_enabled'])
        self.assertEqual(weth_data['reserve_factor'], 0.15)
        
        # Verify that we can create a complete dataset
        complete_data = {
            'network': 'ethereum',
            'pool_address': pool_address,
            'reserves': [
                {
                    'asset_address': usdc_address,
                    'symbol': usdc_symbol,
                    **usdc_data
                },
                {
                    'asset_address': weth_address,
                    'symbol': weth_symbol,
                    **weth_data
                }
            ]
        }
        
        # Verify the complete dataset structure
        self.assertEqual(complete_data['network'], 'ethereum')
        self.assertEqual(len(complete_data['reserves']), 2)
        
        # Verify first reserve (USDC)
        usdc_reserve = complete_data['reserves'][0]
        self.assertEqual(usdc_reserve['symbol'], 'USDC')
        self.assertEqual(usdc_reserve['asset_address'], usdc_address)
        self.assertEqual(usdc_reserve['liquidation_threshold'], 0.78)
        
        # Verify second reserve (WETH)
        weth_reserve = complete_data['reserves'][1]
        self.assertEqual(weth_reserve['symbol'], 'WETH')
        self.assertEqual(weth_reserve['asset_address'], weth_address)
        self.assertEqual(weth_reserve['liquidation_threshold'], 0.825)
        
        print("✓ Integration test passed: Complete reserve data workflow working correctly")


if __name__ == '__main__':
    unittest.main()