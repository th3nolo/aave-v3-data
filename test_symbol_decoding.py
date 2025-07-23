#!/usr/bin/env python3
"""
Test why symbol decoding fails for specific tokens.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_asset_symbol, rpc_call, get_method_id

def test_symbol_decoding():
    """Test symbol decoding for problematic tokens."""
    
    # Tokens that failed
    test_cases = [
        {
            'network': 'Ethereum',
            'token': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
            'name': 'MKR (MakerDAO)',
            'rpc': 'https://ethereum.publicnode.com'
        },
        {
            'network': 'Arbitrum',
            'token': '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',
            'name': 'USDT',
            'rpc': 'https://arbitrum-one.publicnode.com'
        }
    ]
    
    print("Testing Symbol Decoding Issues")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n{test['network']} - {test['name']}")
        print(f"Token: {test['token']}")
        
        # Try to get symbol using our function
        try:
            symbol = get_asset_symbol(test['token'], test['rpc'])
            print(f"✅ Symbol retrieved: {symbol}")
        except Exception as e:
            print(f"❌ get_asset_symbol failed: {e}")
        
        # Try raw RPC call to understand the issue
        try:
            method_id = get_method_id("symbol()")
            result = rpc_call(
                test['rpc'],
                "eth_call",
                [{
                    "to": test['token'],
                    "data": method_id
                }, "latest"]
            )
            
            if 'error' in result:
                print(f"❌ RPC Error: {result['error']}")
            elif 'result' in result:
                print(f"Raw response: {result['result']}")
                
                # Analyze the response
                if result['result'] == '0x':
                    print("  → Empty response (function doesn't exist)")
                else:
                    # Try to decode
                    hex_data = result['result'][2:] if result['result'].startswith('0x') else result['result']
                    print(f"  → Response length: {len(hex_data)} chars")
                    
                    # MKR returns bytes32 instead of string
                    if len(hex_data) == 64:
                        # Try to decode as bytes32
                        try:
                            # Remove trailing zeros
                            trimmed = hex_data.rstrip('0')
                            if trimmed:
                                decoded = bytes.fromhex(trimmed).decode('utf-8', errors='ignore')
                                print(f"  → Decoded as bytes32: '{decoded}'")
                        except:
                            print("  → Failed to decode as bytes32")
                    
                    # Show the raw hex for analysis
                    print(f"  → First 32 bytes: 0x{hex_data[:64]}")
                    
        except Exception as e:
            print(f"❌ Raw RPC call failed: {e}")

if __name__ == "__main__":
    test_symbol_decoding()