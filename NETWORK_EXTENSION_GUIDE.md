# Network Extension and Auto-Discovery Guide

This guide covers how to extend the Aave V3 Data Fetcher to support new networks and leverage automatic discovery from the aave-address-book.

## 🌐 Overview

The Aave V3 Data Fetcher supports two methods for network management:
1. **Automatic Discovery** - Fetches configurations from bgd-labs/aave-address-book
2. **Manual Configuration** - Direct configuration in the networks file

## 🔄 Automatic Network Discovery

### How It Works

The system automatically discovers new Aave V3 networks by:
1. Fetching the latest configurations from [bgd-labs/aave-address-book](https://github.com/bgd-labs/aave-address-book)
2. Parsing network configurations and contract addresses
3. Validating RPC endpoints and contract accessibility
4. Integrating new networks into the fetching process

### Configuration

Auto-discovery is enabled by default. To customize:

```python
# In src/networks.py
AUTO_DISCOVERY_CONFIG = {
    'enabled': True,
    'address_book_url': 'https://api.github.com/repos/bgd-labs/aave-address-book/contents',
    'cache_duration': 3600,  # 1 hour cache
    'fallback_on_failure': True,
    'validate_new_networks': True
}
```

### Supported Networks (2025)

The auto-discovery system currently supports these networks:

#### Tier 1 Networks (High Priority)
- **Ethereum** (Chain ID: 1) - Main network with highest TVL
- **Polygon** (Chain ID: 137) - High-volume L2 network
- **Arbitrum** (Chain ID: 42161) - Optimistic rollup
- **Optimism** (Chain ID: 10) - Optimistic rollup
- **Avalanche** (Chain ID: 43114) - High-speed blockchain

#### Tier 2 Networks (Standard Priority)
- **Base** (Chain ID: 8453) - Coinbase L2 network
- **BNB Chain** (Chain ID: 56) - Binance Smart Chain
- **Gnosis** (Chain ID: 100) - Ethereum sidechain
- **Scroll** (Chain ID: 534352) - zkEVM rollup
- **Metis** (Chain ID: 1088) - Optimistic rollup

#### Tier 3 Networks (Emerging)
- **Celo** (Chain ID: 42220) - Mobile-first blockchain
- **Mantle** (Chain ID: 5000) - Layer 2 scaling solution
- **Soneium** (Chain ID: TBD) - Sony blockchain network
- **Sonic** (Chain ID: TBD) - High-performance blockchain
- **Linea** (Chain ID: 59144) - ConsenSys zkEVM

### Testing Auto-Discovery

```bash
# Test auto-discovery functionality
python -c "from src.networks import discover_networks; print(discover_networks())"

# Validate discovered networks
python -c "from src.networks import validate_discovered_networks; print(validate_discovered_networks())"

# Force refresh of network configurations
python -c "from src.networks import refresh_address_book; refresh_address_book()"
```

## 🔧 Manual Network Addition

### Step 1: Network Configuration

Add new networks to `src/networks.py`:

```python
# Example: Adding a new network
AAVE_V3_NETWORKS = {
    # Existing networks...
    
    'new_network': {
        'rpc': 'https://rpc.new-network.com',
        'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',  # Pool contract
        'name': 'New Network Name',
        'chain_id': 12345,
        'fallback_rpcs': [
            'https://backup-rpc.new-network.com',
            'https://another-backup.new-network.com'
        ],
        'explorer': 'https://explorer.new-network.com',
        'tier': 3,  # Priority tier (1=highest, 3=lowest)
        'enabled': True
    }
}
```

### Step 2: Contract Address Discovery

Find the Aave V3 Pool contract address:

```python
# Method 1: Check aave-address-book
# Visit: https://github.com/bgd-labs/aave-address-book/tree/main/src/AaveV3NewNetwork.sol

# Method 2: Use Aave documentation
# Visit: https://docs.aave.com/developers/deployed-contracts/v3-mainnet

# Method 3: Programmatic discovery
def find_pool_address(network_name, chain_id):
    """Find Aave V3 Pool address for a network."""
    # Implementation to query address book or registry
    pass
```

### Step 3: RPC Endpoint Configuration

Configure reliable RPC endpoints:

```python
# Primary and fallback RPC endpoints
RPC_CONFIGURATION = {
    'primary': 'https://rpc.new-network.com',
    'fallbacks': [
        'https://backup1.new-network.com',
        'https://backup2.new-network.com',
        'https://public-rpc.new-network.com'
    ],
    'timeout': 30,
    'retry_count': 3,
    'rate_limit': 100  # requests per minute
}
```

### Step 4: Network Validation

Validate the new network configuration:

```bash
# Test network connectivity
python -c "
from src.networks import AAVE_V3_NETWORKS
from src.utils import rpc_call
network = AAVE_V3_NETWORKS['new_network']
result = rpc_call(network['rpc'], 'eth_blockNumber', [])
print(f'Latest block: {result}')
"

# Test Pool contract
python -c "
from src.networks import AAVE_V3_NETWORKS
from src.utils import rpc_call, get_method_id
network = AAVE_V3_NETWORKS['new_network']
method_id = get_method_id('getReservesList()')
result = rpc_call(network['rpc'], 'eth_call', [{'to': network['pool'], 'data': method_id}, 'latest'])
print(f'Reserves call result: {result}')
"
```

### Step 5: Testing and Validation

Test the new network thoroughly:

```bash
# Test specific network
python aave_fetcher.py --networks new_network --debug

# Validate data quality
python aave_fetcher.py --networks new_network --validate

# Run comprehensive tests
python test_runner.py --networks new_network --full
```

## 📊 Network Prioritization

### Tier System

Networks are organized into tiers for processing priority:

```python
NETWORK_TIERS = {
    1: ['ethereum', 'polygon', 'arbitrum', 'optimism'],  # Critical networks
    2: ['avalanche', 'base', 'bnb', 'gnosis'],          # Important networks  
    3: ['scroll', 'metis', 'celo', 'mantle']            # Emerging networks
}
```

### Processing Order

```python
def get_processing_order(networks):
    """Return networks ordered by tier priority."""
    ordered = []
    for tier in sorted(NETWORK_TIERS.keys()):
        tier_networks = [n for n in networks if n in NETWORK_TIERS[tier]]
        ordered.extend(tier_networks)
    
    # Add any networks not in tiers
    remaining = [n for n in networks if n not in ordered]
    ordered.extend(remaining)
    
    return ordered
```

## 🔍 Network Health Monitoring

### Health Check Implementation

```python
def check_network_health(network_config):
    """Comprehensive network health check."""
    health_status = {
        'network_name': network_config['name'],
        'rpc_status': 'unknown',
        'pool_contract_status': 'unknown',
        'response_time': None,
        'block_height': None,
        'last_successful_call': None,
        'error_count': 0,
        'warnings': []
    }
    
    try:
        # Test RPC connectivity
        start_time = time.time()
        block_result = rpc_call(network_config['rpc'], 'eth_blockNumber', [])
        response_time = time.time() - start_time
        
        health_status.update({
            'rpc_status': 'healthy',
            'response_time': response_time,
            'block_height': int(block_result, 16),
            'last_successful_call': datetime.utcnow().isoformat()
        })
        
        # Test Pool contract
        method_id = get_method_id('getReservesList()')
        pool_result = rpc_call(
            network_config['rpc'], 
            'eth_call', 
            [{'to': network_config['pool'], 'data': method_id}, 'latest']
        )
        
        if pool_result and pool_result != '0x':
            health_status['pool_contract_status'] = 'healthy'
        else:
            health_status['pool_contract_status'] = 'degraded'
            health_status['warnings'].append('Pool contract returned empty result')
            
    except Exception as e:
        health_status.update({
            'rpc_status': 'unhealthy',
            'error_count': 1,
            'warnings': [str(e)]
        })
    
    return health_status
```

### Automated Health Monitoring

```bash
# Check all network health
python -c "
from src.networks import get_active_networks
from src.monitoring import check_all_network_health
health_report = check_all_network_health(get_active_networks())
print(json.dumps(health_report, indent=2))
"

# Monitor specific network
python -c "
from src.networks import AAVE_V3_NETWORKS
from src.monitoring import check_network_health
status = check_network_health(AAVE_V3_NETWORKS['ethereum'])
print(json.dumps(status, indent=2))
"
```

## 🚀 2025 Network Expansion Strategy

### Expected New Networks

Based on Aave governance and ecosystem development:

#### Q1 2025
- **Mantle** - Layer 2 scaling solution with growing DeFi ecosystem
- **Linea** - ConsenSys zkEVM with strong institutional backing

#### Q2 2025
- **Soneium** - Sony's blockchain network for entertainment and gaming
- **zkSync Era** - Matter Labs zkEVM with significant TVL

#### Q3-Q4 2025
- **Sonic** - High-performance blockchain for DeFi applications
- **Additional L2s** - As ecosystem matures and governance approves

### Preparation Strategy

```python
# Pre-configure expected networks
EXPECTED_2025_NETWORKS = {
    'mantle': {
        'rpc': 'https://rpc.mantle.xyz',
        'pool': None,  # To be determined
        'name': 'Mantle Network',
        'chain_id': 5000,
        'tier': 3,
        'status': 'pending_deployment'
    },
    'soneium': {
        'rpc': 'https://rpc.soneium.org',
        'pool': None,  # To be determined
        'name': 'Soneium',
        'chain_id': None,  # To be determined
        'tier': 3,
        'status': 'pending_deployment'
    }
}
```

### Monitoring for New Deployments

```python
def monitor_new_deployments():
    """Monitor for new Aave V3 deployments."""
    # Check Aave governance proposals
    # Monitor address book updates
    # Scan for new Pool contract deployments
    # Validate new network configurations
    pass
```

## 🔧 Advanced Configuration

### Custom Network Profiles

```python
# Network-specific configurations
NETWORK_PROFILES = {
    'ethereum': {
        'multicall3_address': '0xcA11bde05977b3631167028862bE2a173976CA11',
        'batch_size': 50,
        'timeout': 60,
        'retry_count': 3
    },
    'polygon': {
        'multicall3_address': '0xcA11bde05977b3631167028862bE2a173976CA11',
        'batch_size': 100,  # Higher batch size for faster network
        'timeout': 30,
        'retry_count': 2
    },
    'arbitrum': {
        'multicall3_address': '0xcA11bde05977b3631167028862bE2a173976CA11',
        'batch_size': 75,
        'timeout': 45,
        'retry_count': 3
    }
}
```

### Dynamic RPC Management

```python
class DynamicRPCManager:
    """Manages RPC endpoints with automatic failover and health monitoring."""
    
    def __init__(self, network_config):
        self.network_config = network_config
        self.primary_rpc = network_config['rpc']
        self.fallback_rpcs = network_config.get('fallback_rpcs', [])
        self.current_rpc = self.primary_rpc
        self.health_scores = {}
    
    def get_best_rpc(self):
        """Return the best available RPC endpoint."""
        # Implementation for dynamic RPC selection
        pass
    
    def update_health_score(self, rpc_url, success, response_time):
        """Update health score for an RPC endpoint."""
        # Implementation for health scoring
        pass
```

## 📈 Performance Optimization for Multiple Networks

### Parallel Processing

```python
# Optimize for many networks
def fetch_all_networks_optimized(networks):
    """Fetch data from all networks with optimal performance."""
    
    # Tier-based processing
    tier_1_networks = [n for n in networks if get_network_tier(n) == 1]
    tier_2_networks = [n for n in networks if get_network_tier(n) == 2]
    tier_3_networks = [n for n in networks if get_network_tier(n) == 3]
    
    results = {}
    
    # Process tier 1 networks first (critical)
    with ThreadPoolExecutor(max_workers=4) as executor:
        tier_1_results = executor.map(fetch_network_data, tier_1_networks)
        results.update(dict(zip(tier_1_networks, tier_1_results)))
    
    # Process tier 2 networks
    with ThreadPoolExecutor(max_workers=6) as executor:
        tier_2_results = executor.map(fetch_network_data, tier_2_networks)
        results.update(dict(zip(tier_2_networks, tier_2_results)))
    
    # Process tier 3 networks
    with ThreadPoolExecutor(max_workers=8) as executor:
        tier_3_results = executor.map(fetch_network_data, tier_3_networks)
        results.update(dict(zip(tier_3_networks, tier_3_results)))
    
    return results
```

### Caching Strategy

```python
# Network configuration caching
NETWORK_CACHE = {
    'address_book_cache': {},
    'rpc_health_cache': {},
    'contract_address_cache': {},
    'cache_timestamps': {}
}

def get_cached_network_config(network_name):
    """Get cached network configuration."""
    cache_key = f"network_{network_name}"
    if cache_key in NETWORK_CACHE['address_book_cache']:
        timestamp = NETWORK_CACHE['cache_timestamps'].get(cache_key, 0)
        if time.time() - timestamp < 3600:  # 1 hour cache
            return NETWORK_CACHE['address_book_cache'][cache_key]
    
    # Fetch fresh configuration
    config = fetch_network_config_from_address_book(network_name)
    NETWORK_CACHE['address_book_cache'][cache_key] = config
    NETWORK_CACHE['cache_timestamps'][cache_key] = time.time()
    
    return config
```

## 🧪 Testing New Networks

### Comprehensive Test Suite

```bash
# Test new network addition
python test_new_network.py --network new_network --comprehensive

# Validate against known values
python validate_new_network.py --network new_network --compare-similar

# Performance testing
python test_network_performance.py --network new_network --benchmark
```

### Test Script Example

```python
#!/usr/bin/env python3
"""Test script for new network validation."""

def test_new_network(network_name):
    """Comprehensive test for a new network."""
    
    print(f"Testing network: {network_name}")
    
    # 1. Configuration validation
    config = AAVE_V3_NETWORKS.get(network_name)
    assert config, f"Network {network_name} not found in configuration"
    
    # 2. RPC connectivity test
    rpc_result = test_rpc_connectivity(config['rpc'])
    assert rpc_result['success'], f"RPC connectivity failed: {rpc_result['error']}"
    
    # 3. Pool contract test
    pool_result = test_pool_contract(config['pool'], config['rpc'])
    assert pool_result['success'], f"Pool contract test failed: {pool_result['error']}"
    
    # 4. Data fetching test
    data_result = test_data_fetching(network_name)
    assert data_result['success'], f"Data fetching failed: {data_result['error']}"
    
    # 5. Data validation test
    validation_result = test_data_validation(data_result['data'])
    assert validation_result['success'], f"Data validation failed: {validation_result['error']}"
    
    print(f"✅ All tests passed for {network_name}")
    return True

if __name__ == "__main__":
    import sys
    network_name = sys.argv[1] if len(sys.argv) > 1 else 'ethereum'
    test_new_network(network_name)
```

## 📚 Resources and References

### Official Documentation
- [Aave V3 Documentation](https://docs.aave.com/developers/)
- [Aave Address Book](https://github.com/bgd-labs/aave-address-book)
- [Aave Governance Forum](https://governance.aave.com/)

### Network Resources
- [Chainlist](https://chainlist.org/) - RPC endpoints and chain information
- [DefiLlama](https://defillama.com/) - Network TVL and statistics
- [L2Beat](https://l2beat.com/) - Layer 2 network information

### Development Tools
- [Multicall3 Deployments](https://github.com/mds1/multicall)
- [RPC Endpoint Lists](https://github.com/DefiLlama/chainlist)
- [Network Configuration Templates](https://github.com/ethereum-lists/chains)

---

This guide provides comprehensive coverage of network extension capabilities. The system is designed to automatically adapt to Aave V3's expansion while providing manual override capabilities for custom configurations.