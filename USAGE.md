# Usage Guide

This guide explains how to access and use the Aave V3 data provided by this GitHub Pages deployment.

## 🌐 Data Access Methods

### 1. HTML Interface (Human-Readable)

**URL Pattern**: `https://th3nolo.github.io/aave-v3-data/aave_v3_data.html`

**Features**:
- Responsive tables grouped by network
- Sortable columns for easy comparison
- Real-time data freshness indicators
- Mobile-friendly design
- Direct links to blockchain explorers

**Example URLs**:
```
https://johndoe.github.io/aave-data/aave_v3_data.html
https://alice.github.io/aave-v3-fetcher/aave_v3_data.html
https://defi-team.github.io/protocol-data/aave_v3_data.html
```

### 2. JSON API (Machine-Readable)

**URL Pattern**: `https://raw.githubusercontent.com/th3nolo/aave-v3-data/main/aave_v3_data.json`

**Features**:
- Structured data format
- LLM-friendly schema
- CORS-enabled for web applications
- Programmatic access
- Real-time updates

**Example URLs**:
```
https://raw.githubusercontent.com/johndoe/aave-data/main/aave_v3_data.json
https://raw.githubusercontent.com/alice/aave-v3-fetcher/main/aave_v3_data.json
https://raw.githubusercontent.com/defi-team/protocol-data/main/aave_v3_data.json
```

## 📊 Data Structure

### JSON Schema

```json
{
  "metadata": {
    "last_updated": "2025-01-21T00:00:00Z",
    "total_networks": 15,
    "total_assets": 180,
    "execution_time": 45.2,
    "data_version": "1.0"
  },
  "networks": {
    "ethereum": [
      {
        "asset_address": "0xA0b86a33E6441E6C7E8b0c3c4C0932C5C5C8C8C8",
        "symbol": "USDC",
        "liquidation_threshold": 0.78,
        "loan_to_value": 0.75,
        "liquidation_bonus": 0.05,
        "decimals": 6,
        "active": true,
        "frozen": false,
        "borrowing_enabled": true,
        "stable_borrowing_enabled": false,
        "paused": false,
        "borrowable_in_isolation": true,
        "siloed_borrowing": false,
        "reserve_factor": 0.10,
        "liquidation_protocol_fee": 0.10,
        "debt_ceiling": 0,
        "emode_category": 1,
        "liquidity_index": 1.0234,
        "variable_borrow_index": 1.0456,
        "current_liquidity_rate": 0.0234,
        "current_variable_borrow_rate": 0.0456,
        "last_update_timestamp": 1704067200,
        "a_token_address": "0x...",
        "variable_debt_token_address": "0x..."
      }
    ]
  }
}
```

### HTML Table Structure

The HTML interface displays data in organized tables with the following columns:

| Column           | Description             | Example          |
| ---------------- | ----------------------- | ---------------- |
| Symbol           | Token symbol            | USDC, WETH, WBTC |
| Asset Address    | Token contract address  | 0xA0b8...        |
| LT               | Liquidation Threshold   | 78%              |
| LTV              | Loan-to-Value ratio     | 75%              |
| LB               | Liquidation Bonus       | 5%               |
| Active           | Reserve is active       | ✅ / ❌            |
| Frozen           | Reserve is frozen       | ✅ / ❌            |
| Borrowing        | Borrowing enabled       | ✅ / ❌            |
| Stable Borrowing | Stable rate borrowing   | ✅ / ❌            |
| Paused           | Reserve is paused       | ✅ / ❌            |
| Isolation        | Borrowable in isolation | ✅ / ❌            |
| Reserve Factor   | Protocol fee            | 10%              |
| Debt Ceiling     | Maximum debt            | 1000000          |
| eMode Category   | Efficiency mode         | 1                |

## 🔧 Programmatic Usage

### JavaScript/TypeScript

