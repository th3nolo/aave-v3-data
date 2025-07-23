# Comprehensive Troubleshooting Guide

This guide provides detailed solutions for common issues encountered when deploying and running the Aave V3 Data Fetcher, with special focus on 2025 network expansions and RPC challenges.

## 🚨 Critical Issues

### GitHub Pages Deployment Failures

#### Issue: "Pages build and deployment" Failed
**Symptoms:**
- GitHub Pages shows red X for deployment
- HTML page returns 404 error
- Error message: "The page build failed for the `main` branch"

**Root Causes & Solutions:**

1. **Repository Not Public**
   ```bash
   # Check repository visibility
   # Go to Settings → General → Danger Zone
   # If private, click "Change visibility" → "Make public"
   ```
   
2. **Invalid HTML File**
   ```bash
   # Check if HTML file exists and is valid
   ls -la aave_v3_data.html
   
   # Validate HTML structure
   python -c "
   import os
   if os.path.exists('aave_v3_data.html'):
       with open('aave_v3_data.html', 'r') as f:
           content = f.read()
           if '<html' in content and '</html>' in content:
               print('✅ HTML file appears valid')
           else:
               print('❌ HTML file may be corrupted')
   else:
       print('❌ HTML file not found')
   "
   ```

3. **File Size Too Large**
   ```bash
   # Check file sizes (GitHub Pages has limits)
   ls -lh aave_v3_data.html aave_v3_data.json
   
   # If HTML > 100MB, optimize generation
   python aave_fetcher.py --compact-html
   ```

4. **Pages Configuration Issues**
   ```yaml
   # Verify Pages settings
   # Settings → Pages
   # Source: "Deploy from a branch"
   # Branch: main
   # Folder: / (root)
   ```

#### Issue: Workflow Permissions Error
**Symptoms:**
- Error: "Resource not accessible by integration"
- Error: "Permission denied to write to repository"
- Files not committed after workflow runs

**Solutions:**

1. **Fix Workflow Permissions**
   ```yaml
   # Go to Settings → Actions → General
   # Workflow permissions: "Read and write permissions"
   # ✅ "Allow GitHub Actions to create and approve pull requests"
   ```

2. **Check Token Permissions**
   ```yaml
   # In workflow file, ensure proper permissions
   permissions:
     contents: write
     pages: write
     id-token: write
   ```

3. **Verify Repository Settings**
   ```bash
   # Ensure Actions are enabled
   # Settings → Actions → General
   # Actions permissions: "Allow all actions and reusable workflows"
   ```

## 🌐 RPC Endpoint Issues (2025 Network Expansion)

### High RPC Failure Rates

#### Issue: Multiple Networks Failing
**Symptoms:**
- health_report.json shows low success rates
- Missing data for multiple networks
- Timeout errors in workflow logs

**Diagnosis:**
```bash
# Check RPC health across all networks
python -c "
from src.networks import test_all_rpc_endpoints
import json
results = test_all_rpc_endpoints()
for network, result in results.items():
    status = '✅' if result['success'] else '❌'
    print(f'{status} {network}: {result.get(\"response_time\", \"N/A\")}s - {result.get(\"error\", \"OK\")}')
"
```

**Solutions:**

1. **Add More Fallback RPCs**
   ```python
   # In src/networks.py, expand fallback options
   'ethereum': {
       'rpc': 'https://rpc.ankr.com/eth',
       'fallback_rpcs': [
           'https://eth.llamarpc.com',
           'https://ethereum.publicnode.com',
           'https://eth.rpc.blxrbdn.com',
           'https://rpc.payload.de',
           'https://eth.merkle.io'
       ]
   }
   ```

2. **Implement Rate Limiting**
   ```python
   # Add rate limiting configuration
   RPC_RATE_LIMITS = {
       'ethereum': {'requests_per_minute': 60, 'burst_limit': 10},
       'polygon': {'requests_per_minute': 100, 'burst_limit': 20},
       'arbitrum': {'requests_per_minute': 80, 'burst_limit': 15}
   }
   ```

3. **Use Sequential Mode for Debugging**
   ```bash
   # Reduce concurrent load
   python aave_fetcher.py --sequential --timeout 120 --debug
   ```

#### Issue: New 2025 Networks Not Working
**Symptoms:**
- Mantle, Soneium, Sonic networks failing
- "Contract not found" errors
- Invalid RPC responses

