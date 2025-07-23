#!/usr/bin/env python3
"""
Ultra-fast Aave V3 Data Fetcher combining all optimizations:
- Multicall3 for single RPC call per network
- Batch RPC as fallback
- Parallel processing with connection pooling
- Intelligent caching
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from multicall3 import Multicall3Client, MULTICALL3_ADDRESSES
from batch_rpc import BatchRPCClient
from monitoring import record_network_request, update_rpc_latency


class UltraFastFetcher:
    """The fastest possible Aave data fetcher combining all optimizations."""
    
    def __init__(self):
        # Shared session for all HTTP calls
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Aave-UltraFast/1.0'
        })
        
        # Configure aggressive connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=50,
            pool_maxsize=200,
            max_retries=0
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Initialize clients
        self.multicall_client = Multicall3Client(self.session)
        self.batch_client = BatchRPCClient(self.session)
        
        # Performance tracking
        self.stats = {
            'multicall3_success': 0,
            'batch_rpc_success': 0,
            'fallback_used': 0,
            'total_rpc_calls': 0
        }
    
    def _get_reserves_list(self, rpc_url: str, pool_address: str) -> Optional[List[str]]:
        """Get the list of reserve addresses from the pool."""
        result = self.multicall_client._rpc_call(
            rpc_url,
            'eth_call',
            [{
                'to': pool_address,
                'data': '0xd1946dbc'  # getReservesList()
            }, 'latest'],
            timeout=10
        )
        
        if not result or result == '0x':
            return None
        
        # Parse the array
        try:
            data = result[2:] if result.startswith('0x') else result
            data = data[64:]  # Skip offset
            array_length = int(data[:64], 16)
            data = data[64:]
            
            reserves = []
            for i in range(array_length):
                if len(data) >= 64:
                    address = "0x" + data[24:64]
                    reserves.append(address)
                    data = data[64:]
            
            return reserves
        except Exception:
            return None
    
    def _find_working_rpc(self, rpc_urls: List[str]) -> Optional[str]:
        """Find the first working RPC URL from the list."""
        for url in rpc_urls[:5]:  # Try max 5 URLs
            try:
                result = self.multicall_client._rpc_call(
                    url, 
                    'eth_blockNumber', 
                    [], 
                    timeout=3
                )
                if result:
                    return url
            except Exception:
                continue
        return None
    
    def fetch_network_ultra_fast(
        self,
        network_key: str,
        network_config: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch network data using the fastest available method.
        
        Priority:
        1. Multicall3 (1 RPC call)
        2. Batch RPC (2-3 RPC calls)  
        3. Parallel individual calls (fallback)
        """
        start_time = time.time()
        print(f"🔄 Starting {network_config['name']}...")
        
        # Get RPC URLs
        rpc_urls = [network_config['rpc']] + network_config.get('rpc_fallback', [])
        
        # Find working RPC
        working_url = self._find_working_rpc(rpc_urls)
        if not working_url:
            record_network_request(network_key, False, "No working RPC")
            return None
        
        # Get reserves list
        reserves = self._get_reserves_list(working_url, network_config['pool'])
        if not reserves:
            record_network_request(network_key, False, "Failed to get reserves")
            return None
        
        print(f"🎯 {network_config['name']}: {len(reserves)} reserves found")
        
        # Special handling for BNB and zkSync (PoolDataProvider doesn't work)
        if network_key in ['bnb', 'zksync']:
            print(f"   🔧 Using special fetcher for {network_key}")
            from bnb_zksync_fetcher import BnbZkSyncFetcher
            special_fetcher = BnbZkSyncFetcher()
            try:
                assets = special_fetcher.fetch_network_data(network_key, network_config, reserves)
                if assets:
                    elapsed = time.time() - start_time
                    self.stats['batch_rpc_success'] += 1
                    self.stats['total_rpc_calls'] += len(reserves) * 2
                    record_network_request(network_key, True)
                    update_rpc_latency(working_url, elapsed * 1000)
                    print(f"   ✅ Special fetcher success: {len(assets)} assets in {elapsed:.2f}s")
                    return assets
            except Exception as e:
                print(f"   ❌ Special fetcher failed: {str(e)}")
            finally:
                special_fetcher.close()
            return None
        
        # Try Multicall3 first (if supported)
        multicall_address = MULTICALL3_ADDRESSES.get(network_key)
        if multicall_address:
            try:
                print(f"   🚀 Trying Multicall3...")
                assets = self.multicall_client.fetch_network_data_multicall3(
                    network_key,
                    network_config,
                    working_url,
                    reserves,
                    multicall_address
                )
                
                if assets and len(assets) > 0:
                    elapsed = time.time() - start_time
                    self.stats['multicall3_success'] += 1
                    self.stats['total_rpc_calls'] += 2  # getReservesList + multicall
                    record_network_request(network_key, True)
                    update_rpc_latency(working_url, elapsed * 1000)
                    print(f"   ✅ Multicall3 success: {len(assets)} assets in {elapsed:.2f}s")
                    return assets
                    
            except Exception as e:
                print(f"   ⚠️  Multicall3 failed: {str(e)}")
        
        # Try Batch RPC
        try:
            print(f"   ⚡ Trying Batch RPC...")
            
            # Use the updated fetch_network_data_batch method that gets complete data
            assets = self.batch_client.fetch_network_data_batch(
                network_key,
                network_config,
                working_url,
                reserves
            )
            
            if assets:
                elapsed = time.time() - start_time
                self.stats['batch_rpc_success'] += 1
                self.stats['total_rpc_calls'] += 4  # getReservesList + 3 batch calls
                record_network_request(network_key, True)
                update_rpc_latency(working_url, elapsed * 1000)
                print(f"   ✅ Batch RPC success: {len(assets)} assets in {elapsed:.2f}s")
                return assets
                
        except Exception as e:
            print(f"   ⚠️  Batch RPC failed: {str(e)}")
        
        # Last resort - use the original graceful fetcher
        print(f"   🔄 Falling back to parallel fetching...")
        self.stats['fallback_used'] += 1
        
        # Import and use the optimized graceful fetcher
        from graceful_fetcher_optimized import OptimizedGracefulDataFetcher
        fallback_fetcher = OptimizedGracefulDataFetcher()
        
        try:
            assets = fallback_fetcher.fetch_network_data_optimized(
                network_key,
                network_config,
                max_asset_workers=20  # More aggressive parallelism as last resort
            )
            
            if assets:
                elapsed = time.time() - start_time
                self.stats['total_rpc_calls'] += 1 + (len(assets) * 2)  # Rough estimate
                record_network_request(network_key, True)
                update_rpc_latency(working_url, elapsed * 1000)
                print(f"   ✅ Fallback success: {len(assets)} assets in {elapsed:.2f}s")
                return assets
                
        except Exception as e:
            print(f"   ❌ All methods failed: {str(e)}")
        finally:
            fallback_fetcher.close()
        
        record_network_request(network_key, False, "All fetch methods failed")
        return None
    
    def fetch_network_ultra_fast_optimized(
        self,
        network_key: str,
        network_config: Dict[str, Any],
        priority
    ) -> Tuple[Optional[List[Dict[str, Any]]], float]:
        """
        Optimized network fetching with caching and prioritization.
        
        Returns:
            Tuple of (network_data, execution_time)
        """
        from performance_cache import (
            get_cached_reserve_list, cache_reserve_list,
            get_cached_symbol, cache_symbol
        )
        
        start_time = time.time()
        print(f"🔄 Starting {network_config['name']} (Priority: {priority.tier.name})...")
        
        # Get RPC URLs with priority-based selection
        rpc_urls = [network_config['rpc']] + network_config.get('rpc_fallback', [])
        
        # Find working RPC
        working_url = self._find_working_rpc(rpc_urls)
        if not working_url:
            record_network_request(network_key, False, "No working RPC")
            return None, time.time() - start_time
        
        # Try to get cached reserve list first
        reserves = get_cached_reserve_list(network_key)
        
        if not reserves:
            # Get reserves list from blockchain
            reserves = self._get_reserves_list(working_url, network_config['pool'])
            if reserves:
                # Cache the reserve list with performance score based on priority
                cache_reserve_list(network_key, reserves, priority.weight)
        
        if not reserves:
            record_network_request(network_key, False, "Failed to get reserves")
            return None, time.time() - start_time
        
        print(f"🎯 {network_config['name']}: {len(reserves)} reserves found")
        
        # Special handling for BNB and zkSync (PoolDataProvider doesn't work)
        if network_key in ['bnb', 'zksync']:
            print(f"   🔧 Using special fetcher for {network_key}")
            from bnb_zksync_fetcher import BnbZkSyncFetcher
            special_fetcher = BnbZkSyncFetcher()
            try:
                assets = special_fetcher.fetch_network_data(network_key, network_config, reserves)
                if assets:
                    elapsed = time.time() - start_time
                    self.stats['batch_rpc_success'] += 1
                    self.stats['total_rpc_calls'] += len(reserves) * 2
                    record_network_request(network_key, True)
                    update_rpc_latency(working_url, elapsed * 1000)
                    
                    # Cache symbols for future use
                    for asset in assets:
                        if 'symbol' in asset and 'asset_address' in asset:
                            cache_symbol(asset['asset_address'], asset['symbol'], network_key)
                    
                    print(f"   ✅ Special fetcher success: {len(assets)} assets in {elapsed:.2f}s")
                    return assets, elapsed
            except Exception as e:
                print(f"   ❌ Special fetcher failed: {str(e)}")
            finally:
                special_fetcher.close()
            return None, time.time() - start_time
        
        # Try Multicall3 first (if supported)
        multicall_address = MULTICALL3_ADDRESSES.get(network_key)
        if multicall_address:
            try:
                print(f"   🚀 Trying Multicall3...")
                assets = self.multicall_client.fetch_network_data_multicall3(
                    network_key,
                    network_config,
                    working_url,
                    reserves,
                    multicall_address
                )
                
                if assets and len(assets) > 0:
                    elapsed = time.time() - start_time
                    self.stats['multicall3_success'] += 1
                    self.stats['total_rpc_calls'] += 2  # getReservesList + multicall
                    record_network_request(network_key, True)
                    update_rpc_latency(working_url, elapsed * 1000)
                    
                    # Cache symbols for future use
                    for asset in assets:
                        if 'symbol' in asset and 'asset_address' in asset:
                            cache_symbol(asset['asset_address'], asset['symbol'], network_key)
                    
                    print(f"   ✅ Multicall3 success: {len(assets)} assets in {elapsed:.2f}s")
                    return assets, elapsed
                    
            except Exception as e:
                print(f"   ⚠️  Multicall3 failed: {str(e)}")
        
        # Try Batch RPC
        try:
            print(f"   ⚡ Trying Batch RPC...")
            
            assets = self.batch_client.fetch_network_data_batch(
                network_key,
                network_config,
                working_url,
                reserves
            )
            
            if assets:
                elapsed = time.time() - start_time
                self.stats['batch_rpc_success'] += 1
                self.stats['total_rpc_calls'] += 4  # getReservesList + 3 batch calls
                record_network_request(network_key, True)
                update_rpc_latency(working_url, elapsed * 1000)
                
                # Cache symbols for future use
                for asset in assets:
                    if 'symbol' in asset and 'asset_address' in asset:
                        cache_symbol(asset['asset_address'], asset['symbol'], network_key)
                
                print(f"   ✅ Batch RPC success: {len(assets)} assets in {elapsed:.2f}s")
                return assets, elapsed
                
        except Exception as e:
            print(f"   ⚠️  Batch RPC failed: {str(e)}")
        
        # Last resort - use the optimized graceful fetcher
        print(f"   🔄 Falling back to parallel fetching...")
        self.stats['fallback_used'] += 1
        
        try:
            from graceful_fetcher_optimized import OptimizedGracefulDataFetcher
            fallback_fetcher = OptimizedGracefulDataFetcher()
            
            assets = fallback_fetcher.fetch_network_data_optimized(
                network_key,
                network_config,
                max_asset_workers=min(20, priority.parallel_workers * 4)  # Scale workers by priority
            )
            
            if assets:
                elapsed = time.time() - start_time
                self.stats['total_rpc_calls'] += 1 + (len(assets) * 2)  # Rough estimate
                record_network_request(network_key, True)
                update_rpc_latency(working_url, elapsed * 1000)
                
                # Cache symbols for future use
                for asset in assets:
                    if 'symbol' in asset and 'asset_address' in asset:
                        cache_symbol(asset['asset_address'], asset['symbol'], network_key)
                
                print(f"   ✅ Fallback success: {len(assets)} assets in {elapsed:.2f}s")
                return assets, elapsed
            
            fallback_fetcher.close()
                
        except Exception as e:
            print(f"   ❌ All methods failed: {str(e)}")
        
        record_network_request(network_key, False, "All fetch methods failed")
        return None, time.time() - start_time
    
    def close(self):
        """Clean up resources."""
        self.session.close()
    
    def print_stats(self):
        """Print performance statistics."""
        print("\n📊 Ultra Fast Fetcher Statistics:")
        print(f"   Multicall3 successes: {self.stats['multicall3_success']}")
        print(f"   Batch RPC successes: {self.stats['batch_rpc_success']}")
        print(f"   Fallback used: {self.stats['fallback_used']}")
        print(f"   Total RPC calls made: {self.stats['total_rpc_calls']}")