```javascript
// Fetch JSON data
async function fetchAaveData() {
  const response = await fetch('https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json');
  const data = await response.json();
  
  // Access Ethereum USDC data
  const ethereumAssets = data.networks.ethereum;
  const usdcData = ethereumAssets.find(asset => asset.symbol === 'USDC');
  
  console.log(`USDC Liquidation Threshold: ${usdcData.liquidation_threshold * 100}%`);
  
  return data;
}

// Use with async/await
const aaveData = await fetchAaveData();
```

### Python

```python
import requests
import json

# Fetch JSON data
def fetch_aave_data():
    url = 'https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json'
    response = requests.get(url)
    data = response.json()
    
    # Access Polygon USDC data
    polygon_assets = data['networks']['polygon']
    usdc_data = next(asset for asset in polygon_assets if asset['symbol'] == 'USDC')
    
    print(f"USDC LT on Polygon: {usdc_data['liquidation_threshold'] * 100}%")
    
    return data

# Usage
aave_data = fetch_aave_data()
```

### cURL

```bash
# Fetch JSON data
curl -s https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json | jq .

# Get specific network data
curl -s https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json | jq '.networks.ethereum'

# Get USDC data across all networks
curl -s https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json | jq '.networks[] | map(select(.symbol == "USDC"))'
```

## 🤖 LLM Integration

### ChatGPT/Claude Usage

```
You can access current Aave V3 protocol data from:
https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json

This data includes liquidation thresholds, LTV ratios, and other parameters for all supported assets across multiple networks.

Example query: "What is the current liquidation threshold for USDC on Polygon?"
```

### API Integration

```python
# Example LLM integration
def get_liquidation_threshold(symbol, network):
    """Get liquidation threshold for a specific asset and network."""
    url = 'https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json'
    response = requests.get(url)
    data = response.json()
    
    network_assets = data['networks'].get(network, [])
    asset_data = next((asset for asset in network_assets if asset['symbol'] == symbol), None)
    
    if asset_data:
        return asset_data['liquidation_threshold']
    else:
        return None

# Usage
lt = get_liquidation_threshold('USDC', 'polygon')
print(f"USDC Polygon LT: {lt * 100}%")
```

## 📈 Data Freshness and Updates

### Update Schedule
- **Automatic**: Daily at midnight UTC
- **Manual**: On-demand via GitHub Actions
- **Frequency**: Data refreshed every 24 hours

### Data Freshness Indicators

#### JSON Metadata
```json
{
  "metadata": {
    "last_updated": "2025-01-21T00:00:00Z",
    "execution_time": 45.2,
    "data_version": "1.0"
  }
}
```

#### HTML Indicators
- Last update timestamp displayed at top of page
- Network-specific update status
- Data freshness warnings if stale

### Checking Data Age

```javascript
// Check if data is fresh (less than 25 hours old)
function isDataFresh(lastUpdated) {
  const updateTime = new Date(lastUpdated);
  const now = new Date();
  const hoursSinceUpdate = (now - updateTime) / (1000 * 60 * 60);
  
  return hoursSinceUpdate < 25; // Allow 1 hour buffer
}
```

## 🔍 Data Validation and Quality

### Validation Reports

Access validation data:
```
https://raw.githubusercontent.com/username/repo/main/validation_report.json
```

### Health Monitoring

Check system health:
```
https://raw.githubusercontent.com/username/repo/main/health_report.json
```

### Quality Indicators

- **Success Rate**: Percentage of successful network fetches
- **Data Completeness**: Assets with complete parameter sets
- **Validation Errors**: Known value mismatches
- **RPC Health**: Endpoint availability status

## 🌍 Network Coverage

### Supported Networks

