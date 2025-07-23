"""
Network configuration and validation for Aave V3 supported chains.
Contains comprehensive network definitions and validation utilities.
"""

import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from utils import rpc_call


# Comprehensive Aave V3 networks configuration for 2025 with extensive public RPC endpoints
AAVE_V3_NETWORKS = {
    'ethereum': {
        'name': 'Ethereum Mainnet',
        'chain_id': 1,
        'rpc': 'https://ethereum.publicnode.com',
        'rpc_fallback': [
            'https://eth-mainnet.public.blastapi.io',
            'https://eth.drpc.org',
            'https://eth.llamarpc.com',
            'https://cloudflare-eth.com/v1/mainnet',
            'https://rpc.flashbots.net',
            'https://1rpc.io/eth',
            'https://eth.rpc.hypersync.xyz',
            'https://endpoints.omniatech.io/v1/eth/mainnet/public',
            'https://rpc.ankr.com/eth',
            'https://eth-rpc.gateway.pokt.network',
            'https://ethereum-rpc.publicnode.com',
            'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
            'https://rpc.builder0x69.io',
            'https://rpc.mevblocker.io',
            'https://virginia.rpc.blxrbdn.com',
            'https://uk.rpc.blxrbdn.com',
            'https://singapore.rpc.blxrbdn.com',
            'https://eth.meowrpc.com',
            'https://core.gashawk.io/rpc',
            'https://mainnet.eth.cloud.ava.do',
            'https://ethereumnodelight.app.runonflux.io',
            'https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7',
            'https://ethereum.blockpi.network/v1/rpc/public'
        ],
        'pool': '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
        'pool_data_provider': '0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3',
        'active': True
    },
    'polygon': {
        'name': 'Polygon',
        'chain_id': 137,
        'rpc': 'https://polygon-bor.publicnode.com',
        'rpc_fallback': [
            'https://polygon-mainnet.public.blastapi.io',
            'https://polygon.drpc.org',
            'https://polygon.llamarpc.com',
            'https://polygon-rpc.com',
            'https://endpoints.omniatech.io/v1/matic/mainnet/public',
            'https://polygon.rpc.hypersync.xyz',
            'https://polygon-api.flare.network',
            'https://1rpc.io/matic',
            'https://rpc.ankr.com/polygon',
            'https://polygon-rpc.publicnode.com',
            'https://polygon-mainnet.infura.io/v3/4458cf4d1689497b9a38b1d6bbf05e78',
            'https://matic-mainnet.chainstacklabs.com',
            'https://rpc-mainnet.matic.network',
            'https://rpc-mainnet.matic.quiknode.pro',
            'https://rpc-mainnet.maticvigil.com',
            'https://polygon.meowrpc.com',
            'https://polygon-mainnet.g.alchemy.com/v2/demo',
            'https://polygon.blockpi.network/v1/rpc/public',
            'https://polygon-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://polygon.gateway.tenderly.co'
        ],
        'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        'pool_data_provider': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
        'active': True
    },
    'arbitrum': {
        'name': 'Arbitrum One',
        'chain_id': 42161,
        'rpc': 'https://arbitrum-one.publicnode.com',
        'rpc_fallback': [
            'https://arbitrum-one.public.blastapi.io',
            'https://arbitrum.drpc.org',
            'https://arbitrum.llamarpc.com',
            'https://arb1.arbitrum.io/rpc',
            'https://endpoints.omniatech.io/v1/arbitrum/one/public',
            'https://arbitrum.rpc.hypersync.xyz',
            'https://1rpc.io/arb',
            'https://arbitrum.api.onfinality.io/public',
            'https://rpc.ankr.com/arbitrum',
            'https://arbitrum-mainnet.infura.io/v3/4458cf4d1689497b9a38b1d6bbf05e78',
            'https://arb-mainnet.g.alchemy.com/v2/demo',
            'https://arbitrum.meowrpc.com',
            'https://arbitrum.blockpi.network/v1/rpc/public',
            'https://arbitrum-one.gateway.tenderly.co',
            'https://arbitrum-one.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://rpc.arb1.arbitrum.gateway.fm'
        ],
        'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        'pool_data_provider': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
        'active': True
    },
    'optimism': {
        'name': 'Optimism',
        'chain_id': 10,
        'rpc': 'https://optimism.publicnode.com',
        'rpc_fallback': [
            'https://optimism-mainnet.public.blastapi.io',
            'https://optimism.drpc.org',
            'https://optimism.llamarpc.com',
            'https://mainnet.optimism.io',
            'https://endpoints.omniatech.io/v1/op/mainnet/public',
            'https://optimism.rpc.hypersync.xyz',
            'https://1rpc.io/op',
            'https://optimism.api.onfinality.io/public',
            'https://rpc.ankr.com/optimism',
            'https://optimism-mainnet.infura.io/v3/4458cf4d1689497b9a38b1d6bbf05e78',
            'https://opt-mainnet.g.alchemy.com/v2/demo',
            'https://optimism.meowrpc.com',
            'https://optimism.blockpi.network/v1/rpc/public',
            'https://optimism.gateway.tenderly.co',
            'https://optimism-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://rpc.optimism.gateway.fm'
        ],
        'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        'pool_data_provider': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
        'active': True
    },
    'avalanche': {
        'name': 'Avalanche C-Chain',
        'chain_id': 43114,
        'rpc': 'https://avalanche-evm.publicnode.com',
        'rpc_fallback': [
            'https://ava-mainnet.public.blastapi.io/ext/bc/C/rpc',
            'https://avalanche.drpc.org',
            'https://api.avax.network/ext/bc/C/rpc',
            'https://endpoints.omniatech.io/v1/avax/mainnet/public',
            'https://avalanche.rpc.hypersync.xyz',
            'https://avalanche-api.flare.network/ext/bc/C/rpc',
            'https://avax.meowrpc.com',
            'https://1rpc.io/avax/c',
            'https://rpc.ankr.com/avalanche',
            'https://avalanche-mainnet.infura.io/v3/4458cf4d1689497b9a38b1d6bbf05e78',
            'https://avax-mainnet.gateway.pokt.network/v1/lb/605238bf6b986eea7cf36d5e/ext/bc/C/rpc',
            'https://avalanche-c-chain.publicnode.com',
            'https://avalanche.blockpi.network/v1/rpc/public',
            'https://ava-mainnet.nodereal.io/ext/bc/C/rpc',
            'https://rpc.avax.network/ext/bc/C/rpc',
            'https://avalanche.gateway.tenderly.co'
        ],
        'pool': '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
        'pool_data_provider': '0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654',
        'active': True
    },
    'metis': {
        'name': 'Metis Andromeda',
        'chain_id': 1088,
        'rpc': 'https://metis-rpc.publicnode.com',
        'rpc_fallback': [
            'https://metis-mainnet.public.blastapi.io',
            'https://metis.drpc.org',
            'https://metis-public.nodies.app',
            'https://metis.api.onfinality.io/public',
            'https://metis-pokt.nodies.app',
            'https://andromeda-rpc.polkachu.com',
            'https://metis-andromeda.gateway.tenderly.co',
            'https://andromeda.metis.io/?owner=1088',
            'https://metis-mainnet.g.alchemy.com/v2/demo',
            'https://metis.meowrpc.com',
            'https://metis-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3'
        ],
        'pool': '0x90df02551bB792286e8D4f13E0e357b4Bf1D6a57',
        'pool_data_provider': '0x99411FC17Ad1B56f49719E3850B2CDcc0f9bBFd8',
        'active': True
    },
    'base': {
        'name': 'Base',
        'chain_id': 8453,
        'rpc': 'https://base.publicnode.com',
        'rpc_fallback': [
            'https://mainnet.base.org',
            'https://base-mainnet.public.blastapi.io',
            'https://base.drpc.org',
            'https://base.llamarpc.com',
            'https://endpoints.omniatech.io/v1/base/mainnet/public',
            'https://base.rpc.hypersync.xyz',
            'https://1rpc.io/base',
            'https://base.api.onfinality.io/public',
            'https://rpc.ankr.com/base',
            'https://base-mainnet.g.alchemy.com/v2/demo',
            'https://base.meowrpc.com',
            'https://base.blockpi.network/v1/rpc/public',
            'https://base.gateway.tenderly.co',
            'https://base-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://developer-access-mainnet.base.org',
            'https://base-pokt.nodies.app'
        ],
        'pool': '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
        'pool_data_provider': '0x2d8A3C5677189723C4cB8873CfC9C8976FDF38Ac',
        'active': True
    },
    'gnosis': {
        'name': 'Gnosis Chain',
        'chain_id': 100,
        'rpc': 'https://gnosis.publicnode.com',
        'rpc_fallback': [
            'https://gnosis-mainnet.public.blastapi.io',
            'https://gnosis.drpc.org',
            'https://rpc.gnosis.gateway.fm',
            'https://rpc.gnosischain.com',
            'https://endpoints.omniatech.io/v1/gnosis/mainnet/public',
            'https://gnosis.rpc.hypersync.xyz',
            'https://1rpc.io/gnosis',
            'https://gnosis.api.onfinality.io/public',
            'https://rpc.ankr.com/gnosis',
            'https://gnosis.meowrpc.com',
            'https://gnosis.blockpi.network/v1/rpc/public',
            'https://gnosis-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://xdai-archive.blockscout.com',
            'https://gnosis-pokt.nodies.app'
        ],
        'pool': '0xb50201558B00496A145fE76f7424749556E326D8',
        'pool_data_provider': '0x501B4c19dd9C2e06E94dA7b6D5Ed4ddA013EC741',
        'active': True
    },
    'bnb': {
        'name': 'BNB Smart Chain',
        'chain_id': 56,
        'rpc': 'https://bsc.publicnode.com',
        'rpc_fallback': [
            'https://bsc-dataseed.binance.org',
            'https://bsc-mainnet.public.blastapi.io',
            'https://bsc.drpc.org',
            'https://bsc.llamarpc.com',
            'https://endpoints.omniatech.io/v1/bsc/mainnet/public',
            'https://bsc.rpc.hypersync.xyz',
            'https://bsc.meowrpc.com',
            'https://1rpc.io/bnb',
            'https://rpc.ankr.com/bsc',
            'https://bsc-dataseed1.defibit.io',
            'https://bsc-dataseed1.ninicoin.io',
            'https://bsc-dataseed2.defibit.io',
            'https://bsc-dataseed3.defibit.io',
            'https://bsc-dataseed4.defibit.io',
            'https://bsc-dataseed2.ninicoin.io',
            'https://bsc-dataseed3.ninicoin.io',
            'https://bsc-dataseed4.ninicoin.io',
            'https://bsc-dataseed1.binance.org',
            'https://bsc-dataseed2.binance.org',
            'https://bsc-dataseed3.binance.org',
            'https://bsc-dataseed4.binance.org',
            'https://bsc.blockpi.network/v1/rpc/public',
            'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://bsc-pokt.nodies.app'
        ],
        'pool': '0x6807dc923806fE8Fd134338EABCA509979a7e0cB',
        'pool_data_provider': '0x41393e5e337606dc3821075Af65AeE84D7688CBD',
        'active': True
    },
    'scroll': {
        'name': 'Scroll',
        'chain_id': 534352,
        'rpc': 'https://scroll-rpc.publicnode.com',
        'rpc_fallback': [
            'https://scroll-mainnet.public.blastapi.io',
            'https://scroll.drpc.org',
            'https://rpc.scroll.io',
            'https://scroll-public.nodies.app',
            'https://scroll.rpc.hypersync.xyz',
            'https://1rpc.io/scroll',
            'https://scroll.api.onfinality.io/public',
            'https://rpc.ankr.com/scroll',
            'https://scroll.meowrpc.com',
            'https://scroll.blockpi.network/v1/rpc/public',
            'https://scroll-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://scroll.gateway.tenderly.co',
            'https://scroll-alpha-mainnet.chainstacklabs.com'
        ],
        'pool': '0x11fCfe756c05AD438e312a7fd934381537D3cFfe',
        'pool_data_provider': '0xa99F4E69acF23C6838DE90dD1B5c02EA928A53ee',
        'active': True
    },
    'celo': {
        'name': 'Celo',
        'chain_id': 42220,
        'rpc': 'https://celo-rpc.publicnode.com',
        'rpc_fallback': [
            'https://forno.celo.org',
            'https://celo.drpc.org',
            'https://celo.api.onfinality.io/public',
            'https://celo.rpc.hypersync.xyz',
            'https://1rpc.io/celo',
            'https://celo.rpc.thirdweb.com',
            'https://rpc.ankr.com/celo',
            'https://celo-mainnet.infura.io/v3/4458cf4d1689497b9a38b1d6bbf05e78',
            'https://celo.meowrpc.com',
            'https://celo.blockpi.network/v1/rpc/public',
            'https://celo-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://celo-pokt.nodies.app'
        ],
        'pool': '0x3E59A31363E2ad014dcbc521c4a0d5757d9f3402',
        'pool_data_provider': '0x2e0f8D3B1631296cC7c56538D6Eb6032601E15ED',
        'active': True
    },
    'mantle': {
        'name': 'Mantle',
        'chain_id': 5000,
        'rpc': 'https://mantle.publicnode.com',
        'rpc_fallback': [
            'https://mantle-mainnet.public.blastapi.io',
            'https://mantle.drpc.org',
            'https://rpc.mantle.xyz',
            'https://mantle-public.nodies.app',
            'https://mantle.rpc.hypersync.xyz',
            'https://1rpc.io/mantle',
            'https://mantle.api.onfinality.io/public',
            'https://rpc.ankr.com/mantle',
            'https://mantle.meowrpc.com',
            'https://mantle.blockpi.network/v1/rpc/public',
            'https://mantle-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://mantle-pokt.nodies.app'
        ],
        'pool': '0x2e770EF8AbdEcA83D9310E2d3B3c2FdfFF5fd85A',  # PLACEHOLDER - Aave V3 not deployed yet
        'pool_data_provider': '0x9138E2cAdFEB23AFFdc0419F2912CaB8F135dba9',  # PLACEHOLDER
        'active': False  # Disabled - Aave V3 not deployed on Mantle yet (Jan 2025, still in governance)
    },
    'soneium': {
        'name': 'Soneium',
        'chain_id': 1946,
        'rpc': 'https://soneium-rpc.publicnode.com',
        'rpc_fallback': [
            'https://soneium-mainnet.public.blastapi.io',
            'https://soneium.drpc.org',
            'https://rpc.soneium.org',
            'https://soneium.rpc.hypersync.xyz',
            'https://soneium.gateway.tenderly.co',
            'https://1868.rpc.thirdweb.com',
            'https://soneium.meowrpc.com',
            'https://soneium-pokt.nodies.app'
        ],
        'pool': '0x8b5B7a6055E54a36fF574bbE40cf2eA68d5554b3',
        'pool_data_provider': '0x777fBA024bA9dc51A9E9C5c4842B766d68E89110',
        'active': False  # Test network - not production
    },
    'sonic': {
        'name': 'Sonic',
        'chain_id': 146,
        'rpc': 'https://sonic-rpc.publicnode.com',
        'rpc_fallback': [
            'https://sonic-mainnet.public.blastapi.io',
            'https://sonic.drpc.org',
            'https://rpc.soniclabs.com',
            'https://sonic.rpc.hypersync.xyz',
            'https://sonic.api.onfinality.io/public',
            'https://sonic.gateway.tenderly.co',
            'https://sonic.meowrpc.com',
            'https://sonic-pokt.nodies.app'
        ],
        'pool': '0x8b5B7a6055E54a36fF574bbE40cf2eA68d5554b3',
        'pool_data_provider': '0x777fBA024bA9dc51A9E9C5c4842B766d68E89110',
        'active': False  # Test network - not production
    },
    'zksync': {
        'name': 'zkSync Era',
        'chain_id': 324,
        'rpc': 'https://mainnet.era.zksync.io',
        'rpc_fallback': [
            'https://zksync-mainnet.public.blastapi.io',
            'https://zksync.drpc.org',
            'https://endpoints.omniatech.io/v1/zksync-era/mainnet/public',
            'https://zksync.rpc.hypersync.xyz',
            'https://1rpc.io/zksync2-era',
            'https://zksync.api.onfinality.io/public',
            'https://zksync.gateway.tenderly.co',
            'https://zksync.meowrpc.com',
            'https://zksync-era.blockpi.network/v1/rpc/public',
            'https://zksync-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://zksync-pokt.nodies.app'
        ],
        'pool': '0x4d9429246EA989C9CeE203B43F6d1C7D83e3B8F8',
        'pool_data_provider': '0x7deA671A409f4a95E9b1C84b3C7292F1B8562B7A',
        'active': True
    },
    'linea': {
        'name': 'Linea',
        'chain_id': 59144,
        'rpc': 'https://linea-rpc.publicnode.com',
        'rpc_fallback': [
            'https://linea-mainnet.public.blastapi.io',
            'https://linea.drpc.org',
            'https://rpc.linea.build',
            'https://linea.gateway.tenderly.co',
            'https://linea.rpc.hypersync.xyz',
            'https://1rpc.io/linea',
            'https://linea-mainnet-public.unifra.io',
            'https://rpc.ankr.com/linea',
            'https://linea.meowrpc.com',
            'https://linea.blockpi.network/v1/rpc/public',
            'https://linea-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3',
            'https://linea-pokt.nodies.app'
        ],
        'pool': '0xc47b8C00b0f69a36fa203Ffeac0334874574a8Ac',
        'pool_data_provider': '0x47cd4b507B81cB831669c71c7077f4daF6762FF4',
        'active': True
    }
}


