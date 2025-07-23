#!/usr/bin/env python3
"""
Network configuration validation script.
Validates all network configurations and optionally tests RPC connectivity.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from networks import (
    AAVE_V3_NETWORKS,
    validate_all_networks,
    get_active_networks,
    get_network_summary,
    test_all_rpc_endpoints
)


def main():
    """Main validation script."""
    print("Aave V3 Network Configuration Validation")
    print("=" * 50)
    
    # Show network summary
    summary = get_network_summary()
    print(f"\nNetwork Summary:")
    print(f"  Total networks: {summary['total_networks']}")
    print(f"  Active networks: {summary['active_networks']}")
    print(f"  Inactive networks: {summary['inactive_networks']}")
    
    # Validate all network configurations
    print(f"\nValidating network configurations...")
    is_valid, errors = validate_all_networks()
    
    if is_valid:
        print("✅ All network configurations are valid!")
    else:
        print("❌ Some network configurations have errors:")
        for network, network_errors in errors.items():
            print(f"  {network}:")
            for error in network_errors:
                print(f"    - {error}")
        return 1
    
    # List all active networks
    print(f"\nActive Networks:")
    active_networks = get_active_networks()
    for network_key, config in active_networks.items():
        print(f"  {network_key:12} | Chain ID: {config['chain_id']:6} | {config['name']}")
    
    # Test RPC connectivity if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--test-rpc':
        print(f"\nTesting RPC connectivity...")
        print("(This may take a while...)")
        
        rpc_results = test_all_rpc_endpoints()
        
        print(f"\nRPC Connectivity Results:")
        for network_key, (is_accessible, message) in rpc_results.items():
            status = "✅" if is_accessible else "❌"
            print(f"  {status} {network_key:12} | {message}")
    
    print(f"\nValidation complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())