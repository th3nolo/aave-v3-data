#!/usr/bin/env python3
"""Test different PoolDataProvider methods."""

import sys
sys.path.insert(0, 'src')

import requests
from networks import AAVE_V3_NETWORKS

def test_provider_methods(network_key):
    """Test various PoolDataProvider method signatures."""
    network = AAVE_V3_NETWORKS[network_key]
    provider = network['pool_data_provider']
    rpc_url = network['rpc']
    test_asset = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82" if network_key == 'bnb' else "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4"
    
    print(f"\n{'='*60}")
    print(f"Testing PoolDataProvider methods on {network['name']}")
    print(f"Provider: {provider}")
    print(f"Test asset: {test_asset}")
    print('='*60)
    
    # Method signatures to test
    methods = {
        'getReserveData(address)': '0x00428472',
        'getReserveConfigurationData(address)': '0x3e150141',
        'getReserveTokensAddresses(address)': '0xd2493b6c',
        'getAllReservesTokens()': '0xb316ff89',
        'getAllATokens()': '0xf561ae41',
        'getReserveDataLegacy(address)': '0x35ea6a75',  # Old method
    }
    
    for method_name, method_sig in methods.items():
        print(f"\n{method_name} ({method_sig}):")
        
        try:
            # Prepare call data
            if 'address' in method_name:
                # Need to pass asset address
                call_data = method_sig + test_asset[2:].zfill(64)
            else:
                # No parameters
                call_data = method_sig
            
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{
                    "to": provider,
                    "data": call_data
                }, "latest"],
                "id": 1
            }
            
            response = requests.post(rpc_url, json=payload, timeout=10)
            result = response.json()
            
            if 'result' in result:
                data = result['result']
                if data == '0x' or len(data) <= 2:
                    print(f"   ❌ Empty response")
                else:
                    print(f"   ✅ Response: {len(data)} chars")
                    print(f"      First 100 chars: {data[:100]}...")
                    
                    # Special handling for getAllReservesTokens
                    if 'getAllReservesTokens' in method_name:
                        # Try to decode the array
                        hex_data = data[2:] if data.startswith('0x') else data
                        if len(hex_data) >= 128:
                            offset = int(hex_data[0:64], 16)
                            length = int(hex_data[64:128], 16)
                            print(f"      Array length: {length} tokens")
            else:
                error = result.get('error', {})
                print(f"   ❌ RPC Error: {error.get('message', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

# Test both networks
for network in ['bnb', 'zksync']:
    test_provider_methods(network)