**Solutions:**

1. **Verify Network Configurations**
   ```python
   # Test new network configurations
   NEW_2025_NETWORKS = ['mantle', 'soneium', 'sonic']
   
   for network in NEW_2025_NETWORKS:
       if network in AAVE_V3_NETWORKS:
           config = AAVE_V3_NETWORKS[network]
           print(f"Testing {network}:")
           print(f"  RPC: {config['rpc']}")
           print(f"  Pool: {config['pool']}")
           
           # Test RPC connectivity
           try:
               result = rpc_call(config['rpc'], 'eth_blockNumber', [])
               print(f"  ✅ RPC working: block {int(result, 16)}")
           except Exception as e:
               print(f"  ❌ RPC failed: {e}")
   ```

2. **Update Contract Addresses**
   ```bash
   # Check latest deployments from address book
   python -c "
   from src.networks import refresh_address_book
   refresh_address_book()
   print('Address book refreshed')
   "
   ```

3. **Validate Pool Contracts**
   ```python
   # Test Pool contract calls
   def test_pool_contract(network_name):
       config = AAVE_V3_NETWORKS[network_name]
       method_id = get_method_id('getReservesList()')
       
       try:
           result = rpc_call(
               config['rpc'],
               'eth_call',
               [{'to': config['pool'], 'data': method_id}, 'latest']
           )
           if result and result != '0x':
               print(f"✅ {network_name} Pool contract working")
           else:
               print(f"❌ {network_name} Pool contract returned empty")
       except Exception as e:
           print(f"❌ {network_name} Pool contract failed: {e}")
   
   # Test all new networks
   for network in ['mantle', 'soneium', 'sonic']:
       if network in AAVE_V3_NETWORKS:
           test_pool_contract(network)
   ```

### Rate Limiting Issues

#### Issue: RPC Rate Limits Exceeded
**Symptoms:**
- Error: "Too Many Requests" (429)
- Sudden drops in success rate
- Inconsistent data fetching

**Solutions:**

1. **Implement Exponential Backoff**
   ```python
   # Enhanced retry logic with backoff
   def rpc_call_with_backoff(url, method, params, max_retries=5):
       for attempt in range(max_retries):
           try:
               result = rpc_call(url, method, params)
               return result
           except Exception as e:
               if '429' in str(e) or 'rate limit' in str(e).lower():
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   print(f"Rate limited, waiting {wait_time:.1f}s...")
                   time.sleep(wait_time)
               else:
                   raise e
       raise Exception(f"Max retries exceeded for {url}")
   ```

2. **Distribute Load Across RPCs**
   ```python
   # Round-robin RPC selection
   class RPCLoadBalancer:
       def __init__(self, rpc_urls):
           self.rpc_urls = rpc_urls
           self.current_index = 0
           self.failure_counts = {url: 0 for url in rpc_urls}
       
       def get_next_rpc(self):
           # Skip failed RPCs
           for _ in range(len(self.rpc_urls)):
               url = self.rpc_urls[self.current_index]
               self.current_index = (self.current_index + 1) % len(self.rpc_urls)
               
               if self.failure_counts[url] < 3:  # Max 3 failures
                   return url
           
           # All RPCs failed, reset counters
           self.failure_counts = {url: 0 for url in self.rpc_urls}
           return self.rpc_urls[0]
   ```

3. **Reduce Concurrent Requests**
   ```bash
   # Use fewer workers for rate-limited networks
   python aave_fetcher.py --parallel --max-workers 2
   ```

## 📊 Data Quality Issues

### Validation Failures

#### Issue: 2025 Parameter Validation Errors
**Symptoms:**
- validation_report.json shows multiple errors
- Known values don't match fetched data
- New parameters (supply/borrow caps) failing validation

**Solutions:**

1. **Update Known Values for 2025**
   ```python
   # In src/validation.py, update expected values
   KNOWN_VALUES_2025_UPDATED = {
       'ethereum': {
           'WBTC': {
               'liquidation_threshold': 0.78,  # Updated from 0.70
               'loan_to_value': 0.73,          # Updated from 0.65
               'liquidation_bonus': 0.05,      # Updated from 0.10
               'reserve_factor': 0.50          # Updated from 0.20
           },
           'DAI': {
               'loan_to_value': 0.63           # Updated from 0.75
           }
       },
       'polygon': {
           'USDC': {
               'loan_to_value': 0.00,          # Disabled as collateral
               'reserve_factor': 0.60          # Updated from 0.10
           }
       }
   }
   ```

