#!/usr/bin/env python3
"""
Test all networks to find any remaining symbol decoding failures.
"""

import sys
sys.path.insert(0, 'src')

from networks import get_active_networks
from utils import get_reserves, get_asset_symbol, get_fallback_urls

def test_all_symbols():
    """Test symbol decoding across all active networks."""
    
    networks = get_active_networks()
    print(f"Testing symbol decoding across {len(networks)} active networks...")
    print("=" * 80)
    
    all_symbols = {}
    failed_symbols = []
    
    for network_key, network_config in networks.items():
        print(f"\n{network_config['name']}:")
        
        try:
            # Get reserves
            primary_url = network_config['rpc']
            fallback_urls = get_fallback_urls(network_config)
            if fallback_urls and len(fallback_urls) > 3:
                fallback_urls = fallback_urls[:3]
            
            reserves = get_reserves(
                network_config['pool'], 
                primary_url, 
                fallback_urls
            )
            
            if not reserves:
                print(f"  ❌ No reserves found")
                continue
                
            print(f"  Found {len(reserves)} reserves")
            
            # Test each symbol
            network_symbols = []
            for asset_address in reserves[:5]:  # Test first 5 assets per network for speed
                try:
                    symbol = get_asset_symbol(asset_address, primary_url, fallback_urls)
                    network_symbols.append(symbol)
                    
                    # Check for failed decoding
                    if symbol.startswith('TOKEN_') or symbol in ['UNKNOWN', 'EMPTY', 'INVALID', 'NON_UTF8', 'DECODE_ERROR', 'PARSE_ERROR']:
                        failed_symbols.append({
                            'network': network_config['name'],
                            'asset': asset_address,
                            'symbol': symbol
                        })
                        print(f"    ❌ {asset_address}: {symbol}")
                    else:
                        print(f"    ✅ {asset_address}: {symbol}")
                        
                except Exception as e:
                    print(f"    ❌ {asset_address}: Error - {e}")
                    failed_symbols.append({
                        'network': network_config['name'],
                        'asset': asset_address,
                        'error': str(e)
                    })
            
            all_symbols[network_key] = network_symbols
            
        except Exception as e:
            print(f"  ❌ Network error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if failed_symbols:
        print(f"\n❌ Found {len(failed_symbols)} symbol decoding failures:")
        for fail in failed_symbols:
            if 'error' in fail:
                print(f"  - {fail['network']}: {fail['asset']} - {fail['error']}")
            else:
                print(f"  - {fail['network']}: {fail['asset']} -> {fail['symbol']}")
    else:
        print("\n✅ All symbols decoded successfully!")
    
    # Show active networks
    print(f"\n📊 Active networks tested: {len(networks)}")
    for network_key, network_config in networks.items():
        print(f"  - {network_config['name']}")

if __name__ == "__main__":
    test_all_symbols()