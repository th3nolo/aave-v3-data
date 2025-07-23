#!/usr/bin/env python3
"""
Simple RPC connectivity test using only eth_chainId.
"""

import json
import urllib.request
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networks import get_active_networks

def simple_rpc_call(url, chain_id):
    """Make a simple eth_chainId call."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_chainId",
        "params": [],
        "id": 1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if 'result' in result:
            returned_chain_id = int(result['result'], 16)
            if returned_chain_id == chain_id:
                return True, f"✅ Chain ID {returned_chain_id} verified"
            else:
                return False, f"❌ Chain ID mismatch: expected {chain_id}, got {returned_chain_id}"
        else:
            return False, f"❌ No result in response: {result}"
            
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def test_networks():
    """Test first few networks with enhanced fallbacks."""
    networks = get_active_networks()
    
    print("Testing Enhanced RPC Fallbacks")
    print("=" * 50)
    
    # Test first 3 networks
    for network_key, config in list(networks.items())[:3]:
        print(f"\n🔍 Testing {config['name']} (Chain ID: {config['chain_id']})")
        
        # Test primary RPC
        success, message = simple_rpc_call(config['rpc'], config['chain_id'])
        print(f"   Primary: {message}")
        
        if success:
            continue
            
        # Test fallbacks
        fallbacks = config.get('rpc_fallback', [])
        print(f"   Testing {len(fallbacks)} fallback endpoints...")
        
        fallback_success = False
        for i, fallback_url in enumerate(fallbacks[:5]):  # Test first 5 fallbacks
            success, message = simple_rpc_call(fallback_url, config['chain_id'])
            if success:
                print(f"   Fallback {i+1}: {message}")
                fallback_success = True
                break
            else:
                print(f"   Fallback {i+1}: {message}")
        
        if not fallback_success:
            print(f"   ❌ All endpoints failed for {config['name']}")
        else:
            print(f"   ✅ Fallback successful for {config['name']}")

if __name__ == '__main__':
    test_networks()