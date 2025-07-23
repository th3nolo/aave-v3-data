#!/usr/bin/env python3
"""
Test get_asset_symbol with previously failing tokens.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_asset_symbol

def test_get_asset_symbol():
    """Test that get_asset_symbol correctly decodes all problematic tokens."""
    
    test_cases = [
        ('Ethereum MKR', '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2', 'https://ethereum.publicnode.com', 'MKR'),
        ('Arbitrum USDT', '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9', 'https://arbitrum-one.publicnode.com', 'USDT'),
        ('Avalanche DAI.e', '0xd586e7f844cea2f87f50152665bcbc2c279d8d70', 'https://avalanche-c-chain-rpc.publicnode.com', 'DAI.e'),
        ('Celo USDT', '0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e', 'https://forno.celo.org', 'USDT'),
    ]
    
    print("Testing get_asset_symbol with fixed decoding...")
    print("=" * 60)
    
    all_passed = True
    
    for name, token, rpc, expected in test_cases:
        try:
            symbol = get_asset_symbol(token, rpc)
            if symbol == expected:
                print(f"✅ {name}: '{symbol}'")
            else:
                print(f"❌ {name}: '{symbol}' (expected '{expected}')")
                all_passed = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

if __name__ == "__main__":
    test_get_asset_symbol()