2. **Adjust Validation Tolerances**
   ```python
   # More lenient tolerances for volatile parameters
   VALIDATION_TOLERANCES_2025 = {
       'liquidation_threshold': 0.05,  # 5%
       'loan_to_value': 0.05,          # 5%
       'liquidation_bonus': 0.15,      # 15%
       'reserve_factor': 0.20,         # 20%
       'supply_cap': 0.30,             # 30% (more volatile)
       'borrow_cap': 0.30              # 30% (more volatile)
   }
   ```

3. **Handle New Parameters**
   ```python
   # Validate 2025 features gracefully
   def validate_2025_features(asset):
       """Validate new 2025 parameters."""
       
       # Supply/borrow caps (new feature)
       if 'supply_cap' in asset:
           assert asset['supply_cap'] >= 0, "Supply cap must be non-negative"
       
       if 'borrow_cap' in asset:
           assert asset['borrow_cap'] >= 0, "Borrow cap must be non-negative"
           if 'supply_cap' in asset and asset['supply_cap'] > 0:
               assert asset['borrow_cap'] <= asset['supply_cap'], "Borrow cap cannot exceed supply cap"
       
       # Validate disabled collateral (LTV = 0)
       if asset.get('loan_to_value', 0) == 0 and asset.get('liquidation_threshold', 0) > 0:
           print(f"ℹ️ {asset['symbol']} has collateral disabled (LTV=0)")
   ```

#### Issue: Stale Data Detection
**Symptoms:**
- Data timestamps are old
- freshness_report.json shows stale networks
- Inconsistent update times

**Solutions:**

1. **Check Workflow Schedule**
   ```yaml
   # Verify cron schedule in .github/workflows/update-aave-data.yml
   schedule:
     - cron: '0 0 * * *'  # Daily at midnight UTC
   
   # For more frequent updates:
   schedule:
     - cron: '0 */6 * * *'  # Every 6 hours
   ```

2. **Validate Data Freshness**
   ```bash
   # Check data age
   python -c "
   import json
   from datetime import datetime, timezone
   
   with open('aave_v3_data.json', 'r') as f:
       data = json.load(f)
   
   last_updated = datetime.fromisoformat(data['metadata']['last_updated'].replace('Z', '+00:00'))
   age_hours = (datetime.now(timezone.utc) - last_updated).total_seconds() / 3600
   
   print(f'Data age: {age_hours:.1f} hours')
   if age_hours > 25:
       print('⚠️ Data is stale (>25 hours old)')
   else:
       print('✅ Data is fresh')
   "
   ```

3. **Force Manual Update**
   ```bash
   # Trigger workflow manually
   # Go to Actions → Update Aave V3 Data → Run workflow
   
   # Or run locally and commit
   python aave_fetcher.py --ultra-fast --validate
   git add aave_v3_data.json aave_v3_data.html
   git commit -m "Manual data update"
   git push
   ```

## ⚡ Performance Issues

### GitHub Actions Timeout

#### Issue: Workflow Exceeds 10-Minute Limit
**Symptoms:**
- Workflow cancelled due to timeout
- Incomplete data fetching
- Performance degradation over time

**Solutions:**

1. **Use Maximum Performance Mode**
   ```yaml
   # In workflow file
   - name: Run Aave Data Fetcher
     run: python aave_fetcher.py --turbo --timeout 60
   ```

2. **Optimize Network Processing**
   ```python
   # Prioritize critical networks
   PRIORITY_ORDER = [
       'ethereum', 'polygon', 'arbitrum', 'optimism',  # Tier 1
       'avalanche', 'base', 'bnb', 'gnosis',           # Tier 2
       'scroll', 'metis', 'celo', 'mantle'             # Tier 3
   ]
   
   def process_networks_by_priority():
       """Process networks in priority order."""
       results = {}
       
       for tier, networks in enumerate([PRIORITY_ORDER[:4], PRIORITY_ORDER[4:8], PRIORITY_ORDER[8:]], 1):
           print(f"Processing Tier {tier} networks...")
           with ThreadPoolExecutor(max_workers=min(4, len(networks))) as executor:
               tier_results = executor.map(fetch_network_data, networks)
               results.update(dict(zip(networks, tier_results)))
       
       return results
   ```

