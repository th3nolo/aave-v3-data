#!/usr/bin/env python3
"""
Batch RPC implementation for combining multiple Ethereum JSON-RPC calls.
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchRPCClient:
    """Client for making batch JSON-RPC calls to Ethereum nodes."""
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Aave-Batch-RPC/1.0'
        })
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=100,
            max_retries=0
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def batch_call(
        self, 
        url: str, 
        calls: List[Dict[str, Any]], 
        timeout: int = 30,
        chunk_size: int = 100
    ) -> List[Optional[Any]]:
        """
        Execute multiple RPC calls in a single batch request.
        
        Args:
            url: RPC endpoint URL
            calls: List of call dictionaries with method and params
            timeout: Request timeout in seconds
            chunk_size: Maximum calls per batch (some nodes have limits)
            
        Returns:
            List of results in the same order as calls
        """
        if not calls:
            return []
        
        # Split into chunks if needed
        results = [None] * len(calls)
        
        for chunk_start in range(0, len(calls), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(calls))
            chunk_calls = calls[chunk_start:chunk_end]
            
            # Build batch request
            batch_payload = []
            for i, call in enumerate(chunk_calls):
                batch_payload.append({
                    "jsonrpc": "2.0",
                    "id": chunk_start + i,
                    "method": call['method'],
                    "params": call['params']
                })
            
            try:
                response = self.session.post(
                    url,
                    json=batch_payload,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    batch_results = response.json()
                    
                    # Handle both single and batch responses
                    if isinstance(batch_results, dict):
                        batch_results = [batch_results]
                    
                    # Map results back by ID
                    for result in batch_results:
                        if 'id' in result and 'result' in result:
                            results[result['id']] = result['result']
                        elif 'id' in result and 'error' in result:
                            # Log error but continue
                            results[result['id']] = None
                            
            except Exception:
                # Batch failed, results remain None
                pass
        
        return results
    
    def get_reserves_data_batch(
        self,
        url: str,
        pool_data_provider: str,
        asset_addresses: List[str],
        timeout: int = 30
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Fetch reserve data for multiple assets in a single batch.
        
        Returns list of parsed reserve data dictionaries.
        """
        if not asset_addresses:
            return []
        
        # Build calls for all assets
        calls = []
        for asset in asset_addresses:
            calls.append({
                'method': 'eth_call',
                'params': [{
                    'to': pool_data_provider,
                    'data': f'0x35ea6a75000000000000000000000000{asset[2:].lower()}'
                }, 'latest']
            })
        
        # Execute batch call
        raw_results = self.batch_call(url, calls, timeout)
        
        # Parse results
        parsed_results = []
        for i, raw_result in enumerate(raw_results):
            if raw_result and raw_result != '0x':
                try:
                    parsed = self._parse_reserve_data(raw_result)
                    if parsed:
                        parsed['asset_address'] = asset_addresses[i]
                        parsed_results.append(parsed)
                    else:
                        parsed_results.append(None)
                except Exception:
                    parsed_results.append(None)
            else:
                parsed_results.append(None)
        
        return parsed_results
    
    def get_pool_reserves_data_batch(
        self,
        url: str,
        pool: str,
        asset_addresses: List[str],
        timeout: int = 30
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Fetch reserve configuration data from pool contract.
        
        Returns list of parsed configuration data dictionaries.
        """
        if not asset_addresses:
            return []
        
        # Build calls for all assets
        calls = []
        for asset in asset_addresses:
            calls.append({
                'method': 'eth_call',
                'params': [{
                    'to': pool,
                    'data': f'0x35ea6a75000000000000000000000000{asset[2:].lower()}'  # getReserveData(address)
                }, 'latest']
            })
        
        # Execute batch call
        raw_results = self.batch_call(url, calls, timeout)
        
        # Parse results
        parsed_results = []
        for i, raw_result in enumerate(raw_results):
            if raw_result and raw_result != '0x' and len(raw_result) >= 962:  # 0x + 480 chars minimum
                try:
                    parsed = self._parse_pool_reserve_data(raw_result)
                    if parsed:
                        parsed['asset_address'] = asset_addresses[i]
                        parsed_results.append(parsed)
                    else:
                        parsed_results.append(None)
                except Exception:
                    parsed_results.append(None)
            else:
                parsed_results.append(None)
        
        return parsed_results
    
    def _parse_pool_reserve_data(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse reserve data from Pool.getReserveData response."""
        if not result or result == '0x':
            return None
        
        try:
            data = result[2:] if result.startswith('0x') else result
            
            # Pool.getReserveData returns ReserveData struct:
            # configuration (uint256)
            # liquidityIndex (uint128) 
            # currentLiquidityRate (uint128)
            # variableBorrowIndex (uint128)
            # currentVariableBorrowRate (uint128)
            # currentStableBorrowRate (uint128)
            # lastUpdateTimestamp (uint40)
            # id (uint16)
            # aTokenAddress (address)
            # stableDebtTokenAddress (address)
            # variableDebtTokenAddress (address)
            # interestRateStrategyAddress (address)
            # accruedToTreasury (uint128)
            # unbacked (uint128)
            # isolationModeTotalDebt (uint128)
            
            # Extract configuration
            configuration = int(data[0:64], 16)
            
            # Decode configuration bitmap
            config_data = self._decode_configuration_bitmap(configuration)
            
            # Extract token addresses (last 40 chars = 20 bytes for address)
            a_token_address = '0x' + data[512:576][-40:]  # Field 8
            stable_debt_token = '0x' + data[576:640][-40:]  # Field 9
            variable_debt_token = '0x' + data[640:704][-40:]  # Field 10
            
            return {
                **config_data,
                'a_token_address': a_token_address,
                'stable_debt_token_address': stable_debt_token,
                'variable_debt_token_address': variable_debt_token,
                'last_update_timestamp': int(data[384:448], 16) if len(data) >= 448 else 0  # Field 6
            }
            
        except Exception:
            return None
    
    def _decode_configuration_bitmap(self, config: int) -> Dict[str, Any]:
        """Decode Aave V3 reserve configuration bitmap."""
        liquidation_bonus_raw = ((config >> 32) & ((1 << 16) - 1))
        return {
            'loan_to_value': (config & ((1 << 16) - 1)) / 10000,  # Bits 0-15
            'liquidation_threshold': ((config >> 16) & ((1 << 16) - 1)) / 10000,  # Bits 16-31
            'liquidation_bonus': (liquidation_bonus_raw / 10000) - 1.0 if liquidation_bonus_raw > 0 else 0.0,  # Bits 32-47 (subtract 1.0 to get actual bonus)
            'decimals': (config >> 48) & ((1 << 8) - 1),  # Bits 48-55
            'active': bool((config >> 56) & 1),  # Bit 56
            'frozen': bool((config >> 57) & 1),  # Bit 57
            'borrowing_enabled': bool((config >> 58) & 1),  # Bit 58
            'stable_borrowing_enabled': bool((config >> 59) & 1),  # Bit 59
            'paused': bool((config >> 60) & 1),  # Bit 60
            'borrowable_in_isolation': bool((config >> 61) & 1),  # Bit 61
            'siloed_borrowing': bool((config >> 62) & 1),  # Bit 62
            'flashloan_enabled': bool((config >> 63) & 1),  # Bit 63
            'reserve_factor': ((config >> 64) & ((1 << 16) - 1)) / 10000,  # Bits 64-79
            'borrow_cap': (config >> 80) & ((1 << 16) - 1),  # Bits 80-95
            'supply_cap': (config >> 96) & ((1 << 16) - 1),  # Bits 96-111
            'liquidation_protocol_fee': ((config >> 112) & ((1 << 16) - 1)) / 10000,  # Bits 112-127
            'emode_category': (config >> 128) & ((1 << 8) - 1),  # Bits 128-135
            'unbacked_mint_cap': (config >> 136) & ((1 << 40) - 1),  # Bits 136-175
            'debt_ceiling': (config >> 176) & ((1 << 40) - 1),  # Bits 176-215
        }
    
    def get_symbols_batch(
        self,
        url: str,
        asset_addresses: List[str],
        timeout: int = 30
    ) -> List[Optional[str]]:
        """
        Fetch symbols for multiple assets in a single batch.
        """
        if not asset_addresses:
            return []
        
        # Build calls for all assets (try symbol() method)
        calls = []
        for asset in asset_addresses:
            calls.append({
                'method': 'eth_call',
                'params': [{
                    'to': asset,
                    'data': '0x95d89b41'  # symbol()
                }, 'latest']
            })
        
        # Execute batch call
        raw_results = self.batch_call(url, calls, timeout)
        
        # Parse results
        symbols = []
        for i, raw_result in enumerate(raw_results):
            symbol = self._parse_symbol(raw_result)
            
            # If symbol() failed, try SYMBOL() as fallback
            if not symbol:
                fallback_call = [{
                    'method': 'eth_call',
                    'params': [{
                        'to': asset_addresses[i],
                        'data': '0xf76f8d78'  # SYMBOL()
                    }, 'latest']
                }]
                
                fallback_results = self.batch_call(url, fallback_call, timeout=10)
                if fallback_results and fallback_results[0]:
                    symbol = self._parse_symbol(fallback_results[0])
            
            symbols.append(symbol)
        
        return symbols
    
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
                
        except Exception:
            pass
        
        return None
    
    def _apply_symbol_corrections(self, symbol: Optional[str], asset_address: str, network_key: Optional[str] = None) -> Optional[str]:
        """Apply symbol corrections for bridged USDC tokens (same as utils.py)."""
        if not symbol or symbol != "USDC":
            return symbol
        
        # Known bridged USDC addresses that should be labeled as "USDC.e"
        bridged_usdc_addresses = {
            '0x2791bca1f2de4661ed88a30c99a7a9449aa84174': 'USDC.e',  # Polygon
            '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': 'USDC.e',  # Arbitrum  
            '0x7f5c764cbc14f9669b88837ca1490cca17c31607': 'USDC.e',  # Optimism
        }
        
        address_lower = asset_address.lower()
        for bridged_address, corrected_symbol in bridged_usdc_addresses.items():
            if address_lower == bridged_address.lower():
                print(f"BatchRPC symbol correction: {asset_address} on {network_key} -> '{corrected_symbol}' (was '{symbol}')")
                return corrected_symbol
        
        return symbol
    
    def _parse_reserve_data(self, result: str) -> Optional[Dict[str, Any]]:
        """Parse reserve data from AaveProtocolDataProvider response."""
        if not result or result == '0x':
            return None
        
        try:
            data = result[2:] if result.startswith('0x') else result
            
            # Parse according to AaveProtocolDataProvider.getReserveData return structure
            return {
                'unbacked': str(int(data[0:64], 16)),
                'accruedToTreasury': str(int(data[64:128], 16)),
                'totalATokenSupply': str(int(data[128:192], 16)),
                'totalStableDebt': str(int(data[192:256], 16)),
                'totalVariableDebt': str(int(data[256:320], 16)),
                'liquidityRate': str(int(data[320:384], 16)),
                'variableBorrowRate': str(int(data[384:448], 16)),
                'stableBorrowRate': str(int(data[448:512], 16)),
                'averageStableRate': str(int(data[512:576], 16)),
                'liquidityIndex': str(int(data[576:640], 16)),
                'variableBorrowIndex': str(int(data[640:704], 16)),
                'lastUpdate': int(data[704:768], 16) if len(data) >= 768 else int(time.time())
            }
            
        except Exception:
            return None
    
    def fetch_network_data_batch(
        self,
        network_key: str,
        network_config: Dict[str, Any],
        url: str,
        reserves: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch all data for a network using batch RPC calls.
        
        This method combines symbol, configuration, and reserve data fetching into minimal RPC calls.
        """
        if not reserves:
            return []
        
        # Fetch symbols, pool config data, and data provider data in parallel batches
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit batch calls
            symbols_future = executor.submit(
                self.get_symbols_batch,
                url,
                reserves,
                timeout=30
            )
            
            # Get configuration data from pool contract
            pool_data_future = executor.submit(
                self.get_pool_reserves_data_batch,
                url,
                network_config['pool'],
                reserves,
                timeout=30
            )
            
            # Get supply/debt data from pool_data_provider
            reserves_future = executor.submit(
                self.get_reserves_data_batch,
                url,
                network_config['pool_data_provider'],
                reserves,
                timeout=30
            )
            
            # Get results
            symbols = symbols_future.result()
            pool_data = pool_data_future.result()
            reserves_data = reserves_future.result()
        
        # Combine results
        combined_data = []
        for i, asset_address in enumerate(reserves):
            if i < len(symbols) and i < len(pool_data) and i < len(reserves_data):
                symbol = symbols[i]
                pool_reserve = pool_data[i]
                provider_data = reserves_data[i]
                
                if symbol and pool_reserve and provider_data:
                    # Apply symbol corrections for bridged USDC tokens
                    corrected_symbol = self._apply_symbol_corrections(symbol, asset_address, network_key)
                    
                    # Merge all data
                    asset_data = {
                        'asset_address': asset_address,
                        'symbol': corrected_symbol,
                        'network': network_config['name'],
                        'networkKey': network_key,
                    }
                    
                    # Add configuration data from pool
                    asset_data.update(pool_reserve)
                    
                    # Add supply/debt data from pool_data_provider
                    if provider_data:
                        asset_data.update({
                            'totalATokenSupply': provider_data.get('totalATokenSupply', '0'),
                            'totalStableDebt': provider_data.get('totalStableDebt', '0'),
                            'totalVariableDebt': provider_data.get('totalVariableDebt', '0'),
                            'liquidityRate': provider_data.get('liquidityRate', '0'),
                            'variableBorrowRate': provider_data.get('variableBorrowRate', '0'),
                            'stableBorrowRate': provider_data.get('stableBorrowRate', '0'),
                            'averageStableRate': provider_data.get('averageStableRate', '0'),
                            'liquidityIndex': provider_data.get('liquidityIndex', '0'),
                            'variableBorrowIndex': provider_data.get('variableBorrowIndex', '0'),
                            'lastUpdate': provider_data.get('lastUpdate', 0),
                            'unbacked': provider_data.get('unbacked', '0'),
                            'accruedToTreasury': provider_data.get('accruedToTreasury', '0'),
                        })
                    
                    # Convert rate fields to proper format
                    try:
                        RAY = 10**27
                        asset_data['current_liquidity_rate'] = float(asset_data.get('liquidityRate', '0')) / RAY
                        asset_data['current_variable_borrow_rate'] = float(asset_data.get('variableBorrowRate', '0')) / RAY
                        asset_data['liquidity_index'] = float(asset_data.get('liquidityIndex', '0')) / RAY
                        asset_data['variable_borrow_index'] = float(asset_data.get('variableBorrowIndex', '0')) / RAY
                    except:
                        asset_data['current_liquidity_rate'] = 0.0
                        asset_data['current_variable_borrow_rate'] = 0.0
                        asset_data['liquidity_index'] = 0.0
                        asset_data['variable_borrow_index'] = 0.0
                    
                    combined_data.append(asset_data)
        
        return combined_data
    
    def close(self):
        """Close the session."""
        self.session.close()


def test_batch_rpc():
    """Test the batch RPC implementation."""
    client = BatchRPCClient()
    
    # Test with mainnet
    url = "https://eth.llamarpc.com"
    
    # Test batch call for block number
    calls = [
        {'method': 'eth_blockNumber', 'params': []},
        {'method': 'eth_chainId', 'params': []},
        {'method': 'net_version', 'params': []}
    ]
    
    results = client.batch_call(url, calls, timeout=10)
    print("Batch RPC Test Results:")
    print(f"  Block Number: {results[0]}")
    print(f"  Chain ID: {results[1]}")
    print(f"  Network Version: {results[2]}")
    
    client.close()


if __name__ == "__main__":
    test_batch_rpc()