"""
Core utility functions for blockchain interactions.
Provides method ID generation, RPC calls, and address parsing functionality.
"""

import hashlib
import json
import urllib.request
import urllib.parse
import time
import random
from typing import Dict, Any, Optional, List, Tuple


def get_method_id(signature: str) -> str:
    """
    Generate Keccak-256 method ID from function signature.
    
    Args:
        signature: Function signature like "getReservesList()"
        
    Returns:
        Hex string of first 4 bytes of Keccak-256 hash
    """
    # Precomputed method IDs for Aave V3 functions
    # These are the correct Keccak-256 hashes (NOT SHA3-256)
    PRECOMPUTED_METHOD_IDS = {
        "getReservesList()": "0xd1946dbc",
        "symbol()": "0x95d89b41",
        "getReserveData(address)": "0x35ea6a75",
        "decimals()": "0x313ce567",
        "totalSupply()": "0x18160ddd",
        "balanceOf(address)": "0x70a08231",
        "name()": "0x06fdde03",
    }
    
    if signature in PRECOMPUTED_METHOD_IDS:
        return PRECOMPUTED_METHOD_IDS[signature]
    else:
        # For unknown signatures, raise an error instead of using wrong hash
        raise ValueError(f"Unknown method signature: {signature}. Please add its Keccak-256 hash to PRECOMPUTED_METHOD_IDS.")


class RPCError(Exception):
    """Custom exception for RPC-related errors."""
    def __init__(self, message: str, error_type: str = "unknown", retry_after: Optional[int] = None):
        super().__init__(message)
        self.error_type = error_type
        self.retry_after = retry_after


class NetworkError(Exception):
    """Custom exception for network-related errors."""
    def __init__(self, message: str, error_type: str = "network"):
        super().__init__(message)
        self.error_type = error_type