3. **Monitor Execution Time**
   ```bash
   # Track performance
   python aave_fetcher.py --turbo --save-performance-report
   
   # Check execution breakdown
   python -c "
   import json
   with open('performance_report.json', 'r') as f:
       report = json.load(f)
   
   total_time = sum(metrics['duration'] for metrics in report['network_metrics'].values())
   print(f'Total execution time: {total_time:.1f}s')
   
   # Show slowest networks
   slow_networks = sorted(
       report['network_metrics'].items(),
       key=lambda x: x[1]['duration'],
       reverse=True
   )[:5]
   
   print('Slowest networks:')
   for network, metrics in slow_networks:
       print(f'  {network}: {metrics[\"duration\"]:.1f}s')
   "
   ```

#### Issue: Memory Usage Problems
**Symptoms:**
- Out of memory errors
- Workflow killed unexpectedly
- Slow performance with large datasets

**Solutions:**

1. **Optimize Memory Usage**
   ```python
   # Process networks sequentially for memory efficiency
   def fetch_with_memory_optimization():
       """Memory-optimized fetching."""
       results = {}
       
       for network in get_active_networks():
           print(f"Processing {network}...")
           network_data = fetch_network_data(network)
           results[network] = network_data
           
           # Clear intermediate data
           gc.collect()
       
       return results
   ```

2. **Reduce Concurrent Workers**
   ```bash
   # Use fewer workers to reduce memory usage
   python aave_fetcher.py --max-workers 2 --sequential
   ```

3. **Monitor Memory Usage**
   ```python
   import psutil
   import os
   
   def monitor_memory():
       """Monitor memory usage during execution."""
       process = psutil.Process(os.getpid())
       memory_mb = process.memory_info().rss / 1024 / 1024
       print(f"Memory usage: {memory_mb:.1f} MB")
       
       if memory_mb > 1000:  # 1GB threshold
           print("⚠️ High memory usage detected")
   ```

## 🔧 Network-Specific Issues

### Ethereum Mainnet Issues

#### Issue: High Gas Estimation Errors
**Symptoms:**
- "Gas estimation failed" errors
- Slow response times
- Inconsistent data

**Solutions:**

1. **Use Multiple RPC Providers**
   ```python
   'ethereum': {
       'rpc': 'https://rpc.ankr.com/eth',
       'fallback_rpcs': [
           'https://eth.llamarpc.com',
           'https://ethereum.publicnode.com',
           'https://rpc.payload.de'
       ]
   }
   ```

2. **Optimize Gas Settings**
   ```python
   # Use appropriate gas limits for view functions
   ETH_CALL_PARAMS = {
       'gas': '0x5f5e100',  # 100M gas limit
       'gasPrice': '0x0'    # No gas price for view calls
   }
   ```

### Layer 2 Network Issues

#### Issue: Polygon RPC Instability
**Symptoms:**
- Frequent timeouts
- Inconsistent block numbers
- Rate limiting

**Solutions:**

1. **Use Polygon-Specific RPCs**
   ```python
   'polygon': {
       'rpc': 'https://polygon-rpc.com',
       'fallback_rpcs': [
           'https://rpc.ankr.com/polygon',
           'https://polygon.llamarpc.com',
           'https://polygon.publicnode.com'
       ]
   }
   ```

2. **Adjust Timeout Settings**
   ```python
   NETWORK_TIMEOUTS = {
       'polygon': 45,    # Longer timeout for Polygon
       'arbitrum': 30,   # Standard timeout
       'optimism': 30    # Standard timeout
   }
   ```

#### Issue: Arbitrum/Optimism Sequencer Issues
**Symptoms:**
- "Sequencer down" errors
- Delayed block confirmations
- Inconsistent data

**Solutions:**

1. **Check Sequencer Status**
   ```python
   def check_sequencer_status(network):
       """Check L2 sequencer status."""
       if network == 'arbitrum':
           # Check Arbitrum sequencer
           sequencer_url = 'https://arb1.arbitrum.io/rpc'
       elif network == 'optimism':
           # Check Optimism sequencer
           sequencer_url = 'https://mainnet.optimism.io'
       
       try:
           result = rpc_call(sequencer_url, 'eth_blockNumber', [])
           return {'status': 'up', 'latest_block': int(result, 16)}
       except:
           return {'status': 'down', 'latest_block': None}
   ```