def fetch_aave_data_ultra_fast(
    max_network_workers: int = 8,
    save_reports: bool = True
) -> Tuple[Dict[str, List[Dict]], Dict[str, Any]]:
    """
    Fetch Aave data using the ultra-fast optimized approach with performance enhancements.
    
    This is the ultimate performance optimization:
    - Network prioritization for critical chains
    - Intelligent caching for network configs and symbols
    - Multicall3 where available (1 RPC call per network)
    - Batch RPC as fallback (2-3 RPC calls per network)
    - Parallel individual calls as last resort
    """
    from networks import get_active_networks
    from network_prioritization import (
        get_prioritized_networks, get_execution_strategy, 
        record_network_performance, network_prioritizer
    )
    from performance_cache import performance_cache
    
    print("⚡ ULTRA FAST AAVE DATA FETCHER ⚡")
    print("=" * 50)
    
    fetcher = UltraFastFetcher()
    networks = get_active_networks()
    all_data = {}
    
    start_time = time.time()
    
    # Get execution strategy based on GitHub Actions time limits
    strategy = get_execution_strategy(0, 540, networks)  # 9 minute safety limit
    
    print(f"🚀 Fetching from {len(networks)} networks with {strategy['max_workers']} workers")
    print(f"   Strategy: {strategy['mode']} | Multicall3 → Batch RPC → Parallel")
    
    # Print network prioritization summary
    network_prioritizer.print_priority_summary(networks)
    
    # Get prioritized networks
    prioritized_networks = get_prioritized_networks(networks)
    
    # Process networks in parallel with prioritization
    with ThreadPoolExecutor(max_workers=strategy['max_workers']) as executor:
        future_to_network = {}
        
        for network_key, network_config, priority in prioritized_networks:
            # Skip if strategy says critical only and this isn't critical
            if strategy['mode'] == 'critical_only' and priority.tier.value > 1:
                continue
            
            future = executor.submit(
                fetcher.fetch_network_ultra_fast_optimized,
                network_key,
                network_config,
                priority
            )
            future_to_network[future] = (network_key, priority)
        
        completed = 0
        for future in as_completed(future_to_network):
            network_key, priority = future_to_network[future]
            completed += 1
            
            try:
                network_data, execution_time = future.result()
                
                if network_data:
                    all_data[network_key] = network_data
                    record_network_performance(network_key, execution_time, True)
                else:
                    record_network_performance(network_key, execution_time, False)
                    
                # Progress indicator
                print(f"\n📈 Progress: {completed}/{len(future_to_network)} networks")
                
                # Check if we're approaching time limits
                elapsed = time.time() - start_time
                if elapsed > 480:  # 8 minutes
                    print("⚠️  Approaching time limit - may stop early")
                    break
                
            except Exception as e:
                print(f"❌ {networks[network_key]['name']}: {str(e)}")
                record_network_performance(network_key, 60, False)  # Assume 60s for failed attempts
    
    # Save cache after processing
    performance_cache.save()
    
    # Calculate final stats
    total_time = time.time() - start_time
    total_assets = sum(len(assets) for assets in all_data.values())
    
    # Print performance report
    print("\n" + "=" * 50)
    print("🏁 FETCH COMPLETE")
    print("=" * 50)
    print(f"⏱️  Total time: {total_time:.1f}s")
    print(f"📊 Total assets: {total_assets}")
    print(f"🌐 Successful networks: {len(all_data)}/{len(networks)}")
    print(f"🎯 Execution strategy: {strategy['mode']}")
    
    if total_assets > 0:
        print(f"⚡ Average time per asset: {(total_time / total_assets) * 1000:.1f}ms")
        print(f"🚀 Assets per second: {total_assets / total_time:.1f}")
    
    fetcher.print_stats()
    
    # Performance comparison
    print("\n📊 Performance Analysis:")
    if fetcher.stats['multicall3_success'] > 0:
        print(f"   🎯 Multicall3 used for {fetcher.stats['multicall3_success']} networks (fastest)")
    if fetcher.stats['batch_rpc_success'] > 0:
        print(f"   ⚡ Batch RPC used for {fetcher.stats['batch_rpc_success']} networks (fast)")
    if fetcher.stats['fallback_used'] > 0:
        print(f"   🔄 Fallback used for {fetcher.stats['fallback_used']} networks (slower)")
    
    # Cache statistics
    cache_stats = performance_cache.get_cache_stats()
    if cache_stats['total_entries'] > 0:
        print(f"\n💾 Cache Performance:")
        print(f"   📊 Cache entries: {cache_stats['active_entries']}/{cache_stats['total_entries']}")
        print(f"   🎯 Hit potential: {cache_stats['cache_hit_potential']}")
        print(f"   ⚡ Avg performance score: {cache_stats['average_performance_score']:.2f}")
    
    # GitHub Actions compliance
    if total_time < 300:  # 5 minutes
        print("✅ Excellent performance - well under GitHub Actions limits")
    elif total_time < 480:  # 8 minutes
        print("✅ Good performance - within GitHub Actions limits")
    elif total_time < 540:  # 9 minutes
        print("⚠️  Approaching GitHub Actions time limit")
    else:
        print("🔴 Exceeding recommended GitHub Actions time limit")
    
    # Close resources
    fetcher.close()
    
    # Create comprehensive fetch report
    fetch_report = {
        'fetch_summary': {
            'total_time': total_time,
            'total_assets': total_assets,
            'networks_attempted': len(networks),
            'networks_successful': len(all_data),
            'avg_time_per_asset_ms': (total_time / total_assets * 1000) if total_assets > 0 else 0,
            'assets_per_second': total_assets / total_time if total_time > 0 else 0,
            'multicall3_used': fetcher.stats['multicall3_success'],
            'batch_rpc_used': fetcher.stats['batch_rpc_success'],
            'fallback_used': fetcher.stats['fallback_used'],
            'total_rpc_calls': fetcher.stats['total_rpc_calls'],
            'execution_strategy': strategy['mode'],
            'github_actions_compliant': total_time < 540
        },
        'performance_optimizations': {
            'cache_stats': cache_stats,
            'network_prioritization': network_prioritizer.get_network_stats(),
            'strategy_used': strategy
        }
    }
    
    return all_data, fetch_report


if __name__ == "__main__":
    # Test the ultra fast fetcher
    data, report = fetch_aave_data_ultra_fast(max_network_workers=10)
    
    print(f"\n✅ Fetched {report['fetch_summary']['total_assets']} assets")
    print(f"⚡ Performance: {report['fetch_summary']['assets_per_second']:.1f} assets/second")