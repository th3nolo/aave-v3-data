#!/usr/bin/env python3
"""
Simple test to verify the core fetching logic works.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_reserves, get_asset_symbol, get_reserve_data
from networks import AAVE_V3_NETWORKS

def test_simple_fetch():
    """Test basic fetching without all the monitoring overhead"""
    # Test with Ethereum mainnet
    network = AAVE_V3_NETWORKS['ethereum']
    pool_address = network['pool']
    rpc_url = network['rpc']
    
    print("Testing basic fetch functionality...")
    print("=" * 60)
    print(f"Network: Ethereum Mainnet")
    print(f"Pool: {pool_address}")
    print(f"RPC: {rpc_url}")
    
    try:
        # Step 1: Get reserves list
        print("\n1. Getting reserves list...")
        reserves = get_reserves(pool_address, rpc_url, fallback_urls=[network['rpc_fallback'][0]])
        print(f"✅ Found {len(reserves)} reserves")
        
        # Step 2: Test with first reserve
        if reserves:
            asset_address = reserves[0]
            print(f"\n2. Testing with first asset: {asset_address}")
            
            # Get symbol
            print("   Getting symbol...")
            symbol = get_asset_symbol(asset_address, rpc_url, fallback_urls=[network['rpc_fallback'][0]])
            print(f"   ✅ Symbol: {symbol}")
            
            # Get reserve data
            print("   Getting reserve data...")
            reserve_data = get_reserve_data(asset_address, pool_address, rpc_url, fallback_urls=[network['rpc_fallback'][0]])
            
            # Show some data
            supply_rate = reserve_data.get('current_liquidity_rate', 0) * 100
            borrow_rate = reserve_data.get('current_variable_borrow_rate', 0) * 100
            
            print(f"   ✅ Reserve data retrieved:")
            print(f"      Supply APY: {supply_rate:.2f}%")
            print(f"      Borrow APY: {borrow_rate:.2f}%")
            print(f"      Active: {reserve_data.get('active', False)}")
            print(f"      Decimals: {reserve_data.get('decimals', 0)}")
            
            print("\n✅ ALL TESTS PASSED! The fetcher should work now.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_fetch()