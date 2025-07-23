#!/usr/bin/env python3
"""Check if Aave is actually deployed on BNB and zkSync."""

import requests
import json
from src.networks import AAVE_V3_NETWORKS

def check_contract(network_name, rpc_url, pool_address):
    """Check if a contract exists at the given address."""
    try:
        # Check if contract exists by calling eth_getCode
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [pool_address, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            code = result['result']
            # If code is '0x' or '0x0', no contract exists
            has_contract = code != '0x' and code != '0x0' and len(code) > 2
            print(f"{network_name}: Contract {'EXISTS' if has_contract else 'NOT FOUND'} at {pool_address}")
            if has_contract:
                print(f"  Code length: {len(code)} characters")
            return has_contract
        else:
            print(f"{network_name}: RPC error - {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"{network_name}: Connection error - {str(e)}")
        return False

# Check BNB and zkSync
for network_key in ['bnb', 'zksync']:
    network = AAVE_V3_NETWORKS[network_key]
    print(f"\nChecking {network['name']}...")
    check_contract(
        network['name'],
        network['rpc'],
        network['pool']
    )