def validate_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format.
    
    Args:
        address: Address string to validate
        
    Returns:
        True if valid Ethereum address format
    """
    if not isinstance(address, str):
        return False
    
    # Check if it starts with 0x and has correct length
    if not address.startswith('0x'):
        return False
    
    if len(address) != 42:  # 0x + 40 hex characters
        return False
    
    # Check if all characters after 0x are valid hex
    hex_part = address[2:]
    return all(c in '0123456789abcdefABCDEF' for c in hex_part)


def validate_rpc_url(url: str) -> bool:
    """
    Validate RPC URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL format
    """
    if not isinstance(url, str):
        return False
    
    # Enhanced URL validation to handle complex paths and subdomains
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)*'  # subdomains
        r'[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?'  # domain
        r'\.?'  # optional trailing dot
        r'|localhost'  # localhost
        r'|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP address
        r')'
        r'(?::\d+)?'  # optional port
        r'(?:/[^\s]*)?$',  # optional path (more permissive)
        re.IGNORECASE
    )
    
    return url_pattern.match(url) is not None


def validate_network_config(network_key: str, config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a single network configuration.
    
    Args:
        network_key: Network identifier key
        config: Network configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ['name', 'chain_id', 'rpc', 'pool', 'pool_data_provider', 'active']
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate field types and formats
    if 'name' in config and not isinstance(config['name'], str):
        errors.append("Field 'name' must be a string")
    
    if 'chain_id' in config and not isinstance(config['chain_id'], int):
        errors.append("Field 'chain_id' must be an integer")
    
    if 'active' in config and not isinstance(config['active'], bool):
        errors.append("Field 'active' must be a boolean")
    
    if 'rpc' in config and not validate_rpc_url(config['rpc']):
        errors.append(f"Invalid RPC URL format: {config['rpc']}")
    
    if 'pool' in config and not validate_ethereum_address(config['pool']):
        errors.append(f"Invalid pool address format: {config['pool']}")
    
    if 'pool_data_provider' in config and not validate_ethereum_address(config['pool_data_provider']):
        errors.append(f"Invalid pool_data_provider address format: {config['pool_data_provider']}")
    
    # Validate fallback URLs if present
    if 'rpc_fallback' in config:
        fallbacks = config['rpc_fallback']
        if not isinstance(fallbacks, list):
            errors.append("Field 'rpc_fallback' must be a list")
        else:
            for fb_url in fallbacks:
                if not validate_rpc_url(fb_url):
                    errors.append(f"Invalid fallback RPC URL format: {fb_url}")
    
    return len(errors) == 0, errors


def validate_all_networks() -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate all network configurations.
    
    Returns:
        Tuple of (all_valid, dict_of_errors_by_network)
    """
    all_errors = {}
    all_valid = True
    
    for network_key, config in AAVE_V3_NETWORKS.items():
        is_valid, errors = validate_network_config(network_key, config)
        if not is_valid:
            all_errors[network_key] = errors
            all_valid = False
    
    return all_valid, all_errors


