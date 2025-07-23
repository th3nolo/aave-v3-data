#!/usr/bin/env python3
"""
Test script to identify which networks have invalid pool addresses causing execution reverts.
"""

import sys
sys.path.insert(0, 'src')

from networks import AAVE_V3_NETWORKS
from utils import rpc_call_with_retry
import json

def test_pool_contract(network_key, config):
    """Test if a pool contract is valid by trying to call getReservesList()"""
    print(f"\nTesting {config['name']} ({network_key})...")
    print(f"  Pool address: {config['pool']}")
    
    try:
        # Try to call getReservesList() on the pool contract
        # Method ID for getReservesList() is the first 8 characters of the keccak-256 hash
        method_id = '0xd1946dbc'  # getReservesList()
        
        result = rpc_call_with_retry(
            config['rpc'],
            'eth_call',
            [{
                'to': config['pool'],
                'data': method_id
            }, 'latest'],
            max_retries=1,
            fallback_urls=config.get('rpc_fallback', [])[:3]  # Use only first 3 fallbacks for speed
        )
        
        if 'error' in result:
            error_msg = result['error'].get('message', str(result['error']))
            if 'execution reverted' in error_msg.lower():
                print(f"  ❌ EXECUTION REVERTED - Invalid pool contract!")
                return False, "execution reverted"
            else:
                print(f"  ⚠️  Other error: {error_msg}")
                return False, error_msg
        elif 'result' in result and result['result'] != '0x':
            print(f"  ✅ Valid pool contract - getReservesList() succeeded")
            return True, "success"
        else:
            print(f"  ❌ Empty result - likely invalid contract")
            return False, "empty result"
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False, str(e)

def main():
    """Test all active networks for valid pool contracts"""
    print("=" * 80)
    print("AAVE V3 POOL CONTRACT VALIDATION TEST")
    print("=" * 80)
    
    results = {
        'valid': [],
        'invalid': [],
        'errors': {}
    }
    
    # Test each active network
    for network_key, config in AAVE_V3_NETWORKS.items():
        if not config.get('active', False):
            continue
            
        is_valid, error_msg = test_pool_contract(network_key, config)
        
        if is_valid:
            results['valid'].append(network_key)
        else:
            results['invalid'].append(network_key)
            results['errors'][network_key] = error_msg
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Valid pool contracts: {len(results['valid'])}")
    print(f"❌ Invalid pool contracts: {len(results['invalid'])}")
    
    if results['invalid']:
        print("\nNetworks with invalid pool addresses:")
        for network in results['invalid']:
            error = results['errors'][network]
            print(f"  - {network}: {error}")
            print(f"    Pool: {AAVE_V3_NETWORKS[network]['pool']}")
    
    # Save results
    with open('pool_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to pool_validation_results.json")
    
    return results

if __name__ == "__main__":
    main()