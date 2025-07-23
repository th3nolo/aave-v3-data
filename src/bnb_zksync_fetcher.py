#!/usr/bin/env python3
"""
Special fetcher for BNB and zkSync that only uses Pool contract data.
Since PoolDataProvider doesn't work on these networks, we'll get what we can from Pool alone.
"""

import time
from typing import Dict, List, Any, Optional
from batch_rpc import BatchRPCClient
from utils import get_method_id, _decode_configuration_bitmap, parse_address

class BnbZkSyncFetcher:
    """Fetcher for BNB and zkSync networks using only Pool contract."""
    
    def __init__(self):
        self.batch_client = BatchRPCClient()
    
    def fetch_network_data(self, network_key: str, network_config: Dict, reserves: List[str]) -> List[Dict[str, Any]]:
        """Fetch data using only Pool contract since PoolDataProvider doesn't work."""
        if not reserves:
            return []
        
        print(f"   🔧 Using BNB/zkSync special fetcher (Pool-only mode)")
        
        url = network_config['rpc']
        pool_address = network_config['pool']
        
        # Build batch calls for Pool.getReserveData
        pool_calls = []
        symbol_calls = []
        
        for asset in reserves:
            # getReserveData(address)
            pool_calls.append({
                'method': 'eth_call',
                'params': [{
                    'to': pool_address,
                    'data': '0x35ea6a75' + asset[2:].zfill(64)
                }, 'latest']
            })
            
            # symbol() for each asset
            symbol_calls.append({
                'method': 'eth_call',
                'params': [{
                    'to': asset,
                    'data': '0x95d89b41'
                }, 'latest']
            })
        
        # Execute batch calls
        start = time.time()
        pool_results = self.batch_client.batch_call(url, pool_calls, timeout=30)
        symbol_results = self.batch_client.batch_call(url, symbol_calls, timeout=30)
        elapsed = time.time() - start
        
        print(f"   ✅ Fetched {len(reserves)} assets in {elapsed:.2f}s (Pool-only mode)")
        
        # Parse results
        assets_data = []
        for i, asset_address in enumerate(reserves):
            if i < len(pool_results) and i < len(symbol_results):
                pool_data = self._parse_pool_reserve_data(pool_results[i])
                symbol = self._parse_symbol(symbol_results[i])
                
                if pool_data and symbol:
                    # Combine data
                    asset_data = {
                        'asset_address': asset_address,
                        'symbol': symbol,
                        'network': network_config['name'],
                        'networkKey': network_key,
                        
                        # From Pool contract
                        **pool_data,
                        
                        # Default values for missing PoolDataProvider data
                        'totalATokenSupply': '0',
                        'totalStableDebt': '0',
                        'totalVariableDebt': '0',
                        'liquidityRate': '0',
                        'variableBorrowRate': '0',
                        'stableBorrowRate': '0',
                        'averageStableRate': '0',
                        'unbacked': '0',
                        'accruedToTreasury': '0',
                        
                        # Set rates to 0 since we can't get them
                        'current_liquidity_rate': 0.0,
                        'current_variable_borrow_rate': 0.0,
                        'liquidity_index': 1.0,
                        'variable_borrow_index': 1.0,
                    }
                    
                    assets_data.append(asset_data)
        
        return assets_data
    
    def _parse_pool_reserve_data(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse Pool.getReserveData response."""
        if not result or result == '0x' or len(result) < 2:
            return None
        
        try:
            data = result[2:] if result.startswith('0x') else result
            
            # Pool.getReserveData returns ReserveData struct:
            # configuration (uint256) - contains all the bit-packed parameters
            # liquidityIndex, rates, etc (which we'll skip since they're not critical)
            # aTokenAddress, stableDebtTokenAddress, variableDebtTokenAddress
            
            if len(data) < 960:  # Need at least 15 fields * 64 chars
                return None
            
            # Extract configuration
            configuration = int(data[0:64], 16)
            config_data = _decode_configuration_bitmap(configuration)
            
            # Extract token addresses (fields 8, 9, 10)
            a_token_address = '0x' + data[512:576][-40:]
            stable_debt_token = '0x' + data[576:640][-40:]
            variable_debt_token = '0x' + data[640:704][-40:]
            
            # Extract last update timestamp (field 6)
            last_update = int(data[384:448], 16) if len(data) >= 448 else 0
            
            return {
                **config_data,
                'a_token_address': a_token_address,
                'stable_debt_token_address': stable_debt_token,
                'variable_debt_token_address': variable_debt_token,
                'last_update_timestamp': last_update,
            }
            
        except Exception as e:
            print(f"      Warning: Failed to parse pool data: {e}")
            return None
    
    def _parse_symbol(self, result: str) -> Optional[str]:
        """Parse symbol from contract response."""
        if not result or result == '0x':
            return None
        
        try:
            data = result[2:] if result.startswith('0x') else result
            
            # Handle different encoding formats
            if len(data) >= 128:  # Dynamic string
                offset = int(data[0:64], 16) * 2
                length = int(data[offset:offset+64], 16) * 2
                symbol_hex = data[offset+64:offset+64+length]
            else:  # Fixed bytes32
                symbol_hex = data.rstrip('0')
            
            if symbol_hex:
                return bytes.fromhex(symbol_hex).decode('utf-8').strip('\x00')
                
        except:
            pass
        
        return None
    
    def close(self):
        """Close the batch client."""
        self.batch_client.close()