def get_active_networks() -> Dict[str, Dict]:
    """
    Get only active network configurations.
    
    Returns:
        Dictionary of active networks
    """
    return {
        key: config for key, config in AAVE_V3_NETWORKS.items()
        if config.get('active', False)
    }


def get_network_by_chain_id(chain_id: int) -> Optional[Tuple[str, Dict]]:
    """
    Find network configuration by chain ID.
    
    Args:
        chain_id: Blockchain chain ID
        
    Returns:
        Tuple of (network_key, config) or None if not found
    """
    for key, config in AAVE_V3_NETWORKS.items():
        if config.get('chain_id') == chain_id:
            return key, config
    return None


def get_fallback_urls(config: Dict) -> Optional[List[str]]:
    """
    Extract fallback RPC URLs from network configuration.
    
    Args:
        config: Network configuration dictionary
        
    Returns:
        List of fallback URLs or None if not configured
    """
    fallback = config.get('rpc_fallback')
    if isinstance(fallback, list):
        return fallback
    elif isinstance(fallback, str):
        return [fallback]
    return None


def test_rpc_connectivity(network_key: str, config: Dict) -> Tuple[bool, str]:
    """
    Test RPC endpoint connectivity for a network with retry logic and fallbacks.
    
    Args:
        network_key: Network identifier
        config: Network configuration
        
    Returns:
        Tuple of (is_accessible, error_message)
    """
    try:
        # Get fallback URLs from configuration
        fallback_urls = get_fallback_urls(config)
        
        # Test basic RPC connectivity with eth_chainId call using retry logic
        from utils import rpc_call_with_retry
        
        result = rpc_call_with_retry(
            config['rpc'], 
            'eth_chainId', 
            [],
            max_retries=2,  # Reduced retries for connectivity test
            fallback_urls=fallback_urls
        )
        
        if 'result' in result:
            # Verify chain ID matches configuration
            returned_chain_id = int(result['result'], 16)
            expected_chain_id = config['chain_id']
            
            if returned_chain_id != expected_chain_id:
                return False, f"Chain ID mismatch: expected {expected_chain_id}, got {returned_chain_id}"
            
            return True, "RPC endpoint accessible"
        else:
            return False, "No result in RPC response"
            
    except Exception as e:
        return False, f"RPC connection failed: {str(e)}"


