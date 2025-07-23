#!/usr/bin/env python3
"""
Test to verify the method ID generation issue.
"""

import hashlib

def wrong_method_id(signature: str) -> str:
    """Current implementation using SHA3-256 (WRONG)"""
    keccak = hashlib.sha3_256()
    keccak.update(signature.encode('utf-8'))
    return '0x' + keccak.hexdigest()[:8]

def correct_method_id_web3(signature: str) -> str:
    """Correct implementation using Web3.py"""
    try:
        from web3 import Web3
        return Web3.keccak(text=signature).hex()[:10]  # 0x + 8 chars
    except ImportError:
        return "Web3 not installed"

def correct_method_id_pycryptodome(signature: str) -> str:
    """Correct implementation using pycryptodome"""
    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(signature.encode('utf-8'))
        return '0x' + k.hexdigest()[:8]
    except ImportError:
        return "pycryptodome not installed"

# Test with getReservesList()
signature = "getReservesList()"
print(f"Testing method ID generation for: {signature}")
print("=" * 60)

print(f"Current (WRONG) implementation: {wrong_method_id(signature)}")
print(f"Correct (Web3.py):              {correct_method_id_web3(signature)}")
print(f"Correct (pycryptodome):         {correct_method_id_pycryptodome(signature)}")

# The correct method ID for getReservesList() should be 0xd1946dbc
print(f"\nExpected correct value:         0xd1946dbc")

# Test with another known function
signature2 = "symbol()"
print(f"\n\nTesting method ID generation for: {signature2}")
print("=" * 60)
print(f"Current (WRONG) implementation: {wrong_method_id(signature2)}")
print(f"Correct (Web3.py):              {correct_method_id_web3(signature2)}")
print(f"Correct (pycryptodome):         {correct_method_id_pycryptodome(signature2)}")
print(f"\nExpected correct value:         0x95d89b41")