2. **Use Alternative RPCs**
   ```python
   'arbitrum': {
       'rpc': 'https://arb1.arbitrum.io/rpc',
       'fallback_rpcs': [
           'https://rpc.ankr.com/arbitrum',
           'https://arbitrum.publicnode.com'
       ]
   }
   ```

## 🛠️ Advanced Debugging

### Debug Mode Execution

```bash
# Maximum debugging information
python aave_fetcher.py \
  --sequential \
  --debug \
  --log-file debug.log \
  --save-debug-report \
  --include-rpc-history \
  --timeout 120 \
  --validate-freshness
```

### Custom Debug Scripts

```python
#!/usr/bin/env python3
"""Custom debugging script for troubleshooting."""

import json
import time
from src.networks import AAVE_V3_NETWORKS, get_active_networks
from src.utils import rpc_call, get_method_id

def comprehensive_debug():
    """Run comprehensive debugging checks."""
    
    print("🔍 Comprehensive Debug Report")
    print("=" * 50)
    
    # 1. Network configuration check
    print("\n1. Network Configuration Check")
    active_networks = get_active_networks()
    print(f"Active networks: {len(active_networks)}")
    
    for network, config in active_networks.items():
        print(f"\n{network}:")
        print(f"  RPC: {config['rpc']}")
        print(f"  Pool: {config['pool']}")
        print(f"  Fallbacks: {len(config.get('fallback_rpcs', []))}")
    
    # 2. RPC connectivity test
    print("\n2. RPC Connectivity Test")
    for network, config in active_networks.items():
        try:
            start_time = time.time()
            result = rpc_call(config['rpc'], 'eth_blockNumber', [])
            response_time = time.time() - start_time
            block_number = int(result, 16)
            
            print(f"✅ {network}: Block {block_number} ({response_time:.2f}s)")
        except Exception as e:
            print(f"❌ {network}: {str(e)[:100]}...")
    
    # 3. Pool contract test
    print("\n3. Pool Contract Test")
    method_id = get_method_id('getReservesList()')
    
    for network, config in active_networks.items():
        try:
            result = rpc_call(
                config['rpc'],
                'eth_call',
                [{'to': config['pool'], 'data': method_id}, 'latest']
            )
            
            if result and result != '0x':
                # Decode reserve count
                reserve_count = len(result[2:]) // 64  # Each address is 32 bytes (64 hex chars)
                print(f"✅ {network}: {reserve_count} reserves")
            else:
                print(f"⚠️ {network}: Empty response")
                
        except Exception as e:
            print(f"❌ {network}: {str(e)[:100]}...")
    
    # 4. Data file check
    print("\n4. Data File Check")
    files_to_check = [
        'aave_v3_data.json',
        'aave_v3_data.html',
        'health_report.json',
        'validation_report.json'
    ]
    
    for filename in files_to_check:
        try:
            with open(filename, 'r') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                    print(f"✅ {filename}: Valid JSON ({len(str(data))} chars)")
                else:
                    content = f.read()
                    print(f"✅ {filename}: {len(content)} chars")
        except FileNotFoundError:
            print(f"❌ {filename}: Not found")
        except Exception as e:
            print(f"⚠️ {filename}: {e}")
    
    print("\n" + "=" * 50)
    print("Debug report complete")

if __name__ == "__main__":
    comprehensive_debug()
```

### Performance Profiling

```python
#!/usr/bin/env python3
"""Performance profiling for troubleshooting."""

import cProfile
import pstats
import io
from src.graceful_fetcher import fetch_all_networks

def profile_execution():
    """Profile the execution to find bottlenecks."""
    
    pr = cProfile.Profile()
    pr.enable()
    
    # Run the fetcher
    try:
        results = fetch_all_networks(['ethereum', 'polygon'])  # Test with 2 networks
    except Exception as e:
        print(f"Error during profiling: {e}")
    
    pr.disable()
    
    # Generate report
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print("Performance Profile:")
    print(s.getvalue())

if __name__ == "__main__":
    profile_execution()
```

This comprehensive troubleshooting guide should help resolve most issues encountered during deployment and operation of the Aave V3 Data Fetcher, especially with the 2025 network expansions and evolving RPC landscape.