def test_all_rpc_endpoints() -> Dict[str, Tuple[bool, str]]:
    """
    Test RPC connectivity for all active networks.
    
    Returns:
        Dictionary mapping network_key to (is_accessible, message)
    """
    results = {}
    active_networks = get_active_networks()
    
    for network_key, config in active_networks.items():
        results[network_key] = test_rpc_connectivity(network_key, config)
    
    return results


def get_network_summary() -> Dict[str, int]:
    """
    Get summary statistics of network configuration.
    
    Returns:
        Dictionary with network statistics
    """
    total_networks = len(AAVE_V3_NETWORKS)
    active_networks = len(get_active_networks())
    
    return {
        'total_networks': total_networks,
        'active_networks': active_networks,
        'inactive_networks': total_networks - active_networks
    }


# Auto-update functionality from aave-address-book
AAVE_ADDRESS_BOOK_BASE_URL = "https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src"


def fetch_address_book_networks() -> Optional[Dict[str, Dict]]:
    """
    Fetch network configurations from aave-address-book repository.
    
    Returns:
        Dictionary of network configurations or None if fetch fails
    """
    try:
        # List of known Aave V3 network files in the address book
        network_files = [
            'AaveV3Ethereum.sol',
            'AaveV3Polygon.sol', 
            'AaveV3Arbitrum.sol',
            'AaveV3Optimism.sol',
            'AaveV3Avalanche.sol',
            'AaveV3Metis.sol',
            'AaveV3Base.sol',
            'AaveV3Gnosis.sol',
            'AaveV3BNB.sol',
            'AaveV3Scroll.sol',
            'AaveV3Celo.sol',
            'AaveV3Mantle.sol',
            'AaveV3ZkSync.sol',
            'AaveV3Linea.sol'
        ]
        
        discovered_networks = {}
        
        for network_file in network_files:
            try:
                network_name = network_file.replace('AaveV3', '').replace('.sol', '').lower()
                file_url = f"{AAVE_ADDRESS_BOOK_BASE_URL}/{network_file}"
                
                with urllib.request.urlopen(file_url, timeout=30) as response:
                    content = response.read().decode('utf-8')
                
                # Parse network configuration from the file
                network_config = parse_network_solidity_file(content, network_name)
                if network_config:
                    discovered_networks[network_name] = network_config
                    print(f"Successfully discovered network: {network_name}")
                    
            except Exception as e:
                print(f"Failed to fetch {network_file}: {e}")
                continue
        
        return discovered_networks if discovered_networks else None
        
    except Exception as e:
        print(f"Failed to fetch from aave-address-book: {e}")
        return None


