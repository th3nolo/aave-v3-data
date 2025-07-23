#!/usr/bin/env python3
"""
Final test of symbol decoding.
"""

import sys
sys.path.insert(0, 'src')

# Test the actual decode function
from utils import _decode_string_response

def test_decode():
    test_cases = [
        {
            'name': 'MKR (bytes32)',
            'hex': '0x4d4b520000000000000000000000000000000000000000000000000000000000',
            'expected': 'MKR'
        },
        {
            'name': 'USDT Arbitrum',
            'hex': '0x00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000007555344e282ae3000000000000000000000000000000000000000000000000000',
            'expected': 'USDT'
        },
        {
            'name': 'Standard WETH',
            'hex': '0x00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000004574554480000000000000000000000000000000000000000000000000000000',
            'expected': 'WETH'
        }
    ]
    
    print("Testing symbol decoding with actual responses...")
    print("=" * 60)
    
    for test in test_cases:
        result = _decode_string_response(test['hex'])
        status = "✅" if result == test['expected'] else "❌"
        print(f"{status} {test['name']}: '{result}' (expected '{test['expected']}')")

if __name__ == "__main__":
    test_decode()