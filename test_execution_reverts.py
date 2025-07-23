#!/usr/bin/env python3
"""
Quick test to check if execution revert errors are resolved.
"""

import sys
sys.path.insert(0, 'src')

from networks import AAVE_V3_NETWORKS
from utils import rpc_call

def test_pool_call(network_key, config):
    """Test a simple call to the pool contract"""
    try:
        # Simple eth_call to check if contract exists
        result = rpc_call(
            config['rpc'],
            'eth_call',
            [{
                'to': config['pool'],
                'data': '0xd1946dbc'  # getReservesList()
            }, 'latest']
        )
        
        if 'error' in result:
            error_msg = result['error'].get('message', str(result['error']))
            if 'execution reverted' in error_msg.lower():
                return False, "EXECUTION REVERTED"
            return False, error_msg
        elif 'result' in result:
            return True, "SUCCESS"
        else:
            return False, "No result"
            
    except Exception as e:
        return False, str(e)

def main():
    print("EXECUTION REVERT ERROR TEST")
    print("=" * 60)
    
    # Test the networks we fixed
    test_networks = ['celo', 'mantle', 'linea']
    
    for network_key in test_networks:
        config = AAVE_V3_NETWORKS[network_key]
        print(f"\n{config['name']} ({network_key}):")
        print(f"  Pool: {config['pool']}")
        
        success, msg = test_pool_call(network_key, config)
        if success:
            print(f"  ✅ {msg} - No execution revert!")
        else:
            print(f"  ❌ {msg}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()