def parse_address_book_content(content: str) -> Dict[str, Dict]:
    """
    Parse network information from aave-address-book Solidity content.
    This function is deprecated in favor of parse_network_solidity_file.
    
    Args:
        content: Solidity file content from address book
        
    Returns:
        Dictionary of parsed network configurations
    """
    # This function is kept for backward compatibility but is no longer used
    # The actual parsing is now done in parse_network_solidity_file
    return {}


def fetch_network_from_github_api(network_name: str) -> Optional[Dict]:
    """
    Fetch specific network configuration from GitHub API.
    
    Args:
        network_name: Name of the network to fetch
        
    Returns:
        Network configuration dictionary or None if not found
    """
    try:
        # Construct API URL for specific network file
        api_url = f"https://api.github.com/repos/bgd-labs/aave-address-book/contents/src/{network_name.title()}V3.sol"
        
        with urllib.request.urlopen(api_url, timeout=30) as response:
            api_response = json.loads(response.read().decode('utf-8'))
        
        if 'content' in api_response:
            # Decode base64 content
            import base64
            content = base64.b64decode(api_response['content']).decode('utf-8')
            
            # Parse the Solidity file for network configuration
            return parse_network_solidity_file(content, network_name)
        
        return None
        
    except Exception as e:
        print(f"Failed to fetch {network_name} from GitHub API: {e}")
        return None