def rpc_call_with_retry(
    url: str, 
    method: str, 
    params: list, 
    request_id: int = 1,
    max_retries: int = 3,
    fallback_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Make JSON-RPC call with exponential backoff retry logic and fallback endpoints.
    
    Args:
        url: Primary RPC endpoint URL
        method: RPC method name (e.g., "eth_call")
        params: List of parameters for the method
        request_id: Request ID for JSON-RPC
        max_retries: Maximum number of retry attempts (default: 3)
        fallback_urls: List of fallback RPC URLs to try if primary fails
        
    Returns:
        Dictionary containing RPC response
        
    Raises:
        RPCError: If all RPC attempts fail
        NetworkError: If network connectivity issues persist
    """
    all_urls = [url]
    if fallback_urls:
        all_urls.extend(fallback_urls)
    
    last_exception = None
    
    for url_index, current_url in enumerate(all_urls):
        for attempt in range(max_retries):
            try:
                result = _make_single_rpc_call(current_url, method, params, request_id)
                
                # Log successful call if it wasn't the first attempt
                if attempt > 0 or url_index > 0:
                    print(f"RPC call succeeded on attempt {attempt + 1} using {current_url}")
                
                return result
                
            except RPCError as e:
                last_exception = e
                
                # Handle specific error types
                if e.error_type == "rate_limit":
                    # For rate limiting, wait longer and try fallback sooner
                    if e.retry_after:
                        wait_time = min(e.retry_after, 60)  # Cap at 60 seconds
                    else:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), 30)
                    
                    print(f"Rate limited on {current_url}, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries - 1:  # Don't wait on last attempt
                        time.sleep(wait_time)
                    continue
                    
                elif e.error_type == "server_error":
                    # For server errors, use exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                        print(f"Server error on {current_url}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    continue
                    
                elif e.error_type == "invalid_request":
                    # For invalid requests, don't retry - fail fast
                    print(f"Invalid request error on {current_url}: {e}")
                    break
                    
                else:
                    # For other errors, use standard exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), 5)
                        print(f"RPC error on {current_url}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries}): {e}")
                        time.sleep(wait_time)
                    continue
                    
            except NetworkError as e:
                last_exception = e
                
                # For network errors, try exponential backoff
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                    print(f"Network error on {current_url}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                continue
                
            except Exception as e:
                last_exception = e
                print(f"Unexpected error on {current_url} (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), 5)
                    time.sleep(wait_time)
                continue
        
        # If we get here, all retries for this URL failed
        if url_index < len(all_urls) - 1:
            print(f"All retries failed for {current_url}, trying fallback endpoint...")
    
    # If we get here, all URLs and retries failed
    if isinstance(last_exception, (RPCError, NetworkError)):
        raise last_exception
    else:
        raise RPCError(f"All RPC endpoints failed after {max_retries} retries each. Last error: {last_exception}")


def _make_single_rpc_call(url: str, method: str, params: list, request_id: int = 1) -> Dict[str, Any]:
    """
    Make a single JSON-RPC call without retry logic.
    
    Args:
        url: RPC endpoint URL
        method: RPC method name
        params: List of parameters
        request_id: Request ID for JSON-RPC
        
    Returns:
        Dictionary containing RPC response
        
    Raises:
        RPCError: For RPC-specific errors
        NetworkError: For network connectivity issues
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Aave-V3-Data-Fetcher/1.0'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 429:
                # Rate limiting
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise RPCError(
                    f"Rate limited by {url}", 
                    error_type="rate_limit", 
                    retry_after=retry_after_int
                )
            
            if response.status >= 500:
                # Server error
                raise RPCError(
                    f"Server error {response.status} from {url}", 
                    error_type="server_error"
                )
            
            if response.status >= 400:
                # Client error
                raise RPCError(
                    f"Client error {response.status} from {url}", 
                    error_type="client_error"
                )
            
            result = json.loads(response.read().decode('utf-8'))
            
        if 'error' in result:
            error_info = result['error']
            error_code = error_info.get('code', 0) if isinstance(error_info, dict) else 0
            error_message = error_info.get('message', str(error_info)) if isinstance(error_info, dict) else str(error_info)
            
            # Classify RPC errors
            if error_code == -32602:
                error_type = "invalid_request"
            elif error_code == -32000:
                error_type = "server_error"
            elif "rate" in error_message.lower() or "limit" in error_message.lower():
                error_type = "rate_limit"
            else:
                error_type = "rpc_error"
            
            raise RPCError(f"RPC Error {error_code}: {error_message}", error_type=error_type)
            
        return result
        
    except urllib.error.HTTPError as e:
        if e.code == 429:
            retry_after = e.headers.get('Retry-After')
            retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise RPCError(f"Rate limited by {url}", error_type="rate_limit", retry_after=retry_after_int)
        elif e.code >= 500:
            raise RPCError(f"Server error {e.code} from {url}", error_type="server_error")
        else:
            raise RPCError(f"HTTP error {e.code} from {url}", error_type="client_error")
            
    except urllib.error.URLError as e:
        if "timeout" in str(e).lower():
            raise NetworkError(f"Timeout connecting to {url}: {e}")
        elif "connection" in str(e).lower():
            raise NetworkError(f"Connection error to {url}: {e}")
        else:
            raise NetworkError(f"Network error connecting to {url}: {e}")
            
    except json.JSONDecodeError as e:
        raise RPCError(f"Invalid JSON response from {url}: {e}", error_type="invalid_response")
    
    except Exception as e:
        raise RPCError(f"Unexpected error calling {url}: {e}", error_type="unknown")


def rpc_call(url: str, method: str, params: list, request_id: int = 1) -> Dict[str, Any]:
    """
    Make JSON-RPC call to blockchain endpoint (backward compatibility wrapper).
    
    Args:
        url: RPC endpoint URL
        method: RPC method name (e.g., "eth_call")
        params: List of parameters for the method
        request_id: Request ID for JSON-RPC
        
    Returns:
        Dictionary containing RPC response
        
    Raises:
        Exception: If RPC call fails or returns error
    """
    try:
        return rpc_call_with_retry(url, method, params, request_id, max_retries=3)
    except (RPCError, NetworkError) as e:
        raise Exception(str(e))


def parse_address(hex_str: str) -> str:
    """
    Parse Ethereum address from hex string response.
    
    Args:
        hex_str: Hex string that may contain address data
        
    Returns:
        Checksummed Ethereum address
    """
    # Remove 0x prefix if present
    if hex_str.startswith('0x'):
        hex_str = hex_str[2:]
    
    # Extract last 40 characters (20 bytes) for address
    if len(hex_str) >= 40:
        address_hex = hex_str[-40:]
        return '0x' + address_hex
    
    raise ValueError(f"Invalid hex string for address: {hex_str}")


def encode_call_data(method_id: str, params: list = None) -> str:
    """
    Encode contract call data with method ID and parameters.
    
    Args:
        method_id: 4-byte method identifier
        params: List of parameters to encode (currently supports basic types)
        
    Returns:
        Hex-encoded call data
    """
    if params is None:
        params = []
    
    # For now, just return method ID (parameters encoding would be more complex)
    # This is sufficient for view functions with no parameters
    return method_id


def decode_hex_to_int(hex_str: str) -> int:
    """
    Decode hex string to integer.
    
    Args:
        hex_str: Hex string with or without 0x prefix
        
    Returns:
        Integer value
    """
    if hex_str.startswith('0x'):
        hex_str = hex_str[2:]
    
    return int(hex_str, 16) if hex_str else 0


def format_address(address: str) -> str:
    """
    Format address to standard checksum format.
    
    Args:
        address: Ethereum address string
        
    Returns:
        Properly formatted address
    """
    if not address.startswith('0x'):
        address = '0x' + address
    
    # Remove any extra characters and ensure proper length
    if address.startswith('0x'):
        hex_part = address[2:]
    else:
        hex_part = address
    
    # Pad with zeros if too short, truncate if too long
    hex_part = hex_part.zfill(40)[-40:]
    
    return '0x' + hex_part.lower()


def get_reserves(pool_address: str, rpc_url: str, fallback_urls: Optional[List[str]] = None, network_key: Optional[str] = None) -> list:
    """
    Retrieve list of reserve assets from Aave V3 Pool contract with retry logic.
    
    Args:
        pool_address: Address of the Aave V3 Pool contract
        rpc_url: Primary RPC endpoint URL for the network
        fallback_urls: Optional list of fallback RPC URLs
        
    Returns:
        List of asset addresses
        
    Raises:
        Exception: If RPC call fails or response is invalid
    """
    try:
        # Generate method ID for getReservesList()
        method_id = get_method_id("getReservesList()")
        
        # Prepare eth_call parameters
        call_params = {
            "to": pool_address,
            "data": method_id
        }
        
        # Make RPC call with retry logic
        result = rpc_call_with_retry(
            rpc_url, 
            "eth_call", 
            [call_params, "latest"],
            fallback_urls=fallback_urls
        )
        
        if 'result' not in result:
            raise Exception("No result in RPC response")
        
        response_data = result['result']
        
        # Record successful request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, True)
            except ImportError:
                pass  # Monitoring not available
        
        # Decode dynamic array response
        return _decode_address_array(response_data)
        
    except (RPCError, NetworkError) as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        raise Exception(f"Failed to get reserves from {pool_address}: {e}")
    except Exception as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        raise Exception(f"Unexpected error getting reserves: {e}")


def _decode_address_array(hex_data: str) -> list:
    """
    Decode dynamic array of addresses from contract response.
    
    Args:
        hex_data: Hex-encoded contract response
        
    Returns:
        List of decoded addresses
    """
    if not hex_data or hex_data == '0x':
        return []
    
    # Remove 0x prefix
    if hex_data.startswith('0x'):
        hex_data = hex_data[2:]
    
    # Validate hex data
    if not all(c in '0123456789abcdefABCDEF' for c in hex_data):
        raise Exception("Invalid hex characters in response data")
    
    # Dynamic arrays are encoded as:
    # - First 32 bytes: offset to array data (usually 0x20 = 32)
    # - Next 32 bytes: array length
    # - Following bytes: array elements (32 bytes each for addresses)
    
    if len(hex_data) < 128:  # Need at least offset + length
        if len(hex_data) < 64:
            raise Exception("Response data too short for valid array")
        return []
    
    try:
        # Skip offset (first 64 hex chars = 32 bytes)
        # Read array length (next 64 hex chars = 32 bytes)
        length_hex = hex_data[64:128]
        array_length = int(length_hex, 16)
        
        if array_length == 0:
            return []
        
        # Check if we have enough data for all addresses
        expected_data_length = 128 + (array_length * 64)
        if len(hex_data) < expected_data_length:
            raise Exception(f"Insufficient data for {array_length} addresses")
        
        # Extract addresses (each address is 32 bytes = 64 hex chars)
        addresses = []
        start_pos = 128  # Start after offset and length
        
        for i in range(array_length):
            # Each address is padded to 32 bytes, address is in last 20 bytes
            addr_start = start_pos + (i * 64)
            addr_end = addr_start + 64
            
            if addr_end > len(hex_data):
                raise Exception(f"Data truncated at address {i}")
                
            addr_hex = hex_data[addr_start:addr_end]
            # Extract last 40 characters (20 bytes) for the address
            address = '0x' + addr_hex[-40:]
            addresses.append(address)
        
        return addresses
        
    except ValueError as e:
        raise Exception(f"Failed to decode address array: invalid hex value - {e}")
    except IndexError as e:
        raise Exception(f"Failed to decode address array: data structure error - {e}")


def get_asset_symbol(asset_address: str, rpc_url: str, fallback_urls: Optional[List[str]] = None, network_key: Optional[str] = None) -> str:
    """
    Retrieve ERC20 token symbol from contract with retry logic.
    
    Args:
        asset_address: Address of the ERC20 token contract
        rpc_url: Primary RPC endpoint URL for the network
        fallback_urls: Optional list of fallback RPC URLs
        
    Returns:
        Token symbol string (fallback to address-based identifier if retrieval fails)
    """
    try:
        # Generate method ID for symbol()
        method_id = get_method_id("symbol()")
        
        # Prepare eth_call parameters
        call_params = {
            "to": asset_address,
            "data": method_id
        }
        
        # Make RPC call with retry logic
        result = rpc_call_with_retry(
            rpc_url, 
            "eth_call", 
            [call_params, "latest"],
            fallback_urls=fallback_urls
        )
        
        if 'result' not in result:
            print(f"Warning: No result in RPC response for symbol of {asset_address}")
            return f"TOKEN_{asset_address[-8:].upper()}"
        
        response_data = result['result']
        
        # Decode string response
        symbol = _decode_string_response(response_data)
        
        # Check if decoding failed and return fallback
        error_codes = ["UNKNOWN", "EMPTY", "INVALID", "NON_UTF8", "DECODE_ERROR", "PARSE_ERROR"]
        if symbol in error_codes:
            print(f"Warning: Symbol decoding failed for {asset_address}, using fallback")
            return f"TOKEN_{asset_address[-8:].upper()}"
        
        # Record successful request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, True)
            except ImportError:
                pass  # Monitoring not available
        
        return symbol
        
    except (RPCError, NetworkError) as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        print(f"Warning: Failed to get symbol for {asset_address}: {e}")
        return f"TOKEN_{asset_address[-8:].upper()}"
    except Exception as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        print(f"Warning: Unexpected error getting symbol for {asset_address}: {e}")
        return f"TOKEN_{asset_address[-8:].upper()}"


def _decode_string_response(hex_data: str) -> str:
    """
    Decode string response from contract call.
    Handles both standard string encoding and bytes32 format.
    
    Args:
        hex_data: Hex-encoded contract response
        
    Returns:
        Decoded string with UTF-8 error handling
    """
    if not hex_data or hex_data == '0x':
        return "UNKNOWN"
    
    # Remove 0x prefix
    if hex_data.startswith('0x'):
        hex_data = hex_data[2:]
    
    # Check if this is bytes32 format (64 chars, no dynamic encoding)
    if len(hex_data) == 64:
        try:
            # Try to decode as bytes32
            # Remove trailing zeros
            trimmed = hex_data.rstrip('0')
            if trimmed:
                decoded = bytes.fromhex(trimmed).decode('utf-8', errors='ignore')
                # Check if it's a reasonable symbol
                if decoded and len(decoded) <= 20:  # Increased limit
                    # Allow alphanumeric, dots, underscores, dashes, spaces
                    valid_chars = all(c.isalnum() or c in '._- ' for c in decoded)
                    if valid_chars:
                        return decoded
        except:
            pass
    
    # For dynamic strings, we need at least offset + length (128 chars)
    # But some tokens have extra padding, so we'll be more lenient
    if len(hex_data) < 128:
        return "UNKNOWN"
    
    try:
        # String encoding:
        # - First 32 bytes: offset to string data (usually 0x20 = 32)
        # - Next 32 bytes: string length
        # - Following bytes: string data (padded to 32-byte boundaries)
        
        # Skip offset (first 64 hex chars = 32 bytes)
        # Read string length (next 64 hex chars = 32 bytes)
        length_hex = hex_data[64:128]
        string_length = int(length_hex, 16)
        
        if string_length == 0:
            return "EMPTY"
        
        # Extract string data
        string_start = 128
        string_end = string_start + (string_length * 2)  # 2 hex chars per byte
        
        if string_end > len(hex_data):
            # Try to extract what we can
            string_end = len(hex_data)
        
        string_hex = hex_data[string_start:string_end]
        
        # Convert hex to bytes
        string_bytes = bytes.fromhex(string_hex)
        
        # Decode with UTF-8 error handling
        try:
            symbol = string_bytes.decode('utf-8').strip('\x00')
            # Remove any null bytes and whitespace
            symbol = symbol.replace('\x00', '').strip()
            
            # Handle special cases before validation
            if symbol == 'USD₮0':
                return 'USDT'  # Arbitrum USDT special case
            elif symbol == 'USDt₮':
                return 'USDT'  # Celo USDT special case
            elif symbol == 'USD₮':
                return 'USDT'  # Celo USDT special case (without 't')
            
            # Validate symbol (should be alphanumeric with dots, underscores, dashes, spaces)
            if symbol and len(symbol) <= 30:  # Increased limit for LP tokens
                # Allow alphanumeric, dots, underscores, dashes, spaces
                valid_chars = all(c.isalnum() or c in '._- ' for c in symbol)
                if valid_chars:
                    return symbol
            return "INVALID"
                
        except UnicodeDecodeError:
            # Try to extract ASCII characters only
            try:
                # Decode with errors='ignore' to skip problematic characters
                symbol = string_bytes.decode('utf-8', errors='ignore').strip('\x00')
                symbol = symbol.replace('\x00', '').strip()
                
                # Filter out non-ASCII characters (like the special 𝔸 in USDt(𝔸))
                symbol = ''.join(c for c in symbol if ord(c) < 128)
                
                # Clean up common patterns
                if symbol.startswith('USDt(') and symbol.endswith(')'):
                    symbol = 'USDT'  # Fix for Arbitrum USDT
                elif symbol == 'USD0':
                    symbol = 'USDT'  # Fix for Arbitrum USDT (USD₮0)
                elif symbol == 'USDt':
                    symbol = 'USDT'  # Fix for Celo USDT (USDt₮)
                elif symbol == 'USD':
                    symbol = 'USDT'  # Fix for Celo USDT (USD₮)
                
                # Validate symbol (should be alphanumeric with dots, underscores, dashes, spaces)
                if symbol and len(symbol) <= 30:  # Increased limit for LP tokens
                    # Allow alphanumeric, dots, underscores, dashes, spaces
                    valid_chars = all(c.isalnum() or c in '._- ' for c in symbol)
                    if valid_chars:
                        return symbol
                return "NON_UTF8"
                    
            except Exception:
                return "DECODE_ERROR"
        
    except (ValueError, IndexError) as e:
        return "PARSE_ERROR"


def get_reserve_data(asset_address: str, pool_address: str, rpc_url: str, fallback_urls: Optional[List[str]] = None, network_key: Optional[str] = None) -> dict:
    """
    Retrieve and decode reserve data from Aave V3 Pool contract with retry logic.
    
    Args:
        asset_address: Address of the reserve asset
        pool_address: Address of the Aave V3 Pool contract
        rpc_url: Primary RPC endpoint URL for the network
        fallback_urls: Optional list of fallback RPC URLs
        
    Returns:
        Dictionary containing decoded reserve data
        
    Raises:
        Exception: If RPC call fails or data cannot be decoded
    """
    try:
        # Generate method ID for getReserveData(address)
        method_id = get_method_id("getReserveData(address)")
        
        # Encode the asset address parameter (32 bytes padded)
        asset_param = asset_address[2:].zfill(64)  # Remove 0x and pad to 64 chars
        call_data = method_id + asset_param
        
        # Prepare eth_call parameters
        call_params = {
            "to": pool_address,
            "data": call_data
        }
        
        # Make RPC call with retry logic
        result = rpc_call_with_retry(
            rpc_url, 
            "eth_call", 
            [call_params, "latest"],
            fallback_urls=fallback_urls
        )
        
        if 'result' not in result:
            raise Exception("No result in RPC response")
        
        response_data = result['result']
        
        # Record successful request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, True)
            except ImportError:
                pass  # Monitoring not available
        
        # Decode reserve data response
        return _decode_reserve_data_response(response_data)
        
    except (RPCError, NetworkError) as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        raise Exception(f"Failed to get reserve data for {asset_address}: {e}")
    except Exception as e:
        # Record failed request for monitoring
        if network_key:
            try:
                from monitoring import record_network_request
                record_network_request(network_key, False, str(e))
            except ImportError:
                pass  # Monitoring not available
        
        raise Exception(f"Unexpected error getting reserve data: {e}")


def _decode_reserve_data_response(hex_data: str) -> dict:
    """
    Decode reserve data response from getReserveData call.
    
    The response contains a struct with the following fields:
    - configuration (uint256): Packed configuration bitmap
    - liquidityIndex (uint128): Current liquidity index
    - currentLiquidityRate (uint128): Current liquidity rate
    - variableBorrowIndex (uint128): Current variable borrow index
    - currentVariableBorrowRate (uint128): Current variable borrow rate
    - currentStableBorrowRate (uint128): Current stable borrow rate
    - lastUpdateTimestamp (uint40): Last update timestamp
    - id (uint16): Reserve ID
    - aTokenAddress (address): aToken contract address
    - stableDebtTokenAddress (address): Stable debt token address
    - variableDebtTokenAddress (address): Variable debt token address
    - interestRateStrategyAddress (address): Interest rate strategy address
    - accruedToTreasury (uint128): Accrued to treasury
    - unbacked (uint128): Unbacked amount
    
    Args:
        hex_data: Hex-encoded contract response
        
    Returns:
        Dictionary containing decoded reserve data
    """
    if not hex_data or hex_data == '0x':
        raise Exception("Empty response data")
    
    # Remove 0x prefix
    if hex_data.startswith('0x'):
        hex_data = hex_data[2:]
    
    # Each field is 32 bytes (64 hex chars), extract them
    if len(hex_data) < 64 * 15:  # Need at least 15 fields
        raise Exception("Response data too short for reserve data struct")
    
    try:
        # Extract fields (each 64 hex chars = 32 bytes)
        fields = []
        for i in range(15):
            start = i * 64
            end = start + 64
            field_hex = hex_data[start:end]
            fields.append(field_hex)
        
        # Parse individual fields
        configuration = int(fields[0], 16)
        liquidity_index = int(fields[1], 16)
        current_liquidity_rate = int(fields[2], 16)
        variable_borrow_index = int(fields[3], 16)
        current_variable_borrow_rate = int(fields[4], 16)
        current_stable_borrow_rate = int(fields[5], 16)
        last_update_timestamp = int(fields[6], 16)
        reserve_id = int(fields[7], 16)
        a_token_address = '0x' + fields[8][-40:]  # Last 20 bytes
        stable_debt_token_address = '0x' + fields[9][-40:]
        variable_debt_token_address = '0x' + fields[10][-40:]
        interest_rate_strategy_address = '0x' + fields[11][-40:]
        accrued_to_treasury = int(fields[12], 16)
        unbacked = int(fields[13], 16)
        # Note: isolation_mode_total_debt was removed in current Aave V3
        
        # Decode configuration bitmap
        config_data = _decode_configuration_bitmap(configuration)
        
        # Convert rates and indices to decimal format
        # Aave uses 27-decimal precision (RAY = 10^27)
        RAY = 10**27
        
        return {
            # Configuration bitmap data
            **config_data,
            
            # Rate and index data (converted from RAY precision)
            'liquidity_index': liquidity_index / RAY,
            'current_liquidity_rate': current_liquidity_rate / RAY,
            'variable_borrow_index': variable_borrow_index / RAY,
            'current_variable_borrow_rate': current_variable_borrow_rate / RAY,
            'current_stable_borrow_rate': current_stable_borrow_rate / RAY,
            
            # Other fields
            'last_update_timestamp': last_update_timestamp,
            'reserve_id': reserve_id,
            'a_token_address': a_token_address,
            'stable_debt_token_address': stable_debt_token_address,
            'variable_debt_token_address': variable_debt_token_address,
            'interest_rate_strategy_address': interest_rate_strategy_address,
            'accrued_to_treasury': accrued_to_treasury / RAY,
            'unbacked': unbacked / RAY
        }
        
    except (ValueError, IndexError) as e:
        raise Exception(f"Failed to decode reserve data: {e}")


def _decode_configuration_bitmap(config: int) -> dict:
    """
    Decode Aave V3 reserve configuration bitmap.
    
    Bitmap layout:
    - Bits 0-15: LTV (Loan to Value)
    - Bits 16-31: Liquidation Threshold
    - Bits 32-47: Liquidation Bonus
    - Bits 48-55: Decimals
    - Bit 56: Active
    - Bit 57: Frozen
    - Bit 58: Borrowing Enabled
    - Bit 59: Stable Rate Borrowing Enabled
    - Bit 60: Paused
    - Bit 61: Borrowable in Isolation
    - Bit 62: Siloed Borrowing
    - Bit 63: Flashloan Enabled
    - Bits 64-79: Reserve Factor
    - Bits 80-95: Borrow Cap
    - Bits 96-111: Supply Cap
    - Bits 112-127: Liquidation Protocol Fee
    - Bits 128-167: eMode Category
    - Bits 168-207: Unbacked Mint Cap
    - Bits 208-247: Debt Ceiling
    
    Args:
        config: Configuration bitmap as integer
        
    Returns:
        Dictionary containing decoded configuration parameters
    """
    def extract_bits(value: int, start_bit: int, num_bits: int) -> int:
        """Extract specific bits from integer."""
        mask = (1 << num_bits) - 1
        return (value >> start_bit) & mask
    
    # Extract values from bitmap
    ltv = extract_bits(config, 0, 16)
    liquidation_threshold = extract_bits(config, 16, 16)
    liquidation_bonus = extract_bits(config, 32, 16)
    decimals = extract_bits(config, 48, 8)
    
    # Boolean flags
    active = bool(extract_bits(config, 56, 1))
    frozen = bool(extract_bits(config, 57, 1))
    borrowing_enabled = bool(extract_bits(config, 58, 1))
    stable_borrowing_enabled = bool(extract_bits(config, 59, 1))
    paused = bool(extract_bits(config, 60, 1))
    borrowable_in_isolation = bool(extract_bits(config, 61, 1))
    siloed_borrowing = bool(extract_bits(config, 62, 1))
    flashloan_enabled = bool(extract_bits(config, 63, 1))
    
    # Additional parameters
    reserve_factor = extract_bits(config, 64, 16)
    borrow_cap = extract_bits(config, 80, 16)
    supply_cap = extract_bits(config, 96, 16)
    liquidation_protocol_fee = extract_bits(config, 112, 16)
    emode_category = extract_bits(config, 128, 8)
    unbacked_mint_cap = extract_bits(config, 168, 40)
    debt_ceiling = extract_bits(config, 208, 40)
    
    # Convert percentage values (stored as basis points, 1% = 100 bp)
    # LTV, LT, LB, Reserve Factor, and Liquidation Protocol Fee are in basis points
    return {
        'loan_to_value': ltv / 10000.0,  # Convert from basis points to decimal
        'liquidation_threshold': liquidation_threshold / 10000.0,
        'liquidation_bonus': (liquidation_bonus / 10000.0) - 1.0 if liquidation_bonus > 0 else 0.0,
        'decimals': decimals,
        'active': active,
        'frozen': frozen,
        'borrowing_enabled': borrowing_enabled,
        'stable_borrowing_enabled': stable_borrowing_enabled,
        'paused': paused,
        'borrowable_in_isolation': borrowable_in_isolation,
        'siloed_borrowing': siloed_borrowing,
        'flashloan_enabled': flashloan_enabled,
        'reserve_factor': reserve_factor / 10000.0,
        'borrow_cap': borrow_cap,
        'supply_cap': supply_cap,
        'liquidation_protocol_fee': liquidation_protocol_fee / 10000.0,
        'emode_category': emode_category,
        'unbacked_mint_cap': unbacked_mint_cap,
        'debt_ceiling': debt_ceiling
    }