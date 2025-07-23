#!/usr/bin/env python3
"""
Optimized Aave V3 Data Fetcher with parallel asset fetching and performance improvements.
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from functools import lru_cache
from datetime import datetime

from monitoring import log_network_attempt, log_network_success, log_network_failure, update_rpc_latency
from utils import get_reserves, get_asset_symbol, get_reserve_data


class OptimizedGracefulDataFetcher:
    """Optimized data fetcher with parallel asset fetching and connection pooling."""
    
    def __init__(self):
        self.start_time = time.time()
        self.success_count = 0
        self.failure_count = 0
        self.network_attempts = {}
        self.network_latencies = {}
        
        # Connection pooling with requests
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Aave-Data-Fetcher/2.0'
        })
        
        # Configure connection pool
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,  # Number of connection pools
            pool_maxsize=100,     # Connections per pool
            max_retries=0         # We handle retries ourselves
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Cache for symbol lookups (symbols don't change)
        self._symbol_cache = {}
        
        # Reduced timeouts for faster failover
        self.timeout_config = {
            'connection': 5,   # 5 seconds to establish connection
            'read': 10,        # 10 seconds to read response
            'total': 15        # 15 seconds total per request
        }
    
    def _optimized_rpc_call(self, url: str, method: str, params: List[Any], timeout: Optional[int] = None) -> Optional[Any]:
        """Optimized RPC call using connection pooling and reduced timeouts."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            timeout = timeout or self.timeout_config['total']
            response = self.session.post(
                url,
                json=payload,
                timeout=(self.timeout_config['connection'], self.timeout_config['read'])
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    # Don't retry on JSON-RPC errors, fail fast
                    return None
            
            return None
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.ConnectionError:
            return None
        except Exception:
            return None
    
    @lru_cache(maxsize=1000)
    def _get_cached_symbol(self, asset_address: str, rpc_url: str) -> Optional[str]:
        """Cache symbol lookups as they don't change."""
        cache_key = f"{asset_address}:{rpc_url}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        # Try symbol() first (most common)
        result = self._optimized_rpc_call(
            rpc_url,
            "eth_call",
            [{
                "to": asset_address,
                "data": "0x95d89b41"  # symbol()
            }, "latest"]
        )
        
        if result and result != "0x":
            try:
                # Decode the result
                if result.startswith('0x'):
                    result = result[2:]
                
                # Handle different encoding formats
                if len(result) >= 128:  # Dynamic string
                    offset = int(result[0:64], 16) * 2
                    length = int(result[offset:offset+64], 16) * 2
                    symbol_hex = result[offset+64:offset+64+length]
                else:  # Fixed bytes32
                    symbol_hex = result.rstrip('0')
                
                if symbol_hex:
                    symbol = bytes.fromhex(symbol_hex).decode('utf-8').strip('\x00')
                    self._symbol_cache[cache_key] = symbol
                    return symbol
                    
            except Exception:
                pass
        
        # Fallback to SYMBOL() if symbol() fails
        result = self._optimized_rpc_call(
            rpc_url,
            "eth_call",
            [{
                "to": asset_address,
                "data": "0xf76f8d78"  # SYMBOL()
            }, "latest"]
        )
        
        if result and result != "0x":
            try:
                symbol = bytes.fromhex(result[2:].rstrip('0')).decode('utf-8').strip('\x00')
                self._symbol_cache[cache_key] = symbol
                return symbol
            except Exception:
                pass
        
        return None
    
    def fetch_asset_data_parallel(
        self, 
        asset_address: str,
        network_config: Dict,
        rpc_url: str,
        network_key: str
    ) -> Optional[Dict]:
        """Fetch data for a single asset with optimized RPC calls."""
        try:
            # Get symbol (cached)
            symbol = self._get_cached_symbol(asset_address, rpc_url)
            if not symbol:
                return None
            
            # Get configuration data from pool
            pool_result = self._optimized_rpc_call(
                rpc_url,
                "eth_call",
                [{
                    "to": network_config.get('pool'),
                    "data": f"0x35ea6a75000000000000000000000000{asset_address[2:].lower()}"
                }, "latest"]
            )
            
            # Get supply/debt data from pool_data_provider
            provider_result = self._optimized_rpc_call(
                rpc_url,
                "eth_call",
                [{
                    "to": network_config.get('pool_data_provider'),
                    "data": f"0x35ea6a75000000000000000000000000{asset_address[2:].lower()}"
                }, "latest"]
            )
            
            if not pool_result or pool_result == "0x" or not provider_result or provider_result == "0x":
                return None
            
            # Parse pool data (configuration and token addresses)
            try:
                pool_data = pool_result[2:] if pool_result.startswith('0x') else pool_result
                
                # Extract configuration
                configuration = int(pool_data[0:64], 16)
                
                # Decode configuration bitmap
                config_data = {
                    'loan_to_value': (configuration & ((1 << 16) - 1)) / 10000,
                    'liquidation_threshold': ((configuration >> 16) & ((1 << 16) - 1)) / 10000,
                    'liquidation_bonus': ((configuration >> 32) & ((1 << 16) - 1)) / 10000,
                    'decimals': (configuration >> 48) & ((1 << 8) - 1),
                    'active': bool((configuration >> 56) & 1),
                    'frozen': bool((configuration >> 57) & 1),
                    'borrowing_enabled': bool((configuration >> 58) & 1),
                    'stable_borrowing_enabled': bool((configuration >> 59) & 1),
                    'paused': bool((configuration >> 60) & 1),
                    'borrowable_in_isolation': bool((configuration >> 61) & 1),
                    'siloed_borrowing': bool((configuration >> 62) & 1),
                    'reserve_factor': ((configuration >> 64) & ((1 << 16) - 1)) / 10000,
                    'borrow_cap': (configuration >> 80) & ((1 << 16) - 1),
                    'supply_cap': (configuration >> 96) & ((1 << 16) - 1),
                    'liquidation_protocol_fee': ((configuration >> 112) & ((1 << 16) - 1)) / 10000,
                    'emode_category': (configuration >> 128) & ((1 << 8) - 1),
                    'debt_ceiling': (configuration >> 176) & ((1 << 40) - 1),
                }
                
                # Extract token addresses (last 40 chars = 20 bytes for address)
                a_token_address = '0x' + pool_data[512:576][-40:]
                stable_debt_token = '0x' + pool_data[576:640][-40:]
                variable_debt_token = '0x' + pool_data[640:704][-40:]
                last_update_timestamp = int(pool_data[384:448], 16) if len(pool_data) >= 448 else 0
                
                # Parse provider data (supply/debt amounts)
                provider_data = provider_result[2:] if provider_result.startswith('0x') else provider_result
                
                # Combine all data
                RAY = 10**27
                reserve_data = {
                    'asset_address': asset_address,
                    'symbol': symbol,
                    'network': network_config['name'],
                    'networkKey': network_key,
                    
                    # Configuration data
                    **config_data,
                    'a_token_address': a_token_address,
                    'stable_debt_token_address': stable_debt_token,
                    'variable_debt_token_address': variable_debt_token,
                    'last_update_timestamp': last_update_timestamp,
                    
                    # Supply/debt data from provider
                    'unbacked': str(int(provider_data[0:64], 16)),
                    'accruedToTreasury': str(int(provider_data[64:128], 16)),
                    'totalATokenSupply': str(int(provider_data[128:192], 16)),
                    'totalStableDebt': str(int(provider_data[192:256], 16)),
                    'totalVariableDebt': str(int(provider_data[256:320], 16)),
                    'liquidityRate': str(int(provider_data[320:384], 16)),
                    'variableBorrowRate': str(int(provider_data[384:448], 16)),
                    'stableBorrowRate': str(int(provider_data[448:512], 16)),
                    'averageStableRate': str(int(provider_data[512:576], 16)),
                    'liquidityIndex': str(int(provider_data[576:640], 16)),
                    'variableBorrowIndex': str(int(provider_data[640:704], 16)),
                    'lastUpdate': int(provider_data[704:768], 16) if len(provider_data) >= 768 else int(time.time()),
                    
                    # Converted rates
                    'current_liquidity_rate': float(int(provider_data[320:384], 16)) / RAY,
                    'current_variable_borrow_rate': float(int(provider_data[384:448], 16)) / RAY,
                    'liquidity_index': float(int(provider_data[576:640], 16)) / RAY,
                    'variable_borrow_index': float(int(provider_data[640:704], 16)) / RAY,
                }
                
                return reserve_data
                
            except Exception:
                return None
                
        except Exception:
            return None
    
    def fetch_network_data_optimized(
        self, 
        network_key: str, 
        network_config: Dict,
        max_asset_workers: int = 10
    ) -> Optional[List[Dict]]:
        """Fetch all assets for a network in parallel."""
        start_time = time.time()
        log_network_attempt(network_key, network_config['name'])
        
        # Get the best working RPC URL
        rpc_urls = [network_config['rpc']] + network_config.get('rpc_fallback', [])[:3]  # Limit to 4 URLs total
        
        working_url = None
        for url in rpc_urls:
            if self._optimized_rpc_call(url, "eth_blockNumber", []):
                working_url = url
                break
        
        if not working_url:
            log_network_failure(network_key, network_config['name'], "No working RPC URL")
            return None
        
        # Get reserves list
        pool_address = network_config.get('pool')
        result = self._optimized_rpc_call(
            working_url,
            "eth_call",
            [{
                "to": pool_address,
                "data": "0xd1946dbc"  # getReservesList()
            }, "latest"]
        )
        
        if not result or result == "0x":
            log_network_failure(network_key, network_config['name'], "Failed to get reserves list")
            return None
        
        # Parse reserves list
        try:
            reserves = self._parse_reserves_list(result)
            if not reserves:
                return None
        except Exception as e:
            log_network_failure(network_key, network_config['name'], f"Failed to parse reserves: {str(e)}")
            return None
        
        # Fetch all assets in parallel
        all_assets = []
        
        with ThreadPoolExecutor(max_workers=min(max_asset_workers, len(reserves))) as executor:
            future_to_asset = {
                executor.submit(
                    self.fetch_asset_data_parallel,
                    asset_address,
                    network_config,
                    working_url,
                    network_key
                ): asset_address
                for asset_address in reserves
            }
            
            for future in as_completed(future_to_asset, timeout=30):  # 30 second timeout for all assets
                asset_address = future_to_asset[future]
                try:
                    asset_data = future.result(timeout=5)  # 5 second timeout per asset
                    if asset_data:
                        all_assets.append(asset_data)
                except Exception:
                    continue
        
        # Log results
        elapsed = time.time() - start_time
        update_rpc_latency(working_url, elapsed * 1000)  # Convert to ms
        
        if all_assets:
            log_network_success(network_key, network_config['name'], len(all_assets), elapsed)
            return all_assets
        else:
            log_network_failure(network_key, network_config['name'], "No assets fetched")
            return None
    
    def _parse_reserves_list(self, result: str) -> List[str]:
        """Parse the reserves list from contract response."""
        if not result or result == "0x":
            return []
        
        data = result[2:] if result.startswith('0x') else result
        
        # Skip offset (first 32 bytes)
        data = data[64:]
        
        # Get array length
        array_length = int(data[:64], 16)
        data = data[64:]
        
        reserves = []
        for i in range(array_length):
            if len(data) >= 64:
                address = "0x" + data[24:64]  # Take last 20 bytes
                reserves.append(address)
                data = data[64:]
        
        return reserves
    
    def close(self):
        """Close the session to free resources."""
        self.session.close()


def fetch_aave_data_optimized(
    max_network_workers: int = 4,
    max_asset_workers: int = 10,
    save_reports: bool = True
) -> Tuple[Dict[str, List[Dict]], Dict[str, Any]]:
    """
    Fetch Aave data with optimized parallel processing.
    
    Args:
        max_network_workers: Max concurrent networks
        max_asset_workers: Max concurrent assets per network
        save_reports: Whether to save fetch reports
        
    Returns:
        Tuple of (data_dict, fetch_report)
    """
    from networks import get_active_networks
    
    fetcher = OptimizedGracefulDataFetcher()
    networks = get_active_networks()
    all_data = {}
    
    print(f"🚀 Starting optimized fetch from {len(networks)} networks")
    print(f"   Network workers: {max_network_workers}, Asset workers per network: {max_asset_workers}")
    
    start_time = time.time()
    
    # Fetch networks in parallel (same as before)
    with ThreadPoolExecutor(max_workers=max_network_workers) as executor:
        future_to_network = {
            executor.submit(
                fetcher.fetch_network_data_optimized,
                network_key,
                network_config,
                max_asset_workers
            ): network_key
            for network_key, network_config in networks.items()
        }
        
        for future in as_completed(future_to_network):
            network_key = future_to_network[future]
            try:
                network_data = future.result()
                if network_data:
                    all_data[network_key] = network_data
                    print(f"✅ {networks[network_key]['name']}: {len(network_data)} assets")
                else:
                    print(f"❌ {networks[network_key]['name']}: Failed")
            except Exception as e:
                print(f"❌ {networks[network_key]['name']}: {str(e)}")
    
    # Close session
    fetcher.close()
    
    # Create fetch report
    total_time = time.time() - start_time
    total_assets = sum(len(assets) for assets in all_data.values())
    
    fetch_report = {
        'fetch_summary': {
            'total_time': total_time,
            'total_assets': total_assets,
            'networks_attempted': len(networks),
            'networks_successful': len(all_data),
            'success_rate': len(all_data) / len(networks) if networks else 0,
            'avg_time_per_asset': total_time / total_assets if total_assets > 0 else 0
        },
        'network_results': {
            network_key: {
                'success': network_key in all_data,
                'asset_count': len(all_data.get(network_key, [])),
            }
            for network_key in networks
        }
    }
    
    print(f"\n⚡ Optimized fetch completed in {total_time:.1f}s")
    print(f"   {total_assets} assets from {len(all_data)} networks")
    print(f"   {total_time / total_assets:.3f}s per asset average")
    
    return all_data, fetch_report