def parse_network_solidity_file(content: str, network_name: str) -> Optional[Dict]:
    """
    Parse network configuration from individual Solidity file.
    
    Args:
        content: Solidity file content
        network_name: Network name for identification
        
    Returns:
        Network configuration dictionary or None
    """
    try:
        # Enhanced regex patterns to find Pool and Pool Data Provider addresses
        pool_patterns = [
            r'address\s+(?:public\s+)?(?:constant\s+)?POOL\s*=\s*(0x[a-fA-F0-9]{40})',
            r'POOL\s*=\s*(0x[a-fA-F0-9]{40})',
            r'pool:\s*(0x[a-fA-F0-9]{40})',
        ]
        
        provider_patterns = [
            r'address\s+(?:public\s+)?(?:constant\s+)?POOL_DATA_PROVIDER\s*=\s*(0x[a-fA-F0-9]{40})',
            r'POOL_DATA_PROVIDER\s*=\s*(0x[a-fA-F0-9]{40})',
            r'poolDataProvider:\s*(0x[a-fA-F0-9]{40})',
            r'AAVE_PROTOCOL_DATA_PROVIDER\s*=\s*(0x[a-fA-F0-9]{40})',
        ]
        
        pool_address = None
        provider_address = None
        
        # Try to find Pool address
        for pattern in pool_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                pool_address = match.group(1)
                break
        
        # Try to find Pool Data Provider address
        for pattern in provider_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                provider_address = match.group(1)
                break
        
        if pool_address and provider_address:
            # Enhanced network mapping with comprehensive fallback RPC endpoints
            network_mapping = {
                'ethereum': {
                    'chain_id': 1, 
                    'rpc': 'https://ethereum.publicnode.com',
                    'rpc_fallback': [
                        'https://eth-mainnet.public.blastapi.io',
                        'https://eth.drpc.org',
                        'https://eth.llamarpc.com',
                        'https://cloudflare-eth.com/v1/mainnet',
                        'https://rpc.flashbots.net',
                        'https://1rpc.io/eth',
                        'https://eth.rpc.hypersync.xyz',
                        'https://endpoints.omniatech.io/v1/eth/mainnet/public'
                    ]
                },
                'polygon': {
                    'chain_id': 137, 
                    'rpc': 'https://polygon-bor.publicnode.com',
                    'rpc_fallback': [
                        'https://polygon-mainnet.public.blastapi.io',
                        'https://polygon.drpc.org',
                        'https://polygon.llamarpc.com',
                        'https://polygon-rpc.com',
                        'https://endpoints.omniatech.io/v1/matic/mainnet/public',
                        'https://polygon.rpc.hypersync.xyz',
                        'https://polygon-api.flare.network',
                        'https://1rpc.io/matic'
                    ]
                },
                'arbitrum': {
                    'chain_id': 42161, 
                    'rpc': 'https://arbitrum-one.publicnode.com',
                    'rpc_fallback': [
                        'https://arbitrum-one.public.blastapi.io',
                        'https://arbitrum.drpc.org',
                        'https://arbitrum.llamarpc.com',
                        'https://arb1.arbitrum.io/rpc',
                        'https://endpoints.omniatech.io/v1/arbitrum/one/public',
                        'https://arbitrum.rpc.hypersync.xyz',
                        'https://1rpc.io/arb',
                        'https://arbitrum.api.onfinality.io/public'
                    ]
                },
                'optimism': {
                    'chain_id': 10, 
                    'rpc': 'https://optimism.publicnode.com',
                    'rpc_fallback': [
                        'https://optimism-mainnet.public.blastapi.io',
                        'https://optimism.drpc.org',
                        'https://optimism.llamarpc.com',
                        'https://mainnet.optimism.io',
                        'https://endpoints.omniatech.io/v1/op/mainnet/public',
                        'https://optimism.rpc.hypersync.xyz',
                        'https://1rpc.io/op',
                        'https://optimism.api.onfinality.io/public'
                    ]
                },
                'avalanche': {
                    'chain_id': 43114, 
                    'rpc': 'https://avalanche-evm.publicnode.com',
                    'rpc_fallback': [
                        'https://ava-mainnet.public.blastapi.io/ext/bc/C/rpc',
                        'https://avalanche.drpc.org',
                        'https://api.avax.network/ext/bc/C/rpc',
                        'https://endpoints.omniatech.io/v1/avax/mainnet/public',
                        'https://avalanche.rpc.hypersync.xyz',
                        'https://avalanche-api.flare.network/ext/bc/C/rpc',
                        'https://avax.meowrpc.com',
                        'https://1rpc.io/avax/c'
                    ]
                },
                'metis': {
                    'chain_id': 1088, 
                    'rpc': 'https://metis-rpc.publicnode.com',
                    'rpc_fallback': [
                        'https://metis-mainnet.public.blastapi.io',
                        'https://metis.drpc.org',
                        'https://metis-public.nodies.app',
                        'https://metis.api.onfinality.io/public',
                        'https://metis-pokt.nodies.app',
                        'https://andromeda-rpc.polkachu.com',
                        'https://metis-andromeda.gateway.tenderly.co'
                    ]
                },
                'base': {
                    'chain_id': 8453, 
                    'rpc': 'https://base.publicnode.com',
                    'rpc_fallback': [
                        'https://mainnet.base.org',
                        'https://base-mainnet.public.blastapi.io',
                        'https://base.drpc.org',
                        'https://base.llamarpc.com',
                        'https://endpoints.omniatech.io/v1/base/mainnet/public',
                        'https://base.rpc.hypersync.xyz',
                        'https://1rpc.io/base',
                        'https://base.api.onfinality.io/public'
                    ]
                },
                'gnosis': {
                    'chain_id': 100, 
                    'rpc': 'https://gnosis.publicnode.com',
                    'rpc_fallback': [
                        'https://gnosis-mainnet.public.blastapi.io',
                        'https://gnosis.drpc.org',
                        'https://rpc.gnosis.gateway.fm',
                        'https://rpc.gnosischain.com',
                        'https://endpoints.omniatech.io/v1/gnosis/mainnet/public',
                        'https://gnosis.rpc.hypersync.xyz',
                        'https://1rpc.io/gnosis',
                        'https://gnosis.api.onfinality.io/public'
                    ]
                },
                'bnb': {
                    'chain_id': 56, 
                    'rpc': 'https://bsc.publicnode.com',
                    'rpc_fallback': [
                        'https://bsc-dataseed.binance.org',
                        'https://bsc-mainnet.public.blastapi.io',
                        'https://bsc.drpc.org',
                        'https://bsc.llamarpc.com',
                        'https://endpoints.omniatech.io/v1/bsc/mainnet/public',
                        'https://bsc.rpc.hypersync.xyz',
                        'https://bsc.meowrpc.com',
                        'https://1rpc.io/bnb'
                    ]
                },
                'scroll': {
                    'chain_id': 534352, 
                    'rpc': 'https://scroll-rpc.publicnode.com',
                    'rpc_fallback': [
                        'https://scroll-mainnet.public.blastapi.io',
                        'https://scroll.drpc.org',
                        'https://rpc.scroll.io',
                        'https://scroll-public.nodies.app',
                        'https://scroll.rpc.hypersync.xyz',
                        'https://1rpc.io/scroll',
                        'https://scroll.api.onfinality.io/public'
                    ]
                },
                'celo': {
                    'chain_id': 42220, 
                    'rpc': 'https://celo-rpc.publicnode.com',
                    'rpc_fallback': [
                        'https://forno.celo.org',
                        'https://celo.drpc.org',
                        'https://celo.api.onfinality.io/public',
                        'https://celo.rpc.hypersync.xyz',
                        'https://1rpc.io/celo',
                        'https://celo.rpc.thirdweb.com'
                    ]
                },
                'mantle': {
                    'chain_id': 5000, 
                    'rpc': 'https://mantle.publicnode.com',
                    'rpc_fallback': [
                        'https://mantle-mainnet.public.blastapi.io',
                        'https://mantle.drpc.org',
                        'https://rpc.mantle.xyz',
                        'https://mantle-public.nodies.app',
                        'https://mantle.rpc.hypersync.xyz',
                        'https://1rpc.io/mantle',
                        'https://mantle.api.onfinality.io/public'
                    ]
                },
                'zksync': {
                    'chain_id': 324, 
                    'rpc': 'https://mainnet.era.zksync.io',
                    'rpc_fallback': [
                        'https://zksync-mainnet.public.blastapi.io',
                        'https://zksync.drpc.org',
                        'https://endpoints.omniatech.io/v1/zksync-era/mainnet/public',
                        'https://zksync.rpc.hypersync.xyz',
                        'https://1rpc.io/zksync2-era',
                        'https://zksync.api.onfinality.io/public',
                        'https://zksync.gateway.tenderly.co'
                    ]
                },
                'linea': {
                    'chain_id': 59144, 
                    'rpc': 'https://linea-rpc.publicnode.com',
                    'rpc_fallback': [
                        'https://linea-mainnet.public.blastapi.io',
                        'https://linea.drpc.org',
                        'https://rpc.linea.build',
                        'https://linea.gateway.tenderly.co',
                        'https://linea.rpc.hypersync.xyz',
                        'https://1rpc.io/linea',
                        'https://linea-mainnet-public.unifra.io'
                    ]
                }
            }
            
            network_info = network_mapping.get(network_name.lower())
            if network_info:
                config = {
                    'name': f"{network_name.title()} (Auto-discovered)",
                    'chain_id': network_info['chain_id'],
                    'rpc': network_info['rpc'],
                    'pool': pool_address,
                    'pool_data_provider': provider_address,
                    'active': True,
                    'source': 'aave-address-book',
                    'last_updated': int(__import__('time').time())
                }
                
                # Add fallback RPC if available
                if 'rpc_fallback' in network_info:
                    config['rpc_fallback'] = network_info['rpc_fallback']
                
                return config
        
        return None
        
    except Exception as e:
        print(f"Failed to parse {network_name} Solidity file: {e}")
        return None


