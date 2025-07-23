#!/usr/bin/env python3
"""
Test script to verify the method ID fix resolves execution reverts.
"""

import sys
sys.path.insert(0, 'src')

from utils import get_method_id, rpc_call

def test_method_id_generation():
    """Test that method IDs are now correct"""
    print("Testing method ID generation...")
    print("=" * 60)
    
    test_cases = [
        ("getReservesList()", "0xd1946dbc"),
        ("symbol()", "0x95d89b41"),
        ("getReserveData(address)", "0x35ea6a75"),
    ]
    
    all_passed = True
    for signature, expected in test_cases:
        try:
            actual = get_method_id(signature)
            passed = actual == expected
            all_passed &= passed
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{signature:25} Expected: {expected}  Actual: {actual}  {status}")
        except Exception as e:
            print(f"{signature:25} ❌ ERROR: {e}")
            all_passed = False
    
    return all_passed

def test_simple_rpc_call():
    """Test a simple RPC call to Ethereum mainnet"""
    print("\n\nTesting RPC call to Ethereum mainnet...")
    print("=" * 60)
    
    # Test parameters
    ethereum_pool = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    rpc_url = "https://ethereum.publicnode.com"
    
    try:
        # Get method ID
        method_id = get_method_id("getReservesList()")
        print(f"Method ID for getReservesList(): {method_id}")
        
        # Make RPC call
        result = rpc_call(
            rpc_url,
            "eth_call",
            [{
                "to": ethereum_pool,
                "data": method_id
            }, "latest"]
        )
        
        if 'error' in result:
            print(f"❌ RPC Error: {result['error']}")
            return False
        elif 'result' in result:
            print(f"✅ SUCCESS! Got result: {result['result'][:66]}...")
            return True
        else:
            print(f"❌ Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run all tests"""
    print("AAVE V3 METHOD ID FIX TEST")
    print("=" * 80)
    
    # Test 1: Method ID generation
    method_id_ok = test_method_id_generation()
    
    # Test 2: RPC call
    rpc_ok = test_simple_rpc_call()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Method ID Generation: {'✅ PASSED' if method_id_ok else '❌ FAILED'}")
    print(f"RPC Call Test:        {'✅ PASSED' if rpc_ok else '❌ FAILED'}")
    print(f"\nOverall:              {'✅ ALL TESTS PASSED' if method_id_ok and rpc_ok else '❌ SOME TESTS FAILED'}")
    
    return method_id_ok and rpc_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)