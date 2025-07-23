#!/usr/bin/env python3
"""
Test script to debug reserve data response format.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_method_id, rpc_call

def test_reserve_data_call():
    """Test getReserveData call to understand response format"""
    # Test with Ethereum mainnet WETH
    pool_address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    rpc_url = "https://ethereum.publicnode.com"
    
    print("Testing getReserveData call...")
    print("=" * 80)
    print(f"Pool: {pool_address}")
    print(f"Asset: {weth_address} (WETH)")
    
    try:
        # Get method ID and encode parameters
        method_id = get_method_id("getReserveData(address)")
        # Encode the asset address parameter (32 bytes padded)
        encoded_address = weth_address[2:].zfill(64)  # Remove 0x and pad to 64 chars
        call_data = method_id + encoded_address
        
        print(f"\nMethod ID: {method_id}")
        print(f"Encoded address: 0x{encoded_address}")
        print(f"Full call data: {call_data}")
        
        # Make RPC call
        result = rpc_call(
            rpc_url,
            "eth_call",
            [{
                "to": pool_address,
                "data": call_data
            }, "latest"]
        )
        
        if 'error' in result:
            print(f"\n❌ RPC Error: {result['error']}")
            return
        elif 'result' in result:
            response = result['result']
            print(f"\n✅ Got response!")
            print(f"Response length: {len(response)} chars (including 0x)")
            print(f"Response bytes: {(len(response) - 2) // 2} bytes")
            print(f"Response 32-byte words: {(len(response) - 2) // 64} words")
            
            # Show all words
            print(f"\nAll words of response:")
            if response.startswith('0x'):
                hex_data = response[2:]
                for i in range(len(hex_data) // 64):
                    word = hex_data[i*64:(i+1)*64]
                    print(f"  Word {i:2d}: 0x{word}")
            
            # Also print the full response for copying
            print(f"\nFull response (for testing):")
            print(response)
            
            # Check if it looks like a struct or dynamic data
            print(f"\nAnalysis:")
            if len(response) > 2:
                # Check if first word looks like an offset (typically 0x20 for dynamic data)
                first_word = response[2:66] if len(response) >= 66 else response[2:]
                if first_word == "0" * 63 + "20":
                    print("  ⚠️  First word is 0x20 - this looks like DYNAMIC DATA (offset pointer)")
                    print("  The actual struct data starts after the offset")
                else:
                    print("  This looks like direct struct data")
            
            return response
        else:
            print(f"\n❌ Unexpected response: {result}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reserve_data_call()