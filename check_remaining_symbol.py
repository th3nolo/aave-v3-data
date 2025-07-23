#!/usr/bin/env python3
"""
Check if there are any other symbol failures we missed.
Based on the output shared, these were the warnings:

Ethereum: 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 (MKR) ✅ Fixed
Arbitrum: 0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9 (USDT) ✅ Fixed  
Avalanche: 
  - 0xd586e7f844cea2f87f50152665bcbc2c279d8d70 (DAI.e) ✅ Fixed
  - 0x5947bb275c521040051d82396192181b413227a3 (?)
  - 0x50b7545627a5162f82a992c33b87adc75187b218 (?)
  - 0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab (?)
  - 0x63a72806098bd3d9520cc43356dd78afe5d386d9 (?)
  - 0x152b9d0fdc40c096757f570a51e494bd4b943e50 (?)
Metis:
  - 0x4c078361fc9bbb78df910800a991c7c3dd2f6ce0 (m.DAI) ✅ Fixed
  - 0xea32a96608495e54156ae48931a7c20f0dcc1a21 (?)
  - 0xbb06dca3ae6887fabf931640f67cab3e3a16f4dc (?)
Gnosis: 0x2a22f9c3b484c3629090feed35f17ff8f88f76f0 (USDC.e) ✅ Fixed
Celo: 0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e (USDT) ✅ Fixed
zkSync:
  - 0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4 (USDC.e) ✅ Fixed
  - 0x4d321cd88c5680ce4f85bb58c578dfe9c2cc1ef6 (?)
"""

import sys
sys.path.insert(0, 'src')

from utils import get_asset_symbol

# Test the remaining unknown tokens
remaining_tokens = [
    # Avalanche
    ('Avalanche', '0x5947bb275c521040051d82396192181b413227a3', 'https://avalanche-c-chain-rpc.publicnode.com'),
    ('Avalanche', '0x50b7545627a5162f82a992c33b87adc75187b218', 'https://avalanche-c-chain-rpc.publicnode.com'),
    ('Avalanche', '0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab', 'https://avalanche-c-chain-rpc.publicnode.com'),
    ('Avalanche', '0x63a72806098bd3d9520cc43356dd78afe5d386d9', 'https://avalanche-c-chain-rpc.publicnode.com'),
    ('Avalanche', '0x152b9d0fdc40c096757f570a51e494bd4b943e50', 'https://avalanche-c-chain-rpc.publicnode.com'),
    # Metis
    ('Metis', '0xea32a96608495e54156ae48931a7c20f0dcc1a21', 'https://andromeda.metis.io/?owner=1088'),
    ('Metis', '0xbb06dca3ae6887fabf931640f67cab3e3a16f4dc', 'https://andromeda.metis.io/?owner=1088'),
    # zkSync
    ('zkSync', '0x4d321cd88c5680ce4f85bb58c578dfe9c2cc1ef6', 'https://mainnet.era.zksync.io'),
]

print("Checking remaining tokens that had symbol warnings...")
print("=" * 80)

for network, token, rpc in remaining_tokens:
    try:
        symbol = get_asset_symbol(token, rpc)
        status = "✅" if not symbol.startswith('TOKEN_') else "❌"
        print(f"{status} {network} - {token}: {symbol}")
    except Exception as e:
        print(f"❌ {network} - {token}: Error - {e}")