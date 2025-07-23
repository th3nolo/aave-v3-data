#!/usr/bin/env python3
"""
Debug zkSync token symbol failure.
"""

import sys
sys.path.insert(0, 'src')

from utils import rpc_call, get_method_id, _decode_string_response

# zkSync token that's failing
token = '0x4d321cd88c5680ce4f85bb58c578dfe9c2cc1ef6'
rpc = 'https://mainnet.era.zksync.io'

print(f"Debugging zkSync token: {token}")
print("=" * 80)

try:
    # Get raw response
    method_id = get_method_id("symbol()")
    result = rpc_call(
        rpc,
        "eth_call",
        [{
            "to": token,
            "data": method_id
        }, "latest"]
    )
    
    if 'result' in result:
        response = result['result']
        print(f"Raw response: {response}")
        print(f"Response length: {len(response) - 2 if response.startswith('0x') else len(response)} chars")
        
        if response == '0x':
            print("→ Empty response (symbol() function doesn't exist or reverted)")
        else:
            # Try to decode
            decoded = _decode_string_response(response)
            print(f"Decoded: '{decoded}'")
            
            # Analyze the hex
            if response.startswith('0x'):
                hex_data = response[2:]
                if len(hex_data) >= 128:
                    offset = int(hex_data[:64], 16)
                    length = int(hex_data[64:128], 16)
                    print(f"→ Dynamic string: offset={offset}, length={length}")
                    
                    if length > 0 and len(hex_data) >= 128 + length * 2:
                        string_hex = hex_data[128:128 + length * 2]
                        string_bytes = bytes.fromhex(string_hex)
                        print(f"String hex: {string_hex}")
                        print(f"String bytes: {string_bytes}")
                        print(f"String repr: {repr(string_bytes)}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"Failed: {e}")

# Let's also try other standard functions
print("\nTrying other token functions...")
for func in ['name()', 'decimals()']:
    try:
        method_id = get_method_id(func)
        result = rpc_call(rpc, "eth_call", [{"to": token, "data": method_id}, "latest"])
        if 'result' in result and result['result'] != '0x':
            print(f"✅ {func}: {result['result']}")
        else:
            print(f"❌ {func}: Empty or error")
    except:
        print(f"❌ {func}: Failed")