# Aave V3 Data API – Free, Real-Time DeFi Lending Protocol Data

**Meta Title:** Aave V3 Data API – Free Daily Updated Lending Rates & Reserve Data for DeFi Developers  
**Meta Description:** Access free, real-time Aave V3 lending rates, reserve parameters, and liquidity data across 13+ blockchains. Updated daily via API & JSON. No API key required.

---

## Overview

The **Aave V3 Data API** provides **public, real-time decentralized finance (DeFi) data** from the Aave V3 lending protocol. It includes:

- Lending and borrowing rates
- Reserve configurations
- Liquidity metrics
- Governance change tracking

Data is refreshed **daily at midnight UTC** using GitHub Actions and hosted for free via GitHub Pages with a global **CDN** for speed and availability.

---

## Features

- **Daily Data Updates** – Automatic updates every 24 hours for consistency.
- **Multi-Network Coverage** – Ethereum, Polygon, Arbitrum, Optimism, Base, zkSync, Avalanche, and more.
- **190+ Assets Tracked** – Detailed reserve parameters for all assets.
- **No Keys or Rate Limits** – Fetch freely without authentication.
- **Multiple Output Formats** – HTML for visual analysis, JSON for programmatic use.
- **Governance Tracking** – Live updates on protocol parameter changes.

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

## SEO & Linking Strategy

- **Primary Keywords:** Aave V3 API, DeFi lending rates, Aave data JSON, blockchain reserve parameters, risk monitoring tools  
- **Internal Links:** Link to [`USAGE.md`](USAGE.md) for extended usage instructions.  
- **External Links:**  
  - [Aave V3 Documentation](https://docs.aave.com/developers/core-contracts/pool)  
  - [Aave Address Book](https://github.com/bgd-labs/aave-address-book)  

---

## License

MIT License – see [LICENSE](LICENSE) for details.

---

📅 **Last Updated:** Automatically refreshed daily via GitHub Actions. See JSON metadata for timestamp.
