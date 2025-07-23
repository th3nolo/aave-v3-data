#!/usr/bin/env python3
"""Check assets with validation warnings."""

import json

# Load the data
with open('aave_v3_data.json', 'r') as f:
    full_data = json.load(f)
    data = full_data.get('aave_v3_data', {})

# Assets mentioned in warnings
warning_assets = {
    'avalanche': ['WBTC.e', 'FRAX', 'MAI'],
    'optimism': ['sUSD', 'MAI'],
    'ethereum': ['LUSD', 'FRAX', 'STG', 'KNC', 'FXS'],
    'arbitrum': ['EURS', 'MAI', 'FRAX'],
    'polygon': ['DAI', 'USDC', 'CRV', 'SUSHI', 'GHST', 'BAL', 'DPI', 'miMATIC', 'stMATIC']
}

print("Assets with zero LTV but non-zero LT:")
print("=" * 60)

for network, symbols in warning_assets.items():
    if network in data:
        print(f"\n{network.upper()}:")
        for asset in data[network]:
            if asset['symbol'] in symbols:
                ltv = asset.get('loan_to_value', 0)
                lt = asset.get('liquidation_threshold', 0)
                frozen = asset.get('frozen', False)
                borrowing = asset.get('borrowing_enabled', False)
                
                if ltv == 0 and lt > 0:
                    print(f"  {asset['symbol']:10} LTV: {ltv}, LT: {lt:.3f}, Frozen: {frozen}, Borrowing: {borrowing}")

print("\n\nThis configuration is VALID in Aave V3:")
print("- LTV = 0: Asset cannot be used as collateral for new borrows")
print("- LT > 0: Existing positions can still be liquidated")
print("- Common for: deprecated assets, risky assets, or assets being phased out")