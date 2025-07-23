#!/usr/bin/env python3
"""
Test symbol decoding for all failing tokens.
"""

import sys
sys.path.insert(0, 'src')

from utils import rpc_call, get_method_id, _decode_string_response

def test_failing_symbols():
    """Test all tokens that are failing symbol decoding."""
    
    failing_tokens = [
        # Ethereum
        {
            'network': 'Ethereum',
            'token': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2',
            'rpc': 'https://ethereum.publicnode.com',
            'expected': 'MKR'
        },
        # Arbitrum
        {
            'network': 'Arbitrum',
            'token': '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',
            'rpc': 'https://arbitrum-one.publicnode.com',
            'expected': 'USDT'
        },
        # Avalanche
        {
            'network': 'Avalanche',
            'token': '0xd586e7f844cea2f87f50152665bcbc2c279d8d70',
            'rpc': 'https://avalanche-c-chain-rpc.publicnode.com',
            'expected': 'DAI'
        },
        # Metis
        {
            'network': 'Metis',
            'token': '0x4c078361fc9bbb78df910800a991c7c3dd2f6ce0',
            'rpc': 'https://andromeda.metis.io/?owner=1088',
            'expected': 'UNKNOWN'
        },
        # Gnosis
        {
            'network': 'Gnosis',
            'token': '0x2a22f9c3b484c3629090feed35f17ff8f88f76f0',
            'rpc': 'https://gnosis-rpc.publicnode.com',
            'expected': 'UNKNOWN'
        },
        # Celo
        {
            'network': 'Celo',
            'token': '0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e',
            'rpc': 'https://forno.celo.org',
            'expected': 'UNKNOWN'
        },
        # zkSync
        {
            'network': 'zkSync',
            'token': '0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4',
            'rpc': 'https://mainnet.era.zksync.io',
            'expected': 'USDC'
        }
    ]
    
    print("Testing Symbol Decoding for Failing Tokens")
    print("=" * 80)
    
    for token_info in failing_tokens:
        print(f"\n{token_info['network']} - {token_info['token']}")
        
        try:
            # Get raw response
            method_id = get_method_id("symbol()")
            result = rpc_call(
                token_info['rpc'],
                "eth_call",
                [{
                    "to": token_info['token'],
                    "data": method_id
                }, "latest"]
            )
            
            if 'result' in result:
                response = result['result']
                print(f"Raw response: {response}")
                
                # Try to decode
                decoded = _decode_string_response(response)
                print(f"Decoded: '{decoded}'")
                
                # Show hex breakdown
                if response != '0x':
                    hex_data = response[2:] if response.startswith('0x') else response
                    print(f"Response length: {len(hex_data)} chars")
                    
                    if len(hex_data) == 64:
                        print("→ bytes32 format detected")
                    elif len(hex_data) >= 128:
                        offset = int(hex_data[:64], 16)
                        length = int(hex_data[64:128], 16)
                        print(f"→ Dynamic string: offset={offset}, length={length}")
                        
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_failing_symbols()