def update_networks_from_address_book() -> Tuple[Dict[str, Dict], List[str]]:
    """
    Update network configurations with data from aave-address-book.
    
    Returns:
        Tuple of (updated_networks_dict, list_of_errors)
    """
    errors = []
    updated_networks = AAVE_V3_NETWORKS.copy()
    
    try:
        print("Fetching network configurations from aave-address-book...")
        
        # Try to fetch from address book
        discovered_networks = fetch_address_book_networks()
        
        if discovered_networks:
            print(f"Successfully discovered {len(discovered_networks)} networks from address book")
            
            # Merge discovered networks with existing ones
            for network_key, config in discovered_networks.items():
                # Validate discovered network configuration
                is_valid, validation_errors = validate_network_config(network_key, config)
                
                if is_valid:
                    # Check if this is a new network or an update
                    if network_key in updated_networks:
                        # Compare with existing configuration
                        existing = updated_networks[network_key]
                        if (existing.get('pool') != config.get('pool') or 
                            existing.get('pool_data_provider') != config.get('pool_data_provider')):
                            print(f"Updated network configuration: {network_key}")
                            print(f"  Pool: {existing.get('pool')} -> {config.get('pool')}")
                            print(f"  Provider: {existing.get('pool_data_provider')} -> {config.get('pool_data_provider')}")
                    else:
                        print(f"Added new network: {network_key}")
                    
                    # Update the network configuration
                    updated_networks[network_key] = config
                else:
                    errors.append(f"Invalid discovered network {network_key}: {validation_errors}")
                    
            # Check for networks that might have been removed from address book
            static_networks = set(AAVE_V3_NETWORKS.keys())
            discovered_network_keys = set(discovered_networks.keys())
            
            # Mark networks as potentially deprecated if they're not in the address book
            for network_key in static_networks:
                if network_key not in discovered_network_keys:
                    if updated_networks[network_key].get('source') != 'static':
                        updated_networks[network_key]['deprecated'] = True
                        print(f"Network {network_key} not found in address book - marked as deprecated")
                        
        else:
            errors.append("Failed to fetch networks from aave-address-book - using fallback configuration")
            print("Warning: Could not fetch from address book, using static configuration")
            
    except Exception as e:
        error_msg = f"Error updating from address book: {str(e)}"
        errors.append(error_msg)
        print(f"Error: {error_msg}")
    
    return updated_networks, errors


def get_networks_with_fallback() -> Dict[str, Dict]:
    """
    Get network configurations with fallback to address book.
    Implements robust fallback mechanism when address-book is unavailable.
    
    Returns:
        Dictionary of network configurations
    """
    try:
        print("Attempting to fetch networks with address book integration...")
        
        # Try to update from address book
        updated_networks, errors = update_networks_from_address_book()
        
        if errors:
            print("Warnings during network update:")
            for error in errors:
                print(f"  - {error}")
        
        # Validate that we have at least some working networks
        active_networks = {k: v for k, v in updated_networks.items() if v.get('active', False)}
        
        if len(active_networks) < 3:  # Ensure we have at least 3 active networks
            print("Warning: Too few active networks discovered, falling back to static configuration")
            return AAVE_V3_NETWORKS
        
        print(f"Successfully loaded {len(active_networks)} active networks")
        return updated_networks
        
    except Exception as e:
        print(f"Error during network discovery, falling back to static configuration: {e}")
        return AAVE_V3_NETWORKS


