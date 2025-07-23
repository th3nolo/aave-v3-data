#!/usr/bin/env python3
"""
Debug Celo USDT decoding.
"""

hex_data = "555344e282ae"
print(f"Hex data: {hex_data}")

# Decode to bytes
string_bytes = bytes.fromhex(hex_data)
print(f"Raw bytes: {string_bytes}")
print(f"Raw bytes repr: {repr(string_bytes)}")

# Try UTF-8 decode
try:
    decoded = string_bytes.decode('utf-8')
    print(f"UTF-8 decoded: '{decoded}'")
    print(f"UTF-8 decoded repr: {repr(decoded)}")
    print(f"Characters: {[c for c in decoded]}")
    print(f"Ord values: {[ord(c) for c in decoded]}")
except Exception as e:
    print(f"UTF-8 decode failed: {e}")

# Try with errors='ignore'
try:
    decoded_ignore = string_bytes.decode('utf-8', errors='ignore')
    print(f"\nUTF-8 (ignore): '{decoded_ignore}'")
    print(f"UTF-8 (ignore) repr: {repr(decoded_ignore)}")
    
    # Filter ASCII only
    ascii_only = ''.join(c for c in decoded_ignore if ord(c) < 128)
    print(f"ASCII only: '{ascii_only}'")
    print(f"ASCII only repr: {repr(ascii_only)}")
except Exception as e:
    print(f"UTF-8 ignore failed: {e}")

# Test the actual symbol matching
if decoded == 'USDt₮':
    print("\n✅ Matches 'USDt₮'")
else:
    print(f"\n❌ Does not match 'USDt₮'")