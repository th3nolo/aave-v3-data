#!/usr/bin/env python3
"""Check the actual interface of PoolDataProvider contracts."""

import sys
sys.path.insert(0, 'src')

import requests
from networks import AAVE_V3_NETWORKS

def check_contract_interface(network_key):
    """Try to understand what contract is deployed."""
    network = AAVE_V3_NETWORKS[network_key]
    provider = network['pool_data_provider']
    rpc_url = network['rpc']
    
    print(f"\n{'='*60}")
    print(f"Analyzing {network['name']} PoolDataProvider")
    print(f"Address: {provider}")
    print('='*60)
    
    # Check if it's a proxy by looking for implementation slot
    implementation_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"  # EIP-1967
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getStorageAt",
            "params": [provider, implementation_slot, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result and result['result'] != '0x0000000000000000000000000000000000000000000000000000000000000000':
            impl_addr = '0x' + result['result'][-40:]
            print(f"✅ Proxy detected! Implementation: {impl_addr}")
        else:
            print("❌ Not a standard EIP-1967 proxy")
    except Exception as e:
        print(f"❌ Error checking proxy: {e}")
    
    # Try some alternative method signatures that might work
    print("\nTrying alternative methods:")
    
    alternative_methods = {
        # Different variations of getting all tokens
        'getReservesList()': '0xd1946dbc',
        'getAssetsList()': '0x16c6fa50',
        'getTokensList()': '0xaa4f36f0',
        'assets()': '0xf11b8188',
        # Try to get address provider
        'ADDRESSES_PROVIDER()': '0x0542975c',
        'addressesProvider()': '0xc72c4d10',
        'getAddressesProvider()': '0xfe65acfe',
    }
    
    for method_name, method_sig in alternative_methods.items():
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": provider,
                    "data": method_sig
                }, "latest"],
                "id": 1
            }
            
            response = requests.post(rpc_url, json=payload, timeout=10)
            result = response.json()
            
            if 'result' in result and result['result'] != '0x' and len(result['result']) > 2:
                print(f"✅ {method_name}: {len(result['result'])} chars response")
                print(f"   Data: {result['result'][:100]}...")
            
        except:
            pass

# Check both networks
for network in ['bnb', 'zksync']:
    check_contract_interface(network)