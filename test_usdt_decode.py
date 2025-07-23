#!/usr/bin/env python3
"""
Debug USDT symbol decoding.
"""

def debug_usdt():
    # USDT response from Arbitrum
    hex_data = "0x00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000007555344e282ae3000000000000000000000000000000000000000000000000000"
    
    # Remove 0x prefix if present
    if hex_data.startswith('0x'):
        hex_data = hex_data[2:]
    
    print(f"Hex data length: {len(hex_data)} chars")
    print(f"Offset (first 32 bytes): {hex_data[:64]}")
    print(f"Length (next 32 bytes): {hex_data[64:128]}")
    
    # Decode length
    length_hex = hex_data[64:128]
    string_length = int(length_hex, 16)
    print(f"String length: {string_length} bytes")
    
    # Extract string
    string_start = 128
    string_end = string_start + (string_length * 2)
    print(f"String data position: {string_start} to {string_end}")
    print(f"Actual hex data length: {len(hex_data)}")
    
    if string_end <= len(hex_data):
        string_hex = hex_data[string_start:string_end]
        print(f"String hex: {string_hex}")
        
        # Decode
        string_bytes = bytes.fromhex(string_hex)
        print(f"Raw bytes: {string_bytes}")
        print(f"Raw bytes hex: {string_bytes.hex()}")
        
        # Try different decodings
        try:
            utf8 = string_bytes.decode('utf-8')
            print(f"UTF-8 decoded: '{utf8}'")
        except Exception as e:
            print(f"UTF-8 decode failed: {e}")
            
        try:
            utf8_ignore = string_bytes.decode('utf-8', errors='ignore')
            print(f"UTF-8 (ignore errors): '{utf8_ignore}'")
            
            # Filter ASCII only
            ascii_only = ''.join(c for c in utf8_ignore if ord(c) < 128)
            print(f"ASCII only: '{ascii_only}'")
        except Exception as e:
            print(f"UTF-8 ignore failed: {e}")

if __name__ == "__main__":
    debug_usdt()