| Network   | Chain ID | Status   | Assets |
| --------- | -------- | -------- | ------ |
| Ethereum  | 1        | ✅ Active | ~20    |
| Polygon   | 137      | ✅ Active | ~15    |
| Arbitrum  | 42161    | ✅ Active | ~12    |
| Optimism  | 10       | ✅ Active | ~10    |
| Avalanche | 43114    | ✅ Active | ~8     |
| Base      | 8453     | ✅ Active | ~8     |
| BNB Chain | 56       | ✅ Active | ~6     |
| Gnosis    | 100      | ✅ Active | ~5     |
| Scroll    | 534352   | ✅ Active | ~4     |
| Metis     | 1088     | ✅ Active | ~3     |

### Network-Specific Access

```javascript
// Get data for specific network
const ethereumData = data.networks.ethereum;
const polygonData = data.networks.polygon;
const arbitrumData = data.networks.arbitrum;
```

## 🔗 Integration Examples

### DeFi Dashboard Integration

```javascript
// Example: Risk dashboard integration
async function calculatePortfolioRisk(positions) {
  const aaveData = await fetchAaveData();
  
  return positions.map(position => {
    const networkData = aaveData.networks[position.network];
    const assetData = networkData.find(asset => 
      asset.asset_address.toLowerCase() === position.asset.toLowerCase()
    );
    
    return {
      ...position,
      liquidationThreshold: assetData.liquidation_threshold,
      riskLevel: position.ltv / assetData.liquidation_threshold
    };
  });
}
```

### Liquidation Bot Integration

```python
# Example: Liquidation monitoring
def check_liquidation_risk(user_positions, aave_data):
    """Check if any positions are at risk of liquidation."""
    at_risk = []
    
    for position in user_positions:
        network_data = aave_data['networks'][position['network']]
        asset_data = next(
            asset for asset in network_data 
            if asset['asset_address'].lower() == position['asset'].lower()
        )
        
        current_ltv = position['debt_value'] / position['collateral_value']
        liquidation_threshold = asset_data['liquidation_threshold']
        
        if current_ltv >= liquidation_threshold * 0.95:  # 95% of threshold
            at_risk.append({
                'position': position,
                'current_ltv': current_ltv,
                'threshold': liquidation_threshold,
                'risk_level': 'HIGH'
            })
    
    return at_risk
```

## 📱 Mobile and Web App Usage

### Responsive Design
The HTML interface is optimized for:
- Desktop browsers
- Mobile devices
- Tablet viewing
- Print formatting

### Web App Integration

```javascript
// Example: Progressive Web App integration
class AaveDataService {
  constructor(repoUrl) {
    this.baseUrl = `https://raw.githubusercontent.com/${repoUrl}/main`;
  }
  
  async getData() {
    const response = await fetch(`${this.baseUrl}/aave_v3_data.json`);
    return response.json();
  }
  
  async getHealthStatus() {
    const response = await fetch(`${this.baseUrl}/health_report.json`);
    return response.json();
  }
}

// Usage
const aaveService = new AaveDataService('username/repo');
const data = await aaveService.getData();
```

## 🆘 Troubleshooting

### Common Issues

#### Data Not Loading
- Check URL format: ensure correct username/repository
- Verify repository is public
- Check if GitHub Pages is enabled
- Confirm data files exist in repository

#### Stale Data
- Check last_updated timestamp in JSON
- Verify GitHub Actions workflow is running
- Check workflow logs for errors
- Manually trigger workflow if needed

#### CORS Issues
- Use raw.githubusercontent.com for JSON API
- Avoid accessing HTML page via JavaScript
- Consider proxy server for production apps

### Debug Tools

```javascript
// Debug data freshness
async function debugDataFreshness() {
  const response = await fetch('https://raw.githubusercontent.com/username/repo/main/aave_v3_data.json');
  const data = await response.json();
  
  console.log('Last updated:', data.metadata.last_updated);
  console.log('Data age (hours):', (Date.now() - new Date(data.metadata.last_updated)) / (1000 * 60 * 60));
  console.log('Networks:', Object.keys(data.networks));
  console.log('Total assets:', data.metadata.total_assets);
}
```

---

**Questions?** Check the main README.md or open an issue in the repository.