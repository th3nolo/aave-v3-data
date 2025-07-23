#!/usr/bin/env python3
"""Check reserves on BNB and zkSync."""

import sys
sys.path.insert(0, 'src')

from utils import get_reserves, get_method_id
from networks import AAVE_V3_NETWORKS
import requests

def check_reserves_count(network_key):
    """Check how many reserves are configured."""
    network = AAVE_V3_NETWORKS[network_key]
    
    try:
        # Try to get reserves
        reserves = get_reserves(
            network['pool'],
            network['rpc'],
            network['rpc_fallback'],
            network_key
        )
        
        print(f"\n{network['name']}:")
        print(f"  Pool address: {network['pool']}")
        print(f"  Number of reserves: {len(reserves)}")
        
        if reserves:
            print(f"  First 3 reserves:")
            for i, reserve in enumerate(reserves[:3]):
                print(f"    {i+1}. {reserve}")
        else:
            # Try calling getReservesList directly
            print("  No reserves found via getReservesList()")
            
            # Let's check if it's a different version or implementation
            # Try calling a basic function to see if contract responds
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": network['pool'],
                    "data": "0x35ea6a75"  # getReserveData(address) method signature
                }, "latest"],
                "id": 1
            }
            
            response = requests.post(network['rpc'], json=payload, timeout=10)
            result = response.json()
            
            if 'error' in result:
                print(f"  Contract error: {result['error']}")
            else:
                print(f"  Contract responds but may have different interface")
                
        return len(reserves)
        
    except Exception as e:
        print(f"\n{network['name']}: ERROR - {str(e)}")
        return 0

# Check both networks
for network in ['bnb', 'zksync']:
    check_reserves_count(network)