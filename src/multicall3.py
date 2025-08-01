#!/usr/bin/env python3
"""
Multicall3 implementation for ultra-efficient blockchain data fetching.
Fetches all reserve data for a network in a SINGLE RPC call.
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
import requests


# Multicall3 is deployed at the same address on most chains
MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"

# Multicall3 deployment addresses for different networks
MULTICALL3_ADDRESSES = {
    'ethereum': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'polygon': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'avalanche': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'arbitrum': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'optimism': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'base': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'gnosis': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'bnb': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'fantom': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'metis': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'scroll': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'polygon-zkevm': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'celo': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'linea': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'zksync': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'mantle': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'sonic': '0xcA11bde05977b3631167028862bE2a173976CA11',
    'soneium': '0xcA11bde05977b3631167028862bE2a173976CA11',
    # Some networks might have different addresses or not support multicall3
    'harmony': None,  # Doesn't have multicall3
}


class Multicall3Client:
    """Ultra-efficient blockchain data fetching using Multicall3."""
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Aave-Multicall3/1.0'
        })
        
        # Function selectors
        self.SYMBOL_SELECTOR = '0x95d89b41'  # symbol()
        self.SYMBOL_UPPERCASE_SELECTOR = '0xf76f8d78'  # SYMBOL()
        self.GET_RESERVE_DATA_SELECTOR = '0x35ea6a75'  # getReserveData(address)
        
    def _rpc_call(self, url: str, method: str, params: List[Any], timeout: int = 30) -> Optional[Any]:
        """Make a single RPC call."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=timeout)
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    # Log the error for debugging
                    error_msg = result['error'].get('message', 'Unknown error')
                    error_code = result['error'].get('code', 'Unknown')
                    print(f"   ⚠️  RPC Error {error_code}: {error_msg}")
                    return None
        except Exception as e:
            print(f"   ⚠️  Request failed: {str(e)}")
            pass
        
        return None
    
    def _encode_multicall3(self, calls: List[Tuple[str, str]]) -> str:
        """
        Encode calls for Multicall3 aggregate3 function.
        
        Args:
            calls: List of (target_address, calldata) tuples
            
        Returns:
            Encoded calldata for aggregate3
        """
        # Multicall3.Call3 struct array
        # struct Call3 {
        #     address target;
        #     bool allowFailure;
        #     bytes callData;
        # }
        
        # aggregate3(Call3[] calldata calls)
        # Function selector: 0x82ad56cb
        selector = '82ad56cb'
        
        # Start encoding
        encoded_calls = selector
        
        # Offset to array data (always 0x20 for single param)
        encoded_calls += '0000000000000000000000000000000000000000000000000000000000000020'
        
        # Array length
        encoded_calls += f'{len(calls):064x}'
        
        # Array of Call3 structs - each struct needs an offset since it contains dynamic data
        # Calculate offsets for each struct
        struct_offsets = []
        current_struct_offset = len(calls) * 32  # After all the offset pointers
        
        for target, calldata in calls:
            struct_offsets.append(current_struct_offset)
            # Each struct has: address (32) + bool (32) + offset_to_bytes (32) + bytes_length (32) + bytes_data (padded)
            calldata_bytes = bytes.fromhex(calldata[2:] if calldata.startswith('0x') else calldata)
            padded_length = ((len(calldata_bytes) + 31) // 32) * 32
            current_struct_offset += 32 + 32 + 32 + 32 + padded_length
        
        # Write struct offsets
        for offset in struct_offsets:
            encoded_calls += f'{offset:064x}'
        
        # Write each struct
        for target, calldata in calls:
            calldata_bytes = bytes.fromhex(calldata[2:] if calldata.startswith('0x') else calldata)
            
            # address target
            encoded_calls += target[2:].lower().zfill(64)
            
            # bool allowFailure (true = 1)
            encoded_calls += '0000000000000000000000000000000000000000000000000000000000000001'
            
            # offset to callData (relative to start of struct)
            encoded_calls += '0000000000000000000000000000000000000000000000000000000000000060'
            
            # callData length
            encoded_calls += f'{len(calldata_bytes):064x}'
            
            # callData (padded to 32 bytes)
            calldata_hex = calldata_bytes.hex()
            padding_needed = ((len(calldata_hex) + 63) // 64) * 64 - len(calldata_hex)
            encoded_calls += calldata_hex + '0' * padding_needed
        
        return '0x' + encoded_calls
    
    def _decode_multicall3_result(self, result: str, num_calls: int) -> List[Tuple[bool, bytes]]:
        """
        Decode the result from aggregate3 call.
        
        Returns:
            List of (success, return_data) tuples
        """
        if not result or result == '0x':
            return [(False, b'')] * num_calls
        
        try:
            data = result[2:] if result.startswith('0x') else result
            
            # Skip offset to array (32 bytes)
            data = data[64:]
            
            # Get array length
            array_length = int(data[:64], 16)
            data = data[64:]
            
            if array_length != num_calls:
                return [(False, b'')] * num_calls
            
            results = []
            
            # Read Result struct offsets
            struct_offsets = []
            for i in range(array_length):
                offset = int(data[i*64:(i+1)*64], 16)
                struct_offsets.append(offset)
            
            # Process each Result struct
            for i, offset in enumerate(struct_offsets):
                # Calculate position in data (offset is relative to start of array data)
                struct_pos = 64 + (array_length * 64) + offset
                
                # Read Result struct: (bool success, bytes returnData)
                # Read success bool
                success = int(data[struct_pos:struct_pos+64], 16) == 1
                
                # Read returnData offset (relative to start of struct)
                returndata_offset = int(data[struct_pos+64:struct_pos+128], 16)
                
                if success and returndata_offset > 0:
                    # Calculate position of return data
                    returndata_pos = struct_pos + returndata_offset
                    
                    # Read length
                    length = int(data[returndata_pos:returndata_pos+64], 16)
                    
                    # Read data
                    return_data_hex = data[returndata_pos+64:returndata_pos+64+(length*2)]
                    return_data = bytes.fromhex(return_data_hex)
                    
                    results.append((True, return_data))
                else:
                    results.append((success, b''))
            
            return results
            
        except Exception as e:
            print(f"   ⚠️  Multicall decode error: {e}")
            return [(False, b'')] * num_calls
    
    def _parse_symbol(self, data: bytes) -> Optional[str]:
        """Parse symbol from return data."""
        if not data:
            return None
        
        try:
            hex_data = data.hex()
            
            # Handle different encoding formats
            if len(hex_data) >= 128:  # Dynamic string
                offset = int(hex_data[0:64], 16) * 2
                length = int(hex_data[offset:offset+64], 16) * 2
                symbol_hex = hex_data[offset+64:offset+64+length]
            else:  # Fixed bytes32
                symbol_hex = hex_data.rstrip('0')
            
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
                print(f"Multicall3 symbol correction: {asset_address} on {network_key} -> '{corrected_symbol}' (was '{symbol}')")
                return corrected_symbol
        
        return symbol
    
    def _parse_reserve_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse reserve data from AaveProtocolDataProvider.getReserveData return."""
        if not data or len(data) < 384:  # Minimum expected data
            return None
        
        try:
            hex_data = data.hex()
            
            # Parse according to AaveProtocolDataProvider.getReserveData return structure:
            # unbacked, accruedToTreasuryScaled, totalAToken, totalStableDebt, totalVariableDebt,
            # liquidityRate, variableBorrowRate, stableBorrowRate, averageStableRate,
            # liquidityIndex, variableBorrowIndex, lastUpdateTimestamp
            return {
                'unbacked': str(int(hex_data[0:64], 16)),
                'accruedToTreasury': str(int(hex_data[64:128], 16)),
                'totalATokenSupply': str(int(hex_data[128:192], 16)),
                'totalStableDebt': str(int(hex_data[192:256], 16)),
                'totalVariableDebt': str(int(hex_data[256:320], 16)),
                'liquidityRate': str(int(hex_data[320:384], 16)),
                'variableBorrowRate': str(int(hex_data[384:448], 16)),
                'stableBorrowRate': str(int(hex_data[448:512], 16)),
                'averageStableRate': str(int(hex_data[512:576], 16)),
                'liquidityIndex': str(int(hex_data[576:640], 16)),
                'variableBorrowIndex': str(int(hex_data[640:704], 16)),
                'lastUpdate': int(hex_data[704:768], 16) if len(hex_data) >= 768 else int(time.time())
            }
            
        except Exception:
            return None
    
    def fetch_network_data_multicall3(
        self,
        network_key: str,
        network_config: Dict[str, Any],
        rpc_url: str,
        reserves: List[str],
        multicall_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all network data in a SINGLE RPC call using Multicall3.
        
        This is the ultimate optimization - instead of 100+ RPC calls,
        we make just ONE call to get all the data.
        """
        if not reserves:
            return []
        
        # Get multicall address for this network
        if not multicall_address:
            multicall_address = MULTICALL3_ADDRESSES.get(network_key, MULTICALL3_ADDRESS)
        
        if not multicall_address:
            print(f"⚠️  Multicall3 not available for {network_key}")
            return []
        
        pool_data_provider = network_config['pool_data_provider']
        
        # Build all calls
        calls = []
        call_map = []  # Track what each call is for
        
        # For each reserve, add symbol and reserve data calls
        for reserve in reserves:
            # Add symbol() call
            calls.append((reserve, self.SYMBOL_SELECTOR))
            call_map.append(('symbol', reserve))
            
            # Add getReserveData(asset) call - using AaveProtocolDataProvider
            reserve_data_calldata = self.GET_RESERVE_DATA_SELECTOR + reserve[2:].lower().zfill(64)
            calls.append((pool_data_provider, reserve_data_calldata))
            call_map.append(('reserve_data', reserve))
        
        # Encode multicall
        encoded_call = self._encode_multicall3(calls)
        
        # Make THE SINGLE RPC CALL
        print(f"🚀 Fetching {len(reserves)} assets with 1 Multicall3 RPC call...")
        start_time = time.time()
        
        result = self._rpc_call(
            rpc_url,
            'eth_call',
            [{
                'to': multicall_address,
                'data': encoded_call
            }, 'latest'],
            timeout=60  # Give more time since this is a big call
        )
        
        elapsed = time.time() - start_time
        print(f"⚡ Multicall3 completed in {elapsed:.2f}s")
        
        if not result:
            print("❌ Multicall3 failed")
            return []
        
        # Decode results
        decoded_results = self._decode_multicall3_result(result, len(calls))
        
        # Process results
        asset_data_map = {}
        
        for i, (success, return_data) in enumerate(decoded_results):
            call_type, asset_address = call_map[i]
            
            if not success:
                continue
            
            if asset_address not in asset_data_map:
                asset_data_map[asset_address] = {
                    'asset_address': asset_address,
                    'network': network_config['name'],
                    'networkKey': network_key
                }
            
            if call_type == 'symbol':
                symbol = self._parse_symbol(return_data)
                if symbol:
                    # Apply symbol corrections for bridged USDC tokens
                    corrected_symbol = self._apply_symbol_corrections(symbol, asset_address, network_key)
                    asset_data_map[asset_address]['symbol'] = corrected_symbol
            elif call_type == 'reserve_data':
                reserve_data = self._parse_reserve_data(return_data)
                if reserve_data:
                    asset_data_map[asset_address].update(reserve_data)
        
        # Filter out incomplete data
        complete_assets = []
        for asset_data in asset_data_map.values():
            if 'symbol' in asset_data and 'totalATokenSupply' in asset_data:
                complete_assets.append(asset_data)
        
        print(f"✅ Multicall3 retrieved {len(complete_assets)}/{len(reserves)} assets")
        
        return complete_assets
    
    def test_multicall3(self, network_key: str = 'ethereum', rpc_url: str = 'https://eth.llamarpc.com'):
        """Test Multicall3 implementation."""
        print(f"\n🧪 Testing Multicall3 on {network_key}...")
        
        # Test with a few known assets
        test_assets = [
            '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
            '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT
        ]
        
        # Simple eth_blockNumber call via multicall
        calls = [(MULTICALL3_ADDRESS, '0x42cbb15c')]  # getBlockNumber()
        encoded = self._encode_multicall3(calls)
        
        result = self._rpc_call(
            rpc_url,
            'eth_call',
            [{
                'to': MULTICALL3_ADDRESS,
                'data': encoded
            }, 'latest']
        )
        
        if result:
            print("✅ Multicall3 is working!")
            decoded = self._decode_multicall3_result(result, 1)
            if decoded[0][0]:
                block_num = int(decoded[0][1].hex(), 16)
                print(f"   Current block: {block_num}")
        else:
            print("❌ Multicall3 test failed")


def test_multicall3_fetcher():
    """Test the Multicall3 fetcher."""
    client = Multicall3Client()
    client.test_multicall3()


if __name__ == "__main__":
    test_multicall3_fetcher()