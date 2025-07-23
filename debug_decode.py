#!/usr/bin/env python3
"""
Debug the decoding issue.
"""

test_response = "0x100000000000000000000103e800030d4000002c402005dc85122904206c1f7200000000000000000000000000000000000000000363ccf736f3dc523259c4e50000000000000000000000000000000000000000003aacd2e8a3582585972686000000000000000000000000000000000000000037a384c1f22e9efedeefe4600000000000000000000000000000000000000000048ba85e75584afc126cee00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006798c4580001000000000000000000004d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e80000000000000000000000004f01aed16d97e3ab5ab2b501154dc9bb0f1a5a2c000000000000000000000000d98a174936c8328596a3a6278b19e93d17d927380000000000000000000000003c613387dba0d30dc72b731aa0faca91caf1e9ef00000000000000000000000000000000000000000000000027f7d0bdb920000000000000000000000000000000000000000000000000000000000000000000000"

print(f"Original response length: {len(test_response)} chars")

# Remove 0x prefix if present
if test_response.startswith('0x'):
    hex_data = test_response[2:]
    print(f"After removing 0x: {len(hex_data)} chars")
else:
    hex_data = test_response
    print("No 0x prefix found")

# Check length
print(f"Expected length for 15 fields: {64 * 15} chars")
print(f"Actual length: {len(hex_data)} chars")
print(f"Length check passes: {len(hex_data) >= 64 * 15}")

# Count words
num_words = len(hex_data) // 64
remainder = len(hex_data) % 64
print(f"\nNumber of complete 32-byte words: {num_words}")
print(f"Remainder bytes: {remainder}")

# Show each word
print("\nWords in response:")
for i in range(num_words):
    start = i * 64
    end = start + 64
    word = hex_data[start:end]
    print(f"  Word {i:2d}: 0x{word}")