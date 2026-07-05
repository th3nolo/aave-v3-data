# Aave V3 Data

Public Aave V3 lending-protocol data, updated daily and served as static JSON and HTML. No servers, no API keys, no rate limits.

## Overview

The dataset covers, per network:

- Lending and borrowing rates
- Reserve configurations
- Liquidity metrics
- Governance change tracking

A GitHub Actions workflow refreshes the data daily at midnight UTC and publishes it to GitHub Pages. Extended usage instructions are in [`USAGE.md`](USAGE.md).

## Features

- Updates daily at midnight UTC via GitHub Actions.
- 13 networks: Ethereum, Polygon, Arbitrum, Optimism, Base, zkSync, Avalanche, and more.
- 190+ assets with full reserve parameters.
- No authentication and no rate limits — the data is static files on GitHub Pages.
- HTML tables for reading, JSON for scripts.
- Tracks protocol parameter changes between refreshes.

---

## Access Points

| Access | URL | Use Case |
|--------|-----|----------|
| **API Explorer** | [Explore API](https://th3nolo.github.io/aave-v3-data/api/) | Search & view live endpoints |
| **Sortable Data Tables** | [View Tables](https://th3nolo.github.io/aave-v3-data/) | Quick on-page analysis |
| **Raw JSON Data** | [Download JSON](https://th3nolo.github.io/aave-v3-data/aave_v3_data.json) | Integration in scripts/apps |
| **Governance Dashboard** | [Monitor Changes](https://th3nolo.github.io/aave-v3-data/governance_monitoring.html) | Risk assessment |

---

## Example Usage

### Command-Line Query (cURL + jq)
```bash
# Fetch all data
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json -o aave_data.json

# Get USDC supply APY on Ethereum
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
jq '.networks.ethereum[] | select(.symbol=="USDC") | .current_liquidity_rate'
```

### JavaScript Example
```javascript
fetch('https://th3nolo.github.io/aave-v3-data/aave_v3_data.json')
  .then(res => res.json())
  .then(data => {
    const highLtvAssets = [];
    for (const [network, assets] of Object.entries(data.networks)) {
      for (const asset of assets) {
        if (asset.loan_to_value > 0.75) {
          highLtvAssets.push({ network, ...asset });
        }
      }
    }
    console.log(highLtvAssets);
  });
```

---

## Data Structure

Example JSON output:
```json
{
  "metadata": {
    "last_updated": "ISO_TIMESTAMP",
    "network_summary": {
      "total_active_networks": 13,
      "total_assets": 190
    }
  },
  "networks": {
    "ethereum": [
      {
        "symbol": "USDC",
        "loan_to_value": 0.75,
        "liquidation_threshold": 0.78,
        "current_liquidity_rate": 0.038,
        "current_variable_borrow_rate": 0.050,
        "supply_cap": 381,
        "borrow_cap": 63488,
        "active": true
      }
    ]
  }
}
```

---

## Installation & Development

### Requirements
- Python 3.x
- GitHub account (if self-hosting)

### Setup
```bash
git clone https://github.com/th3nolo/aave-v3-data.git
cd aave-v3-data
python aave_fetcher.py --validate
```

**Performance Options:**
- `--turbo` for maximum concurrency
- `--ultra-fast` for batch RPC calls
- `--parallel` for standard execution

---

## Governance & Risk Tracking

Stay informed about governance changes with:
- [Governance History JSON](https://th3nolo.github.io/aave-v3-data/governance_history.json)
- [Health Report JSON](https://th3nolo.github.io/aave-v3-data/health_report.json)

---

## References

- [Aave V3 Documentation](https://docs.aave.com/developers/core-contracts/pool)
- [Aave Address Book](https://github.com/bgd-labs/aave-address-book)

---

## License

MIT License – see [LICENSE](LICENSE) for details.

The `last_updated` field in the JSON metadata carries the exact refresh timestamp.
