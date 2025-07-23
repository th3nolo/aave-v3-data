#!/usr/bin/env python3
"""
Basic RPC connectivity test to verify our enhanced fallback endpoints work.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networks import get_active_networks
from utils import rpc_call_with_retry

def test_basic_connectivity():
    """Test basic RPC connectivity using eth_chainId call."""
    print("Testing Basic RPC Connectivity")
    print("=" * 50)
    
    networks = get_active_networks()
    results = {}
    
    for network_key, config in list(networks.items())[:3]:  # Test first 3 networks
        print(f"\nTesting {config['name']} (Chain ID: {config['chain_id']})...")
        
        try:
            # Test primary RPC with basic eth_chainId call
            result = rpc_call_with_retry(
                config['rpc'],
                'eth_chainId',
                [],
                max_retries=2,
                fallback_urls=config.get('rpc_fallback', [])[:5]  # Test first 5 fallbacks
            )
            
            if 'result' in result:
                returned_chain_id = int(result['result'], 16)
                expected_chain_id = config['chain_id']
                
                if returned_chain_id == expected_chain_id:
                    print(f"✅ {config['name']}: Chain ID verified ({returned_chain_id})")
                    results[network_key] = {
                        'status': 'success',
                        'chain_id': returned_chain_id,
                        'message': 'Chain ID verified'
                    }
                else:
                    print(f"⚠️  {config['name']}: Chain ID mismatch - expected {expected_chain_id}, got {returned_chain_id}")
                    results[network_key] = {
                        'status': 'warning',
                        'chain_id': returned_chain_id,
                        'expected_chain_id': expected_chain_id,
                        'message': 'Chain ID mismatch'
                    }
            else:
                print(f"❌ {config['name']}: No result in response")
                results[network_key] = {
                    'status': 'error',
                    'message': 'No result in response'
                }
                
        except Exception as e:
            print(f"❌ {config['name']}: {str(e)}")
            results[network_key] = {
                'status': 'error',
                'message': str(e)
            }
    
    # Save results
    with open('rpc_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to rpc_test_results.json")
    
    # Summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"\n📈 Summary: {successful}/{total} networks successful")
    
    return results

if __name__ == '__main__':
    test_basic_connectivity()