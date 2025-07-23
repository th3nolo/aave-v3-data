#!/usr/bin/env python3
"""
Test decoding of actual reserve data response.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_reserve_data

def test_decode():
    """Test decoding with actual response data"""
    # Use the response we got from test_reserve_data.py
    test_response = "0x100000000000000000000103e800030d4000002c402005dc85122904206c1f7200000000000000000000000000000000000000000363cd081dd1e2bacff37b07000000000000000000000000000000000000000000397d9802dcd86d8272c40b0000000000000000000000000000000000000000037a38619cd59e920756220c0000000000000000000000000000000000000000004747b7084a02f06e3ea493000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000687d593b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000004d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8000000000000000000000000102633152313c81cd80419b6ecf66d14ad68949a000000000000000000000000ea51d7853eefb32b6ee06b1c12e6dcca88be0ffe0000000000000000000000009ec6f08190dea04a54f8afc53db96134e5e3fdfb0000000000000000000000000000000000000000000000016af697445e18bfa300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    
    print("Testing reserve data decoding...")
    print("=" * 80)
    
    # Test parameters
    pool_address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    
    try:
        # Import the decode function directly
        from utils import _decode_reserve_data_response
        
        # Try to decode
        decoded = _decode_reserve_data_response(test_response)
        
        print("✅ Decoding successful!")
        print("\nDecoded data:")
        
        # Print key fields
        for key, value in decoded.items():
            # Format addresses nicely
            if 'address' in key:
                print(f"  {key}: {value}")
            # Format rates as percentages
            elif 'rate' in key and isinstance(value, (int, float)):
                print(f"  {key}: {value * 100:.4f}%")
            # Format indices
            elif 'index' in key and isinstance(value, (int, float)):
                print(f"  {key}: {value:.6f}")
            else:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Decoding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_decode()