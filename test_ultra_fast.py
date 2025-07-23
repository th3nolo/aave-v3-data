#!/usr/bin/env python3
"""Test ultra fast fetcher for BNB and zkSync."""

import sys
sys.path.insert(0, 'src')

from networks import AAVE_V3_NETWORKS
from ultra_fast_fetcher import UltraFastFetcher

# Test with ultra fast fetcher
fetcher = UltraFastFetcher()

for network_key in ['bnb', 'zksync']:
    print(f"\n{'='*60}")
    print(f"Testing {network_key.upper()} with Ultra Fast Fetcher")
    print('='*60)
    
    network = AAVE_V3_NETWORKS[network_key]
    
    try:
        # Use the ultra fast fetch method
        data = fetcher.fetch_network_ultra_fast(network_key, network)
        
        if data:
            print(f"✅ SUCCESS: Fetched {len(data)} assets")
            # Show first asset
            if data:
                first = data[0]
                print(f"\nFirst asset:")
                print(f"  Symbol: {first.get('symbol', 'N/A')}")
                print(f"  Address: {first.get('asset_address', 'N/A')}")
        else:
            print(f"❌ FAILED: No data returned")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

print(f"\n\nStats:")
print(f"  Multicall3 successes: {fetcher.stats['multicall3_success']}")
print(f"  Batch RPC successes: {fetcher.stats['batch_rpc_success']}")
print(f"  Fallback used: {fetcher.stats['fallback_used']}")

fetcher.close()