# Aave V3 Data API

> 🚀 **Fresh Aave V3 protocol data** - lending rates, reserve configurations, liquidity metrics across all networks. Updated daily at midnight UTC via GitHub Actions.

<div align="center">
  
[![Updated Daily](https://img.shields.io/badge/Updated-Daily-brightgreen)](https://github.com/th3nolo/aave-v3-data/actions)
[![Networks](https://img.shields.io/badge/Networks-13-blue)](https://th3nolo.github.io/aave-v3-data/)
[![Assets](https://img.shields.io/badge/Assets-190+-orange)](https://th3nolo.github.io/aave-v3-data/api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### 📊 Analytics & Traffic

![Visitors](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fth3nolo%2Faave-v3-data&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=views&edge_flat=false)
![Profile Views](https://komarev.com/ghpvc/?username=th3nolo-aave-v3-data&label=Profile%20views&color=0e75b6&style=flat)
[![GitHub Clones](https://img.shields.io/badge/dynamic/json?color=success&label=Clones&query=count&url=https://github.com/th3nolo/aave-v3-data/blob/main/traffic_data/views_badge.json?raw=true&logo=github)](https://github.com/th3nolo/aave-v3-data/tree/main/traffic_data)

[📈 View Traffic Report](traffic_data/TRAFFIC_REPORT.md) • [🌍 Top Referrers](traffic_data/TRAFFIC_REPORT.md#top-referrers)

</div>

## 🌟 Access Points

| Endpoint | Description | Best For |
|----------|-------------|-----------|
| 🚀 **[API Dashboard](https://th3nolo.github.io/aave-v3-data/api/)** | Interactive API explorer with live endpoints | Quick data exploration |
| 📊 **[Data Tables](https://th3nolo.github.io/aave-v3-data/)** | Formatted HTML tables with sorting/filtering | Visual analysis |
| 🔗 **[Raw JSON](https://th3nolo.github.io/aave-v3-data/aave_v3_data.json)** | Complete dataset (CDN-backed, ~2MB) | Programmatic access |
| 🏛️ **[Governance Monitor](https://th3nolo.github.io/aave-v3-data/governance_monitoring.html)** | Track parameter changes & proposals | Risk monitoring |

## ⚡ Key Features

- **📈 Fresh Data**: Daily updates at midnight UTC via GitHub Actions
- **🌍 13 Networks**: Ethereum, Polygon, Arbitrum, Optimism, Base, zkSync & more
- **💰 190+ Assets**: Complete reserve parameters for all supported tokens
- **🔄 100% Uptime**: GitHub Pages CDN with automatic failover
- **🤖 LLM-Optimized**: Clean JSON structure perfect for AI/ML applications
- **🛡️ Health Monitoring**: Built-in validation and error reporting
- **🏛️ Governance Tracking**: Parameter changes and proposals updated daily

## 🤔 What's This?

This API provides **free access** to fresh Aave V3 lending protocol data across all supported networks, updated daily. Perfect for:

- **🏦 DeFi Developers**: Build lending aggregators, yield optimizers, or risk dashboards
- **📊 Data Analysts**: Track lending rates, TVL, and protocol health metrics
- **🤖 Trading Bots**: Monitor arbitrage opportunities across networks
- **🎓 Researchers**: Analyze DeFi lending markets and user behavior
- **💼 Risk Managers**: Track exposure and liquidation parameters

No API keys required. No rate limits. Just pure data.

## 🎯 Quick Start Examples

### 🔥 One-Liner Commands

```bash
# Get best stablecoin yields across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq -r '[.networks | to_entries[] | . as $n | .value[] | 
  select(.symbol | test("USD|DAI")) | 
  {network: $n.key, symbol, rate: (.current_liquidity_rate * 100)}] | 
  sort_by(.rate) | reverse | .[0:5] | 
  .[] | "\(.symbol) on \(.network): \(.rate | tostring[0:4])% APY"'

# Compare USDC rates on all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq -r '.networks | to_entries[] | 
  "\(.key): USDC Supply \((.value[] | 
  select(.symbol=="USDC") | .current_liquidity_rate * 100 | tostring[0:4]))% APY"' 2>/dev/null

# Find highest risk assets (LTV > 80%)
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq '[.networks | to_entries[] | .value[] | 
  select(.loan_to_value > 0.80)] | 
  sort_by(-.loan_to_value) | .[0:5] | 
  .[] | "\(.symbol): \(.loan_to_value * 100)% LTV"'
```

### 🌐 API Endpoints

```bash
# Interactive API Dashboard
open https://th3nolo.github.io/aave-v3-data/api/

# Get all data endpoints
curl https://th3nolo.github.io/aave-v3-data/api/v1/data.json

# Direct network access (example URLs)
https://th3nolo.github.io/aave-v3-data/aave_v3_data.json     # Full dataset
https://th3nolo.github.io/aave-v3-data/governance_history.json # Governance data
https://th3nolo.github.io/aave-v3-data/health_report.json      # System health
```

### 📋 Data Structure Sample

```json
{
  "metadata": {
    "last_updated": "2025-07-22T21:38:59Z",
    "network_summary": {
      "total_active_networks": 13,
      "total_assets": 190,
      "success_rate": 1.0
    }
  },
  "networks": {
    "ethereum": [
      {
        "symbol": "USDC",
        "decimals": 6,
        "loan_to_value": 0.75,
        "liquidation_threshold": 0.78,
        "liquidation_bonus": 0.045,
        "current_liquidity_rate": 0.038016,  // 3.80% APY
        "current_variable_borrow_rate": 0.050252,  // 5.03% APY
        "supply_cap": 381,
        "borrow_cap": 63488,
        "active": true,
        "frozen": false,
        "a_token_address": "0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c"
      }
      // ... more assets
    ],
    // ... more networks
  }
}
```

## 📅 Update Schedule & Reliability

### Update Frequency
- **Schedule**: Daily at midnight UTC (00:00 UTC)
- **Method**: GitHub Actions automated workflow
- **Manual Updates**: Can be triggered via workflow dispatch

### What Gets Updated
All data files are refreshed in each update cycle:
- ✅ `aave_v3_data.json` - Protocol parameters, rates, caps
- ✅ `governance_history.json` - Governance proposals and changes
- ✅ `governance_monitoring_report.json` - Parameter change tracking
- ✅ `health_report.json` - System health and validation status
- ✅ All HTML interfaces - Web views regenerated with fresh data

### Reliability Features
- **CDN Delivery**: GitHub Pages with global edge caching
- **Validation**: Schema checks and consistency tests on every update
- **Error Handling**: Failed updates don't overwrite good data
- **Monitoring**: Health reports track success rates and issues

## 🌐 Live Data Access

### HTML Interface
View formatted tables with current Aave V3 parameters:
- **GitHub Pages URL**: `https://th3nolo.github.io/aave-v3-data/aave_v3_data.html`

### JSON API
Access structured data programmatically:
- **GitHub Pages**: `https://th3nolo.github.io/aave-v3-data/aave_v3_data.json` (Recommended - CDN backed)
- **Raw GitHub**: `https://raw.githubusercontent.com/th3nolo/aave-v3-data/main/aave_v3_data.json`

## 📊 Data Coverage

The system fetches data from all major Aave V3 networks including:
- **Ethereum** - Main network with largest TVL
- **Polygon** - High-volume L2 network
- **Arbitrum** - Optimistic rollup network
- **Optimism** - Optimistic rollup network
- **Avalanche** - High-speed blockchain
- **Base** - Coinbase L2 network
- **BNB Chain** - Binance Smart Chain
- **Gnosis** - Ethereum sidechain
- **Scroll** - zkEVM rollup
- **Metis** - Optimistic rollup
- **And more** - Automatically discovers new networks

### Data Parameters

For each asset on each network, the system provides:
- **Liquidation Threshold (LT)** - Maximum LTV before liquidation
- **Loan-to-Value (LTV)** - Maximum borrowing ratio
- **Liquidation Bonus** - Liquidator incentive
- **Reserve Factor** - Protocol fee percentage
- **Supply/Borrow Caps** - Maximum amounts
- **Status Flags** - Active, frozen, borrowing enabled, etc.
- **Interest Rates** - Current supply and borrow rates
- **Token Addresses** - Asset and aToken addresses

## 🔥 Live API Examples with cURL

### 📡 Basic Data Fetching

```bash
# Get all data (warning: large file ~2MB)
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json

# Pretty print with jq
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.'

# Save to file
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json -o aave_data.json
```

### 🌐 Network Queries

```bash
# List all available networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks | keys[]'

# Output:
"arbitrum"
"avalanche"
"base"
"bnb"
"celo"
"ethereum"
"gnosis"
"linea"
"metis"
"optimism"
"polygon"
"scroll"
"zksync"

# Get all Ethereum data
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum'

# Get Polygon network summary - count total assets
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.polygon | length'
```

### 💰 Asset-Specific Queries

```bash
# Get USDC data on Ethereum
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum[] | select(.symbol=="USDC")'

# Example Output:
{
  "symbol": "USDC",
  "decimals": 6,
  "loan_to_value": 0.75,
  "liquidation_threshold": 0.78,
  "liquidation_bonus": 0.045,
  "reserve_factor": 0.1,
  "current_liquidity_rate": 0.038016,
  "current_variable_borrow_rate": 0.050252,
  "supply_cap": 381,
  "borrow_cap": 63488,
  "active": true,
  "frozen": false,
  "borrowing_enabled": true
}

# Get all USDC data across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks | to_entries[] | {network: .key, usdc: (.value[] | select(.symbol=="USDC") | {ltv: .loan_to_value, liquidation_threshold, supply_rate: .current_liquidity_rate, borrow_rate: .current_variable_borrow_rate})}'

# Find highest yield for USDC across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '[.networks | to_entries[] | {network: .key, rate: (.value[] | select(.symbol=="USDC") | .current_liquidity_rate)}] | max_by(.rate)'
```

### 📊 Risk Parameters

```bash
# Get all assets with LTV > 70% on Ethereum
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum[] | select(.loan_to_value > 0.70) | {symbol, ltv: .loan_to_value, liquidation_threshold}'

# Find assets with highest liquidation bonus (profitable for liquidators)
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '[.networks.ethereum[] | {symbol, liquidation_bonus}] | sort_by(.liquidation_bonus) | reverse | .[0:5]'

# Check frozen or paused assets
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks | to_entries[] | {network: .key, frozen: [.value[] | select(.frozen==true) | .symbol]}'
```

### 💸 Interest Rates Analysis

```bash
# Get top 5 assets by supply APY on Arbitrum
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '[.networks.arbitrum[] | {symbol, apy: .current_liquidity_rate}] | sort_by(.apy) | reverse | .[0:5]'

# Compare WETH rates across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks | to_entries[] | {network: .key, weth: (.value[] | select(.symbol=="WETH") | {supply_apy: .current_liquidity_rate, borrow_apy: .current_variable_borrow_rate})}'

# Find stablecoins with best rates
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '[.networks | to_entries[] | . as $n | .value[] | select(.symbol | test("USD|DAI|FRAX")) | {network: $n.key, symbol, rate: .current_liquidity_rate}] | sort_by(.rate) | reverse | .[0:10]'
```

### 🎯 Supply & Borrow Caps

```bash
# Find assets with supply caps on Ethereum
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum[] | select(.supply_cap > 0) | {symbol, supply_cap}'

# Get all borrow caps on Polygon
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.polygon[] | select(.borrow_cap > 0) | {symbol, borrow_cap}'
```

### 🏛️ Governance Monitoring

```bash
# Get governance monitoring data
curl -s https://th3nolo.github.io/aave-v3-data/governance_history.json | jq '.governance_posts[0:5]'

# Check recent parameter changes
curl -s https://th3nolo.github.io/aave-v3-data/governance_history.json | jq '.parameter_changes | sort_by(.timestamp) | reverse | .[0:10]'
```

### 🔧 Advanced Queries

```bash
# Count total assets across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '[.networks | to_entries[] | .value | length] | add'

# Find all LST (Liquid Staking Tokens)
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks | to_entries[] | {network: .key, lst: [.value[] | select(.symbol | test("stETH|rETH|cbETH|wstETH")) | .symbol]}'

# Export specific network data to CSV
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq -r '.networks.ethereum[] | [.symbol, .loan_to_value, .liquidation_threshold, .current_liquidity_rate, .current_variable_borrow_rate] | @csv' > ethereum_rates.csv

# Get Ethereum aToken addresses for monitoring
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum[] | {symbol, a_token_address}'
```

### 🐍 Python One-Liners

```bash
# Quick Python analysis
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f\"Total assets tracked: {sum(len(net) for net in data['networks'].values())}\")"

# Generate markdown table of rates
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('| Network | USDC Supply | USDC Borrow |')
print('|---------|-------------|-------------|')
for n,v in d['networks'].items():
    usdc=[r for r in v if r['symbol']=='USDC']
    if usdc: print(f\"| {n} | {usdc[0]['current_liquidity_rate']:.2%} | {usdc[0]['current_variable_borrow_rate']:.2%} |\")
"
```

### 💡 Pro Tips

1. **Use GitHub Pages URL** (not raw.githubusercontent.com) for better performance
2. **Add `-s` flag** to curl for silent mode
3. **Pipe to `jq` with `.` to pretty-print JSON
4. **Use `jq -r` for raw output** (no JSON quotes)
5. **Cache responses** - Data updates daily at midnight UTC, so cache for up to 24 hours
6. **Use `jq` filters** to reduce data transfer and processing

### 📱 Integration Examples

```bash
# Discord/Slack webhook notification for rate changes
WEBHOOK_URL="your_webhook_url"
RATE=$(curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum.reserves[] | select(.symbol=="USDC") | .liquidity_rate')
curl -X POST -H "Content-Type: application/json" -d "{\"content\":\"USDC supply rate on Ethereum: ${RATE}%\"}" $WEBHOOK_URL

# Cron job for monitoring
# Add to crontab: */60 * * * * /path/to/monitor_rates.sh
#!/bin/bash
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.arbitrum.reserves[] | select(.symbol=="USDC") | .liquidity_rate' > /tmp/usdc_rate.txt
```

## 🚀 Quick Setup

### Prerequisites
- GitHub account
- Public repository (required for GitHub Pages)
- No external dependencies (uses Python 3 standard library only)

### Repository Setup

1. **Create Repository**
   ```bash
   # Clone or fork this repository
   git clone https://github.com/th3nolo/aave-v3-data.git
   cd [repository-name]
   ```

2. **Configure GitHub Pages**
   - Go to repository **Settings** → **Pages**
   - Set **Source** to "Deploy from a branch"
   - Select **Branch**: `main` and **Folder**: `/ (root)`
   - Click **Save**

3. **Enable GitHub Actions**
   - Go to repository **Settings** → **Actions** → **General**
   - Set **Actions permissions** to "Allow all actions and reusable workflows"
   - Set **Workflow permissions** to "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

4. **Test Manual Execution**
   - Go to **Actions** tab
   - Select "Update Aave V3 Data" workflow
   - Click **Run workflow** → **Run workflow**

## 🔧 Local Development

### Running Locally

```bash
# Basic execution
python aave_fetcher.py

# Performance modes
python aave_fetcher.py --turbo          # Maximum performance
python aave_fetcher.py --ultra-fast     # Multicall3 optimization
python aave_fetcher.py --parallel       # Parallel processing

# With validation
python aave_fetcher.py --validate       # Validate against known values

# Custom output files
python aave_fetcher.py --output-json custom.json --output-html custom.html
```

### Performance Options

- **Turbo Mode** (`--turbo`): Maximum performance with 12 concurrent workers
- **Ultra-Fast** (`--ultra-fast`): Multicall3 optimization for batch calls
- **Parallel** (`--parallel`): Standard parallel processing (default)
- **Sequential** (`--sequential`): Fallback for debugging

### Testing and Validation

```bash
# Run with comprehensive validation
python aave_fetcher.py --validate

# Check validation results
cat validation_report.json

# Monitor performance
python aave_fetcher.py --turbo --validate
```

## 📁 Project Structure

```
├── aave_fetcher.py              # Main execution script
├── src/                         # Core modules
│   ├── networks.py             # Network configurations
│   ├── graceful_fetcher.py     # Robust data fetching
│   ├── ultra_fast_fetcher.py   # Performance-optimized fetching
│   ├── json_output.py          # JSON generation
│   ├── html_output.py          # HTML table generation
│   ├── validation.py           # Data validation
│   ├── monitoring.py           # Health monitoring
│   └── utils.py                # Utility functions
├── .github/workflows/
│   └── update-aave-data.yml    # Automated update workflow
├── tests/                      # Test suite
├── aave_v3_data.json          # Generated JSON data
├── aave_v3_data.html          # Generated HTML page
└── README.md                  # This file
```

## 🔄 Automated Updates

### GitHub Actions Workflow

The system automatically updates data daily at midnight UTC using GitHub Actions:

```yaml
# Scheduled execution
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:      # Manual triggering
```

### Workflow Features

- **Daily Updates**: Automatic execution at midnight UTC
- **Manual Triggers**: Run on-demand via GitHub Actions UI
- **Error Handling**: Graceful failure handling with detailed logs
- **Performance Monitoring**: Execution time tracking for GitHub Actions compliance
- **Automatic Deployment**: GitHub Pages rebuilds automatically on data updates

### Monitoring Workflow Status

1. **Actions Tab**: View execution history and logs
2. **Health Reports**: Check `health_report.json` for RPC endpoint status
3. **Validation Reports**: Review `validation_report.json` for data accuracy
4. **Performance Metrics**: Monitor execution times in workflow logs

## 🌐 GitHub Pages Configuration

### Repository Settings

1. **Repository Visibility**: Must be public for GitHub Pages
2. **Pages Source**: Deploy from `main` branch root directory
3. **Custom Domain** (optional): Configure in Pages settings

### Access Patterns

#### HTML Interface
```
https://th3nolo.github.io/aave-v3-data/aave_v3_data.html
```
- Human-readable tables grouped by network
- Responsive design for mobile/desktop
- Real-time data freshness indicators

#### JSON API
```
https://raw.githubusercontent.com/th3nolo/aave-v3-data/main/aave_v3_data.json
```
- Machine-readable structured data
- LLM-friendly format
- CORS-enabled for web applications

#### Example URLs
```
# HTML Interface
https://th3nolo.github.io/aave-v3-data/aave_v3_data.html

# JSON API
https://th3nolo.github.io/aave-v3-data/aave_v3_data.json

# Health Report
https://th3nolo.github.io/aave-v3-data/health_report.json

# Validation Report
https://th3nolo.github.io/aave-v3-data/validation_report.json
```

## 💻 Usage Examples

### HTML Interface Usage

The HTML interface provides human-readable tables with comprehensive data:

#### Accessing the HTML Page
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/aave_v3_data.html
```

#### Features
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Network Grouping**: Data organized by blockchain network
- **Sortable Columns**: Click headers to sort by any parameter
- **Real-time Indicators**: Data freshness and last update timestamps
- **Explorer Links**: Direct links to blockchain explorers for assets

#### Example URLs
```
# Personal deployment
https://th3nolo.github.io/aave-v3-data/aave_v3_data.html

# Team deployment
https://defi-team.github.io/protocol-monitor/aave_v3_data.html

# Organization deployment
https://mycompany.github.io/aave-v3-tracker/aave_v3_data.html
```

### JSON API Usage for LLM Integration

#### Direct API Access
```
https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO-NAME/main/aave_v3_data.json
```

#### LLM Integration Examples

##### ChatGPT/Claude Integration
```
You can access current Aave V3 protocol data from:
https://th3nolo.github.io/aave-v3-data/aave_v3_data.json

This data includes:
- Liquidation thresholds and LTV ratios for all assets
- Supply/borrow caps and current utilization
- Interest rates and protocol fees
- Asset status flags (active, frozen, borrowing enabled)
- Real-time data across 13 blockchain networks

Example queries:
- "What is the current liquidation threshold for USDC on Polygon?"
- "Compare WETH borrowing rates across Ethereum, Arbitrum, and Optimism"
- "Which assets have the highest LTV ratios on Base network?"
- "Show me all frozen assets across all networks"
```

##### Programmatic LLM Access
```python
import requests
import json

def query_aave_data_for_llm(prompt, data_url):
    """Fetch Aave data and format for LLM consumption."""
    
    # Fetch current data
    response = requests.get(data_url)
    aave_data = response.json()
    
    # Format for LLM context
    context = f"""
Current Aave V3 Protocol Data (Updated: {aave_data['metadata']['last_updated']}):

Networks: {', '.join(aave_data['networks'].keys())}
Total Assets: {aave_data['metadata']['total_assets']}

Sample Data Structure:
- Liquidation Threshold: Maximum LTV before liquidation (0-1 scale)
- Loan-to-Value: Maximum borrowing ratio (0-1 scale)  
- Supply/Borrow Caps: Maximum amounts (0 = unlimited)
- Reserve Factor: Protocol fee percentage (0-1 scale)
- Status Flags: active, frozen, borrowing_enabled, etc.

User Query: {prompt}

Please analyze the data and provide a comprehensive answer.
"""
    
    return context, aave_data

# Usage
data_url = "https://th3nolo.github.io/aave-v3-data/aave_v3_data.json"
context, data = query_aave_data_for_llm(
    "What are the safest assets to use as collateral based on liquidation thresholds?",
    data_url
)
```

#### JavaScript/Web Integration
```javascript
// Fetch and display Aave data
async function fetchAaveData() {
    const response = await fetch(
        'https://th3nolo.github.io/aave-v3-data/aave_v3_data.json'
    );
    const data = await response.json();
    
    // Example: Find highest LTV assets
    const highLtvAssets = [];
    
    for (const [network, assets] of Object.entries(data.networks)) {
        for (const asset of assets) {
            if (asset.loan_to_value > 0.75) {
                highLtvAssets.push({
                    network,
                    symbol: asset.symbol,
                    ltv: asset.loan_to_value,
                    liquidation_threshold: asset.liquidation_threshold
                });
            }
        }
    }
    
    // Sort by LTV descending
    highLtvAssets.sort((a, b) => b.ltv - a.ltv);
    
    console.log('Highest LTV Assets:', highLtvAssets.slice(0, 10));
    return highLtvAssets;
}

// Usage in web application
fetchAaveData().then(assets => {
    // Display in UI
    const container = document.getElementById('high-ltv-assets');
    assets.forEach(asset => {
        const div = document.createElement('div');
        div.innerHTML = `
            <strong>${asset.symbol}</strong> on ${asset.network}: 
            LTV ${(asset.ltv * 100).toFixed(1)}%, 
            LT ${(asset.liquidation_threshold * 100).toFixed(1)}%
        `;
        container.appendChild(div);
    });
});
```

#### Python Data Analysis
```python
import requests
import pandas as pd
import json

def analyze_aave_data():
    """Comprehensive Aave data analysis."""
    
    # Fetch data
    url = "https://th3nolo.github.io/aave-v3-data/aave_v3_data.json"
    response = requests.get(url)
    data = response.json()
    
    # Convert to DataFrame for analysis
    all_assets = []
    for network, assets in data['networks'].items():
        for asset in assets:
            asset_data = asset.copy()
            asset_data['network'] = network
            all_assets.append(asset_data)
    
    df = pd.DataFrame(all_assets)
    
    # Analysis examples
    print("=== Aave V3 Data Analysis ===")
    print(f"Total assets across all networks: {len(df)}")
    print(f"Networks: {df['network'].nunique()}")
    print(f"Unique symbols: {df['symbol'].nunique()}")
    
    # Highest LTV assets
    print("\n=== Highest LTV Assets ===")
    high_ltv = df.nlargest(10, 'loan_to_value')[['network', 'symbol', 'loan_to_value', 'liquidation_threshold']]
    print(high_ltv.to_string(index=False))
    
    # Network comparison
    print("\n=== Assets per Network ===")
    network_counts = df['network'].value_counts()
    print(network_counts.to_string())
    
    # Risk analysis
    print("\n=== Risk Analysis ===")
    df['risk_buffer'] = df['liquidation_threshold'] - df['loan_to_value']
    risky_assets = df[df['risk_buffer'] < 0.05].nsmallest(10, 'risk_buffer')
    print("Assets with smallest risk buffer (<5%):")
    print(risky_assets[['network', 'symbol', 'loan_to_value', 'liquidation_threshold', 'risk_buffer']].to_string(index=False))
    
    return df

# Usage
df = analyze_aave_data()

# Custom queries
def find_asset_across_networks(symbol):
    """Find an asset across all networks."""
    asset_data = df[df['symbol'] == symbol]
    if asset_data.empty:
        print(f"Asset {symbol} not found")
        return None
    
    print(f"\n=== {symbol} Across Networks ===")
    columns = ['network', 'loan_to_value', 'liquidation_threshold', 'reserve_factor', 'active']
    print(asset_data[columns].to_string(index=False))
    return asset_data

# Example: Find USDC across all networks
find_asset_across_networks('USDC')
```

#### cURL and Command Line Usage
```bash
# Fetch complete data
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq .

# Get specific network data
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | jq '.networks.ethereum'

# Find USDC across all networks
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq '.networks | to_entries[] | {network: .key, usdc: (.value[] | select(.symbol == "USDC") | {ltv: .loan_to_value, lt: .liquidation_threshold})}'

# Get assets with highest LTV
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq '[.networks | to_entries[] | .value[] | select(.loan_to_value > 0.75)] | sort_by(-.loan_to_value) | .[0:5]'

# Check data freshness
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq '.metadata | {last_updated, network_summary, data_version, generated_at}'

# Monitor specific asset
curl -s https://th3nolo.github.io/aave-v3-data/aave_v3_data.json | \
  jq '.networks.polygon[] | select(.symbol == "USDC") | {symbol, ltv: .loan_to_value, lt: .liquidation_threshold, active}'
```

### Advanced Integration Examples

#### Risk Monitoring Dashboard
```python
class AaveRiskMonitor:
    """Real-time Aave risk monitoring system."""
    
    def __init__(self, data_url):
        self.data_url = data_url
        self.thresholds = {
            'high_ltv': 0.80,
            'low_risk_buffer': 0.05,
            'high_utilization': 0.90
        }
    
    def fetch_current_data(self):
        """Fetch current Aave data."""
        response = requests.get(self.data_url)
        return response.json()
    
    def analyze_risk_levels(self):
        """Analyze current risk levels across all assets."""
        data = self.fetch_current_data()
        risk_analysis = {
            'high_risk_assets': [],
            'network_risk_scores': {},
            'overall_risk_score': 0
        }
        
        for network, assets in data['networks'].items():
            network_risks = []
            
            for asset in assets:
                risk_score = self.calculate_asset_risk(asset)
                network_risks.append(risk_score)
                
                if risk_score > 0.7:  # High risk threshold
                    risk_analysis['high_risk_assets'].append({
                        'network': network,
                        'symbol': asset['symbol'],
                        'risk_score': risk_score,
                        'ltv': asset['loan_to_value'],
                        'liquidation_threshold': asset['liquidation_threshold']
                    })
            
            risk_analysis['network_risk_scores'][network] = sum(network_risks) / len(network_risks)
        
        # Calculate overall risk score
        network_scores = list(risk_analysis['network_risk_scores'].values())
        risk_analysis['overall_risk_score'] = sum(network_scores) / len(network_scores)
        
        return risk_analysis
    
    def calculate_asset_risk(self, asset):
        """Calculate risk score for an asset (0-1 scale)."""
        if not asset['active'] or asset['frozen']:
            return 1.0  # Maximum risk for inactive assets
        
        ltv = asset['loan_to_value']
        lt = asset['liquidation_threshold']
        risk_buffer = lt - ltv
        
        # Risk factors
        ltv_risk = min(ltv / self.thresholds['high_ltv'], 1.0)
        buffer_risk = max(0, (self.thresholds['low_risk_buffer'] - risk_buffer) / self.thresholds['low_risk_buffer'])
        
        # Combined risk score
        return (ltv_risk * 0.6 + buffer_risk * 0.4)

# Usage
monitor = AaveRiskMonitor("https://th3nolo.github.io/aave-v3-data/aave_v3_data.json")
risk_analysis = monitor.analyze_risk_levels()

print(f"Overall Risk Score: {risk_analysis['overall_risk_score']:.2f}")
print(f"High Risk Assets: {len(risk_analysis['high_risk_assets'])}")
```

#### Liquidation Bot Integration
```python
def check_liquidation_opportunities(user_positions, aave_data_url):
    """Check for liquidation opportunities based on current parameters."""
    
    # Fetch current Aave data
    response = requests.get(aave_data_url)
    aave_data = response.json()
    
    liquidation_candidates = []
    
    for position in user_positions:
        # Find asset data
        network_data = aave_data['networks'].get(position['network'], [])
        asset_data = next(
            (asset for asset in network_data 
             if asset['asset_address'].lower() == position['collateral_asset'].lower()),
            None
        )
        
        if not asset_data:
            continue
        
        # Calculate current health factor
        current_ltv = position['debt_value'] / position['collateral_value']
        liquidation_threshold = asset_data['liquidation_threshold']
        
        health_factor = liquidation_threshold / current_ltv if current_ltv > 0 else float('inf')
        
        # Check if position is liquidatable (health factor < 1)
        if health_factor < 1.0:
            liquidation_bonus = asset_data['liquidation_bonus']
            potential_profit = position['debt_value'] * liquidation_bonus
            
            liquidation_candidates.append({
                'user': position['user'],
                'network': position['network'],
                'collateral_asset': asset_data['symbol'],
                'debt_value': position['debt_value'],
                'collateral_value': position['collateral_value'],
                'health_factor': health_factor,
                'liquidation_bonus': liquidation_bonus,
                'potential_profit': potential_profit,
                'priority': 1 / health_factor  # Lower health factor = higher priority
            })
    
    # Sort by priority (most profitable/urgent first)
    liquidation_candidates.sort(key=lambda x: x['priority'], reverse=True)
    
    return liquidation_candidates
```

## 🔍 Data Validation

### Validation Features

- **Parameter Accuracy**: Validates against known protocol values including 2025 updates
- **Consistency Checks**: Ensures data consistency across runs and networks
- **Schema Validation**: Verifies JSON structure compliance for LLM consumption
- **Network Health**: Monitors RPC endpoint availability and response times
- **2025 Updates**: Validates new supply/borrow caps and parameter changes

### Example Validation Checks

```python
# 2025 Updated known values
KNOWN_VALUES_2025 = {
    'ethereum': {
        'USDC': {'liquidation_threshold': 0.78, 'loan_to_value': 0.75},
        'WETH': {'liquidation_threshold': 0.80, 'loan_to_value': 0.80},
        'DAI': {'loan_to_value': 0.63}  # 2025 adjustment
    },
    'polygon': {
        'USDC': {'liquidation_threshold': 0.78, 'loan_to_value': 0.00},  # Disabled as collateral
        'WETH': {'liquidation_threshold': 0.80, 'loan_to_value': 0.80}
    }
}

# Consistency validation with 2025 features
def validate_asset_parameters(asset):
    """Validate asset parameters including 2025 updates."""
    assert 0 <= asset['liquidation_threshold'] <= 1
    assert 0 <= asset['loan_to_value'] <= asset['liquidation_threshold']
    assert asset['reserve_factor'] >= 0
    
    # 2025 feature validation
    if 'supply_cap' in asset:
        assert asset['supply_cap'] >= 0
    if 'borrow_cap' in asset:
        assert asset['borrow_cap'] >= 0
        assert asset['borrow_cap'] <= asset.get('supply_cap', float('inf'))
```

## 🛠️ Troubleshooting

### Common Issues

#### GitHub Pages Not Updating
1. **Repository Visibility**: Ensure repository is public (required for free GitHub Pages)
2. **Pages Configuration**: Go to Settings → Pages, verify source is set to "main" branch root
3. **Workflow Permissions**: Settings → Actions → General, set to "Read and write permissions"
4. **File Generation**: Check if `aave_v3_data.html` exists after workflow runs
5. **Build Logs**: Check Actions tab for detailed error messages

#### RPC Endpoint Failures (2025 Network Expansion Issues)
1. **Health Monitoring**: Review `health_report.json` for endpoint status and response times
2. **Network Configuration**: Check `src/networks.py` for correct RPC URLs and contract addresses
3. **Rate Limiting**: Use `--sequential` mode to reduce concurrent requests if hitting limits
4. **Fallback RPCs**: Ensure multiple backup endpoints are configured for critical networks
5. **New Network Issues**: Validate new 2025 networks (Mantle, Soneium, Sonic) have correct configurations

#### Data Validation Failures
1. **2025 Parameter Updates**: Check `validation_report.json` against updated protocol values
2. **Known Value Mismatches**: Run `python validate_2025_parameters.py --verbose` for detailed comparison
3. **Supply/Borrow Caps**: New 2025 feature may show validation errors - adjust tolerances if needed
4. **Network Expansion**: Ensure validation includes all active networks from address book
5. **Protocol Changes**: Update known values in `src/validation.py` for recent governance changes

#### Performance Issues (GitHub Actions Compliance)
1. **Execution Time**: Use `--turbo` mode for maximum performance (target <5 minutes)
2. **Network Prioritization**: Critical networks (Ethereum, Polygon, Arbitrum) processed first
3. **Multicall3 Optimization**: Use `--ultra-fast` for batch RPC calls
4. **Memory Usage**: Monitor for out-of-memory errors with large datasets
5. **Timeout Settings**: Adjust `--timeout` parameter for slow networks

#### 2025 Network Expansion Issues
1. **Auto-Discovery**: Check if new networks are automatically detected from aave-address-book
2. **Manual Addition**: Add new networks to `src/networks.py` if auto-discovery fails
3. **Contract Validation**: Verify Pool contract addresses for new deployments
4. **RPC Endpoints**: Ensure reliable RPC endpoints for new networks
5. **Governance Tracking**: Monitor Aave governance for new network approvals

### Debug Commands

```bash
# Test specific network (including 2025 networks)
python -c "from src.networks import get_active_networks; print(get_active_networks()['ethereum'])"

# Validate all network configurations
python -c "from src.networks import validate_all_networks; print(validate_all_networks())"

# Test RPC connectivity
python -c "from src.utils import rpc_call; print(rpc_call('https://rpc.ankr.com/eth', 'eth_blockNumber', []))"

# Check auto-discovery
python -c "from src.networks import discover_networks; print(discover_networks())"

# Test new 2025 networks
python aave_fetcher.py --networks mantle,soneium --debug --validate

# Validate 2025 parameter updates
python validate_2025_parameters.py --verbose

# Check governance monitoring
python governance_monitor.py

# Performance debugging
python aave_fetcher.py --sequential --debug --save-performance-report
```

### Advanced Troubleshooting

#### Network-Specific Issues
```bash
# Test individual network health
python -c "
from src.monitoring import check_network_health
from src.networks import AAVE_V3_NETWORKS
health = check_network_health(AAVE_V3_NETWORKS['ethereum'])
print(json.dumps(health, indent=2))
"

# Check RPC endpoint response times
python -c "
from src.networks import test_all_rpc_endpoints
results = test_all_rpc_endpoints()
for network, result in results.items():
    print(f'{network}: {result[\"response_time\"]:.2f}s - {result[\"status\"]}')
"
```

#### Data Quality Issues
```bash
# Validate against known protocol values
python validate_protocol_parameters.py --save-report

# Check data freshness
python aave_fetcher.py --validate-freshness

# Compare with previous run
python -c "
import json
with open('aave_v3_data.json') as f: current = json.load(f)
with open('aave_v3_data_previous.json') as f: previous = json.load(f)
print(f'Current: {len(current[\"networks\"])} networks')
print(f'Previous: {len(previous[\"networks\"])} networks')
"
```

#### Performance Analysis
```bash
# Generate detailed performance report
python aave_fetcher.py --turbo --save-performance-report --include-rpc-history

# Check execution time breakdown
python -c "
import json
with open('performance_report.json') as f: report = json.load(f)
for network, metrics in report['network_metrics'].items():
    print(f'{network}: {metrics[\"duration\"]:.1f}s ({metrics[\"assets_processed\"]} assets)')
"
```

## 📈 Performance Optimization

### Execution Modes

| Mode       | Workers | Features                  | Use Case        |
| ---------- | ------- | ------------------------- | --------------- |
| Turbo      | 12      | Multicall3 + Max parallel | Production      |
| Ultra-Fast | 8       | Multicall3 optimization   | Standard        |
| Parallel   | 4       | Standard parallel         | Development     |
| Sequential | 1       | Debugging                 | Troubleshooting |

### GitHub Actions Compliance

- **Time Limit**: 10 minutes maximum
- **Performance Target**: < 5 minutes for all networks
- **Monitoring**: Automatic performance reporting
- **Optimization**: Parallel processing with Multicall3

## 🔐 Security Considerations

- **No API Keys**: Uses free public RPC endpoints
- **Read-Only**: Only reads blockchain data, no transactions
- **Standard Libraries**: No external dependencies
- **Public Data**: All fetched data is publicly available on-chain

## 🤝 Contributing

### Adding New Networks

1. Update `src/networks.py` with new network configuration
2. Test locally with `python aave_fetcher.py --validate`
3. Submit pull request with validation results

### Extending Data Parameters

1. Modify bitmap parsing in `src/utils.py`
2. Update JSON schema in `src/json_output.py`
3. Add HTML table columns in `src/html_output.py`
4. Update validation checks in `src/validation.py`

## 📈 Analytics & Visitor Tracking

### Current Implementation

This repository uses multiple analytics solutions to track visitor engagement:

1. **HITS Badge** - Simple visitor counter showing total views
2. **GitHub Profile Views** - Tracks profile-specific views
3. **GitHub Traffic API** - Automated daily collection of detailed analytics

### Available Analytics Options

#### 🥇 For Detailed Analytics (Referrers, Geography)

**GoatCounter** (Privacy-friendly, GDPR compliant)
```markdown
![Analytics](https://YOUR-SITE.goatcounter.com/count?p=github-readme)
```
- Shows referrer sources
- Geographic distribution
- No cookies, no personal data
- Free tier available

**Plausible Analytics** (For GitHub Pages)
```html
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
```
- Real-time visitor tracking
- Referrer and country data
- Lightweight (<1KB)
- Paid service

#### 🥈 GitHub-Specific Counters

**Simple Visitor Badge**
```markdown
![Visitors](https://visitor-badge.glitch.me/badge?page_id=username.repo)
```

**Customizable Counter**
```markdown
![](https://komarev.com/ghpvc/?username=YOUR-USERNAME&style=flat-square&color=blue)
```

#### 🥉 Self-Hosted Solution

The included GitHub Action (`traffic-analytics.yml`) automatically:
- Fetches traffic data daily from GitHub API
- Stores data beyond GitHub's 14-day limit
- Generates traffic reports with referrers
- Creates custom badges

### Traffic Data Storage

Historical traffic data is stored in `/traffic_data/`:
- `traffic_history.json` - Complete historical data
- `TRAFFIC_REPORT.md` - Human-readable traffic report
- `views_badge.json` - Data for dynamic badge

### Privacy Considerations

All implemented solutions are:
- ✅ GDPR/CCPA compliant
- ✅ No cookies or personal data storage
- ✅ Transparent to users
- ✅ Open source friendly

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Related Resources

- [Aave V3 Documentation](https://docs.aave.com/developers/core-contracts/pool)
- [Aave Address Book](https://github.com/bgd-labs/aave-address-book)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Last Updated**: Automatically updated daily via GitHub Actions
**Data Freshness**: Check timestamp in JSON output for last update time