def periodic_network_discovery() -> Tuple[Dict[str, Dict], bool]:
    """
    Perform periodic network discovery to automatically include new Aave V3 deployments.
    This function should be called periodically to check for new networks.
    
    Returns:
        Tuple of (networks_dict, discovery_successful)
    """
    try:
        print("Starting periodic network discovery...")
        
        # Get current networks
        current_networks = AAVE_V3_NETWORKS.copy()
        
        # Attempt to discover new networks
        discovered_networks, errors = update_networks_from_address_book()
        
        # Check for new networks
        current_keys = set(current_networks.keys())
        discovered_keys = set(discovered_networks.keys())
        new_networks = discovered_keys - current_keys
        
        if new_networks:
            print(f"Discovered {len(new_networks)} new networks: {', '.join(new_networks)}")
            
            # Validate new networks before adding
            validated_new_networks = {}
            for network_key in new_networks:
                config = discovered_networks[network_key]
                is_valid, validation_errors = validate_network_config(network_key, config)
                
                if is_valid:
                    # Test RPC connectivity before adding
                    is_accessible, rpc_message = test_rpc_connectivity(network_key, config)
                    if is_accessible:
                        validated_new_networks[network_key] = config
                        print(f"  ✓ {network_key}: Validated and accessible")
                    else:
                        print(f"  ✗ {network_key}: RPC not accessible - {rpc_message}")
                else:
                    print(f"  ✗ {network_key}: Invalid configuration - {validation_errors}")
            
            # Merge validated new networks
            discovered_networks.update(validated_new_networks)
            
        discovery_successful = len(errors) == 0
        
        if not discovery_successful:
            print("Discovery completed with errors - using fallback configuration")
            return current_networks, False
        
        print(f"Periodic discovery completed successfully - {len(discovered_networks)} total networks")
        return discovered_networks, True
        
    except Exception as e:
        print(f"Periodic network discovery failed: {e}")
        return AAVE_V3_NETWORKS, False


def discover_new_networks() -> List[str]:
    """
    Discover potentially new Aave V3 networks from address book.
    Scans the aave-address-book repository for new network files.
    
    Returns:
        List of newly discovered network names
    """
    try:
        print("Scanning aave-address-book for new networks...")
        
        # Get list of files in the address book repository
        api_url = "https://api.github.com/repos/bgd-labs/aave-address-book/contents/src"
        
        with urllib.request.urlopen(api_url, timeout=30) as response:
            files_data = json.loads(response.read().decode('utf-8'))
        
        # Extract Aave V3 network files
        aave_v3_files = []
        for file_info in files_data:
            if (file_info['type'] == 'file' and 
                file_info['name'].startswith('AaveV3') and 
                file_info['name'].endswith('.sol')):
                aave_v3_files.append(file_info['name'])
        
        print(f"Found {len(aave_v3_files)} Aave V3 network files in address book")
        
        # Extract network names and check against existing networks
        existing_networks = set(AAVE_V3_NETWORKS.keys())
        new_networks = []
        
        for file_name in aave_v3_files:
            # Extract network name from file name (e.g., AaveV3Ethereum.sol -> ethereum)
            network_name = file_name.replace('AaveV3', '').replace('.sol', '').lower()
            
            if network_name not in existing_networks:
                # Try to fetch and validate configuration for this network
                try:
                    config = fetch_network_from_github_api(network_name)
                    if config:
                        # Validate the configuration
                        is_valid, validation_errors = validate_network_config(network_name, config)
                        if is_valid:
                            new_networks.append(network_name)
                            print(f"  ✓ Discovered new network: {network_name}")
                        else:
                            print(f"  ✗ Invalid configuration for {network_name}: {validation_errors}")
                    else:
                        print(f"  ✗ Could not parse configuration for {network_name}")
                except Exception as e:
                    print(f"  ✗ Error processing {network_name}: {e}")
        
        if new_networks:
            print(f"Successfully discovered {len(new_networks)} new networks: {', '.join(new_networks)}")
        else:
            print("No new networks discovered")
        
        return new_networks
        
    except Exception as e:
        print(f"Error discovering new networks: {e}")
        return []


def save_discovered_networks(networks: Dict[str, Dict], file_path: str = "discovered_networks.json") -> bool:
    """
    Save discovered network configurations to a JSON file for caching.
    
    Args:
        networks: Dictionary of network configurations
        file_path: Path to save the JSON file
        
    Returns:
        True if save was successful
    """
    try:
        # Add metadata
        save_data = {
            'last_updated': int(__import__('time').time()),
            'networks': networks,
            'source': 'aave-address-book',
            'total_networks': len(networks)
        }
        
        with open(file_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Saved {len(networks)} network configurations to {file_path}")
        return True
        
    except Exception as e:
        print(f"Failed to save discovered networks: {e}")
        return False


def load_cached_networks(file_path: str = "discovered_networks.json", max_age_hours: int = 24) -> Optional[Dict[str, Dict]]:
    """
    Load cached network configurations from JSON file.
    
    Args:
        file_path: Path to the cached JSON file
        max_age_hours: Maximum age of cache in hours
        
    Returns:
        Dictionary of network configurations or None if cache is invalid/expired
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            cache_data = json.load(f)
        
        # Check cache age
        current_time = int(__import__('time').time())
        cache_age = current_time - cache_data.get('last_updated', 0)
        max_age_seconds = max_age_hours * 3600
        
        if cache_age > max_age_seconds:
            print(f"Cache expired (age: {cache_age/3600:.1f} hours)")
            return None
        
        networks = cache_data.get('networks', {})
        print(f"Loaded {len(networks)} networks from cache (age: {cache_age/3600:.1f} hours)")
        return networks
        
    except Exception as e:
        print(f"Failed to load cached networks: {e}")
        return None