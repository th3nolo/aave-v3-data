#!/usr/bin/env python3
"""Diagnose why BNB and zkSync are failing."""

import sys
sys.path.insert(0, 'src')

import requests
import json
from networks import AAVE_V3_NETWORKS
from utils import get_method_id, _decode_string_response
from multicall3 import Multicall3Client

def test_basic_calls(network_key, network_config):
    """Test basic contract calls to understand the issue."""
    print(f"\n{'='*60}")
    print(f"DIAGNOSING: {network_config['name']} ({network_key})")
    print('='*60)
    
    pool_address = network_config['pool']
    data_provider = network_config['pool_data_provider']
    rpc_url = network_config['rpc']
    
    # Test 1: Get reserves list
    print("\n1. Testing getReservesList()...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": pool_address,
                "data": "0xd1946dbc"  # getReservesList()
            }, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            print(f"   ✅ Response length: {len(result['result'])} chars")
            print(f"   First 200 chars: {result['result'][:200]}...")
            
            # Try to decode manually
            data = result['result'][2:] if result['result'].startswith('0x') else result['result']
            
            # Check data structure
            if len(data) >= 128:
                offset = int(data[0:64], 16)
                length = int(data[64:128], 16)
                print(f"   Offset: {offset}, Array length: {length}")
                
                # Get first address
                if length > 0:
                    first_addr_start = 128
                    first_addr = '0x' + data[first_addr_start:first_addr_start+64][-40:]
                    print(f"   First reserve: {first_addr}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    # Test 2: Get a specific asset's symbol
    print("\n2. Testing asset symbol fetch...")
    test_asset = "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82" if network_key == 'bnb' else "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4"
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": test_asset,
                "data": "0x95d89b41"  # symbol()
            }, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            symbol = _decode_string_response(result['result'])
            print(f"   ✅ Symbol: {symbol}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    # Test 3: Get reserve data from Pool
    print("\n3. Testing Pool.getReserveData()...")
    try:
        # Encode address as 32 bytes (pad with zeros on the left)
        padded_address = test_asset[2:].zfill(64)
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": pool_address,
                "data": "0x35ea6a75" + padded_address  # getReserveData(address)
            }, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            print(f"   ✅ Response length: {len(result['result'])} chars")
            print(f"   First 256 chars: {result['result'][:256]}...")
            
            # Check structure
            data = result['result'][2:] if result['result'].startswith('0x') else result['result']
            
            # Pool.getReserveData should return 15 fields, each 32 bytes
            expected_length = 15 * 64  # 960 chars
            print(f"   Data length: {len(data)} (expected: {expected_length})")
            
            if len(data) >= 64:
                config_int = int(data[0:64], 16)
                print(f"   Configuration bitmap: {hex(config_int)}")
                
                # Try to decode LTV (first 16 bits)
                ltv = config_int & 0xFFFF
                print(f"   LTV from bitmap: {ltv} ({ltv/10000:.2%})")
                
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    # Test 4: Get reserve data from PoolDataProvider
    print("\n4. Testing PoolDataProvider.getReserveData()...")
    try:
        padded_address = test_asset[2:].zfill(64)
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": data_provider,
                "data": "0x00428472" + padded_address  # getReserveData(address)
            }, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            print(f"   ✅ Response length: {len(result['result'])} chars")
            
            # PoolDataProvider returns different structure
            data = result['result'][2:] if result['result'].startswith('0x') else result['result']
            
            # Should return 12 values, each 32 bytes
            expected_length = 12 * 64  # 768 chars
            print(f"   Data length: {len(data)} (expected: ~{expected_length})")
            
            if len(data) >= 64:
                first_value = int(data[0:64], 16)
                print(f"   First value (unbacked): {first_value}")
                
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    # Test 5: Check Multicall3
    print("\n5. Testing Multicall3 availability...")
    multicall3_addr = "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [multicall3_addr, "latest"],
            "id": 1
        }
        
        response = requests.post(rpc_url, json=payload, timeout=10)
        result = response.json()
        
        if 'result' in result:
            code = result['result']
            if code != '0x' and len(code) > 2:
                print(f"   ✅ Multicall3 deployed (code: {len(code)} chars)")
            else:
                print(f"   ❌ Multicall3 NOT deployed at standard address")
                
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

# Test both networks
for network_key in ['bnb', 'zksync']:
    network = AAVE_V3_NETWORKS[network_key]
    test_basic_calls(network_key, network)