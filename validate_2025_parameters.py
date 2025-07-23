#!/usr/bin/env python3
"""
2025 Risk Parameter Updates Validation Script
Validates new parameters introduced in 2025 including supply/borrow caps and updated risk parameters.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class Risk2025Validator:
    """Validator for 2025 risk parameter updates."""
    
    def __init__(self):
        # 2025 Risk Parameter Updates - Key changes from governance proposals
        self.risk_updates_2025 = {
            'supply_borrow_caps': {
                'description': 'Supply and borrow caps introduced for risk management',
                'networks': ['ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche'],
                'required_fields': ['supply_cap', 'borrow_cap'],
                'validation_rules': {
                    'supply_cap': {'min': 0, 'type': int},
                    'borrow_cap': {'min': 0, 'type': int},
                    'borrow_cap_vs_supply_cap': 'borrow_cap <= supply_cap'
                }
            },
            'wbtc_risk_adjustments': {
                'description': 'WBTC risk parameters updated across all networks',
                'affected_asset': 'WBTC',
                'updates': {
                    'liquidation_threshold': {'old': 0.70, 'new': 0.78, 'tolerance': 0.02},
                    'loan_to_value': {'old': 0.65, 'new': 0.73, 'tolerance': 0.02},
                    'liquidation_bonus': {'old': 0.10, 'new': 0.05, 'tolerance': 0.02},
                    'reserve_factor': {'old': 0.20, 'new': 0.50, 'tolerance': 0.05}
                }
            },
            'stablecoin_reserve_factors': {
                'description': 'Stablecoin reserve factors increased for revenue optimization',
                'affected_assets': ['USDC', 'USDC.e', 'USDT', 'DAI'],
                'networks_affected': ['polygon', 'arbitrum', 'optimism'],
                'expected_increases': {
                    'polygon': {'USDC': 0.60, 'USDC.e': 0.60},
                    'arbitrum': {'USDC.e': 0.50},
                    'optimism': {'USDC': 0.50, 'USDC.e': 0.50}
                }
            },
            'dai_ltv_adjustment': {
                'description': 'DAI LTV reduced from 75% to 63% on Ethereum',
                'network': 'ethereum',
                'asset': 'DAI',
                'parameter': 'loan_to_value',
                'old_value': 0.75,
                'new_value': 0.63,
                'tolerance': 0.02
            },
            'polygon_usdc_collateral_disable': {
                'description': 'Native USDC on Polygon disabled as collateral (LTV=0)',
                'network': 'polygon',
                'asset': 'USDC',
                'parameter': 'loan_to_value',
                'expected_value': 0.00,
                'tolerance': 0.01
            },
            'new_network_expansions': {
                'description': 'New networks added to Aave V3 in 2025',
                'expected_networks': [
                    'ethereum', 'polygon', 'arbitrum', 'optimism', 'avalanche',
                    'metis', 'base', 'gnosis', 'bnb', 'scroll', 'celo', 'mantle',
                    'soneium', 'sonic'
                ],
                'minimum_networks': 12  # Should have at least 12 networks by 2025
            }
        }
    
    def validate_2025_updates(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate all 2025 risk parameter updates."""
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_validations': 0,
                'passed_validations': 0,
                'failed_validations': 0,
                'warnings': 0
            },
            'validations': {}
        }
        
        print("🔍 Validating 2025 Risk Parameter Updates...")
        
        # Validate supply/borrow caps
        caps_result = self._validate_supply_borrow_caps(data)
        validation_results['validations']['supply_borrow_caps'] = caps_result
        self._update_summary(validation_results['summary'], caps_result)
        
        # Validate WBTC risk adjustments
        wbtc_result = self._validate_wbtc_adjustments(data)
        validation_results['validations']['wbtc_risk_adjustments'] = wbtc_result
        self._update_summary(validation_results['summary'], wbtc_result)
        
        # Validate stablecoin reserve factor increases
        stablecoin_result = self._validate_stablecoin_reserve_factors(data)
        validation_results['validations']['stablecoin_reserve_factors'] = stablecoin_result
        self._update_summary(validation_results['summary'], stablecoin_result)
        
        # Validate DAI LTV adjustment
        dai_result = self._validate_dai_ltv_adjustment(data)
        validation_results['validations']['dai_ltv_adjustment'] = dai_result
        self._update_summary(validation_results['summary'], dai_result)
        
        # Validate Polygon USDC collateral disable
        polygon_usdc_result = self._validate_polygon_usdc_disable(data)
        validation_results['validations']['polygon_usdc_collateral_disable'] = polygon_usdc_result
        self._update_summary(validation_results['summary'], polygon_usdc_result)
        
        # Validate network expansions
        network_result = self._validate_network_expansions(data)
        validation_results['validations']['network_expansions'] = network_result
        self._update_summary(validation_results['summary'], network_result)
        
        return validation_results
    
    def _update_summary(self, summary: Dict, result: Dict):
        """Update validation summary with individual result."""
        summary['total_validations'] += 1
        if result['status'] == 'passed':
            summary['passed_validations'] += 1
        elif result['status'] == 'failed':
            summary['failed_validations'] += 1
        
        summary['warnings'] += len(result.get('warnings', []))
    
    def _validate_supply_borrow_caps(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate supply and borrow caps implementation."""
        result = {
            'status': 'passed',
            'description': 'Supply and borrow caps validation',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        caps_config = self.risk_updates_2025['supply_borrow_caps']
        
        for network_key, assets in data.items():
            if network_key not in caps_config['networks']:
                continue
            
            network_details = {
                'assets_with_caps': 0,
                'assets_without_caps': 0,
                'cap_violations': []
            }
            
            for asset in assets:
                symbol = asset.get('symbol', 'UNKNOWN')
                has_supply_cap = 'supply_cap' in asset
                has_borrow_cap = 'borrow_cap' in asset
                
                if has_supply_cap and has_borrow_cap:
                    network_details['assets_with_caps'] += 1
                    
                    # Validate cap values
                    supply_cap = asset['supply_cap']
                    borrow_cap = asset['borrow_cap']
                    
                    if not isinstance(supply_cap, int) or supply_cap < 0:
                        network_details['cap_violations'].append(
                            f"{symbol}: Invalid supply_cap {supply_cap}"
                        )
                    
                    if not isinstance(borrow_cap, int) or borrow_cap < 0:
                        network_details['cap_violations'].append(
                            f"{symbol}: Invalid borrow_cap {borrow_cap}"
                        )
                    
                    if borrow_cap > supply_cap:
                        network_details['cap_violations'].append(
                            f"{symbol}: borrow_cap ({borrow_cap}) > supply_cap ({supply_cap})"
                        )
                else:
                    network_details['assets_without_caps'] += 1
                    result['warnings'].append(
                        f"{network_key} {symbol}: Missing supply/borrow caps"
                    )
            
            result['details'][network_key] = network_details
            
            # Check if violations found
            if network_details['cap_violations']:
                result['status'] = 'failed'
                result['errors'].extend([
                    f"{network_key}: {violation}" for violation in network_details['cap_violations']
                ])
        
        return result
    
    def _validate_wbtc_adjustments(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate WBTC risk parameter adjustments."""
        result = {
            'status': 'passed',
            'description': 'WBTC risk parameter adjustments validation',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        wbtc_config = self.risk_updates_2025['wbtc_risk_adjustments']
        updates = wbtc_config['updates']
        
        for network_key, assets in data.items():
            wbtc_found = False
            
            for asset in assets:
                if asset.get('symbol') == 'WBTC':
                    wbtc_found = True
                    network_details = {'parameter_checks': {}}
                    
                    for param, config in updates.items():
                        if param in asset:
                            actual_value = asset[param]
                            expected_value = config['new']
                            tolerance = config['tolerance']
                            
                            if abs(actual_value - expected_value) <= tolerance:
                                network_details['parameter_checks'][param] = {
                                    'status': 'passed',
                                    'actual': actual_value,
                                    'expected': expected_value
                                }
                            else:
                                network_details['parameter_checks'][param] = {
                                    'status': 'failed',
                                    'actual': actual_value,
                                    'expected': expected_value,
                                    'difference': abs(actual_value - expected_value)
                                }
                                result['errors'].append(
                                    f"{network_key} WBTC {param}: expected {expected_value}, got {actual_value}"
                                )
                                result['status'] = 'failed'
                        else:
                            result['warnings'].append(
                                f"{network_key} WBTC: Missing parameter {param}"
                            )
                    
                    result['details'][network_key] = network_details
                    break
            
            if not wbtc_found and network_key in ['ethereum', 'polygon', 'arbitrum', 'optimism']:
                result['warnings'].append(f"{network_key}: WBTC not found")
        
        return result
    
    def _validate_stablecoin_reserve_factors(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate stablecoin reserve factor increases."""
        result = {
            'status': 'passed',
            'description': 'Stablecoin reserve factor increases validation',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        config = self.risk_updates_2025['stablecoin_reserve_factors']
        expected_increases = config['expected_increases']
        
        for network_key, expected_values in expected_increases.items():
            if network_key not in data:
                result['warnings'].append(f"Network {network_key} not found in data")
                continue
            
            network_details = {}
            
            for asset in data[network_key]:
                symbol = asset.get('symbol', '')
                if symbol in expected_values:
                    expected_rf = expected_values[symbol]
                    actual_rf = asset.get('reserve_factor', 0)
                    
                    if abs(actual_rf - expected_rf) <= 0.05:  # 5% tolerance
                        network_details[symbol] = {
                            'status': 'passed',
                            'actual': actual_rf,
                            'expected': expected_rf
                        }
                    else:
                        network_details[symbol] = {
                            'status': 'failed',
                            'actual': actual_rf,
                            'expected': expected_rf
                        }
                        result['errors'].append(
                            f"{network_key} {symbol} reserve_factor: expected {expected_rf}, got {actual_rf}"
                        )
                        result['status'] = 'failed'
            
            result['details'][network_key] = network_details
        
        return result
    
    def _validate_dai_ltv_adjustment(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate DAI LTV adjustment on Ethereum."""
        result = {
            'status': 'passed',
            'description': 'DAI LTV adjustment validation (Ethereum)',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        config = self.risk_updates_2025['dai_ltv_adjustment']
        
        if 'ethereum' not in data:
            result['status'] = 'failed'
            result['errors'].append("Ethereum network not found in data")
            return result
        
        dai_found = False
        for asset in data['ethereum']:
            if asset.get('symbol') == 'DAI':
                dai_found = True
                actual_ltv = asset.get('loan_to_value', 0)
                expected_ltv = config['new_value']
                tolerance = config['tolerance']
                
                if abs(actual_ltv - expected_ltv) <= tolerance:
                    result['details'] = {
                        'status': 'passed',
                        'actual_ltv': actual_ltv,
                        'expected_ltv': expected_ltv
                    }
                else:
                    result['status'] = 'failed'
                    result['errors'].append(
                        f"Ethereum DAI LTV: expected {expected_ltv}, got {actual_ltv}"
                    )
                    result['details'] = {
                        'status': 'failed',
                        'actual_ltv': actual_ltv,
                        'expected_ltv': expected_ltv,
                        'difference': abs(actual_ltv - expected_ltv)
                    }
                break
        
        if not dai_found:
            result['status'] = 'failed'
            result['errors'].append("DAI not found on Ethereum")
        
        return result
    
    def _validate_polygon_usdc_disable(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate Polygon native USDC collateral disable."""
        result = {
            'status': 'passed',
            'description': 'Polygon native USDC collateral disable validation',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        config = self.risk_updates_2025['polygon_usdc_collateral_disable']
        
        if 'polygon' not in data:
            result['status'] = 'failed'
            result['errors'].append("Polygon network not found in data")
            return result
        
        usdc_found = False
        for asset in data['polygon']:
            symbol = asset.get('symbol', '')
            # Look for native USDC (not USDC.e)
            if symbol == 'USDC':
                usdc_found = True
                actual_ltv = asset.get('loan_to_value', 0)
                expected_ltv = config['expected_value']
                tolerance = config['tolerance']
                
                if abs(actual_ltv - expected_ltv) <= tolerance:
                    result['details'] = {
                        'status': 'passed',
                        'actual_ltv': actual_ltv,
                        'expected_ltv': expected_ltv,
                        'note': 'Native USDC correctly disabled as collateral'
                    }
                else:
                    result['status'] = 'failed'
                    result['errors'].append(
                        f"Polygon native USDC LTV: expected {expected_ltv}, got {actual_ltv}"
                    )
                    result['details'] = {
                        'status': 'failed',
                        'actual_ltv': actual_ltv,
                        'expected_ltv': expected_ltv
                    }
                break
        
        if not usdc_found:
            result['warnings'].append("Native USDC not found on Polygon (might be expected)")
        
        return result
    
    def _validate_network_expansions(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate 2025 network expansions."""
        result = {
            'status': 'passed',
            'description': '2025 network expansion validation',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        config = self.risk_updates_2025['new_network_expansions']
        expected_networks = set(config['expected_networks'])
        actual_networks = set(data.keys())
        minimum_networks = config['minimum_networks']
        
        # Check network count
        if len(actual_networks) >= minimum_networks:
            result['details']['network_count'] = {
                'status': 'passed',
                'actual': len(actual_networks),
                'minimum': minimum_networks
            }
        else:
            result['status'] = 'failed'
            result['errors'].append(
                f"Insufficient networks: expected >= {minimum_networks}, got {len(actual_networks)}"
            )
            result['details']['network_count'] = {
                'status': 'failed',
                'actual': len(actual_networks),
                'minimum': minimum_networks
            }
        
        # Check for expected networks
        missing_networks = expected_networks - actual_networks
        extra_networks = actual_networks - expected_networks
        
        result['details']['network_comparison'] = {
            'expected': list(expected_networks),
            'actual': list(actual_networks),
            'missing': list(missing_networks),
            'extra': list(extra_networks)
        }
        
        if missing_networks:
            result['warnings'].extend([
                f"Missing expected network: {network}" for network in missing_networks
            ])
        
        if extra_networks:
            result['details']['extra_networks_note'] = "Extra networks found (this is good - expansion beyond expectations)"
        
        return result


def load_data_from_file(filepath: str) -> Optional[Dict[str, List[Dict]]]:
    """Load Aave data from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"📂 Loaded data from {filepath}")
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None


def print_validation_summary(results: Dict[str, Any]):
    """Print validation results summary."""
    summary = results['summary']
    
    print(f"\n📊 2025 Risk Parameter Updates Validation Summary:")
    print(f"   ✅ Passed: {summary['passed_validations']}/{summary['total_validations']}")
    print(f"   ❌ Failed: {summary['failed_validations']}/{summary['total_validations']}")
    print(f"   ⚠️  Warnings: {summary['warnings']}")
    print(f"   📈 Success rate: {summary['passed_validations']/max(summary['total_validations'], 1)*100:.1f}%")
    
    print(f"\n📋 Individual Validation Results:")
    for validation_name, validation_result in results['validations'].items():
        status_emoji = "✅" if validation_result['status'] == 'passed' else "❌"
        print(f"   {status_emoji} {validation_name}: {validation_result['status']}")
        
        if validation_result.get('errors'):
            for error in validation_result['errors'][:3]:  # Show first 3 errors
                print(f"      ❌ {error}")
            if len(validation_result['errors']) > 3:
                print(f"      ... and {len(validation_result['errors']) - 3} more errors")


def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(description='Validate 2025 Aave V3 Risk Parameter Updates')
    parser.add_argument('--data-file', default='aave_v3_data.json', help='JSON data file to validate')
    parser.add_argument('--save-report', action='store_true', help='Save detailed validation report')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🔍 Aave V3 2025 Risk Parameter Updates Validation")
    print("=" * 55)
    
    # Load data
    data = load_data_from_file(args.data_file)
    if not data:
        return 1
    
    print(f"📊 Loaded data for {len(data)} networks")
    total_assets = sum(len(assets) for assets in data.values())
    print(f"📈 Total assets: {total_assets}")
    
    # Run 2025 validation
    validator = Risk2025Validator()
    results = validator.validate_2025_updates(data)
    
    # Print summary
    print_validation_summary(results)
    
    # Print detailed results if verbose
    if args.verbose:
        print(f"\n📋 Detailed Validation Results:")
        for validation_name, validation_result in results['validations'].items():
            print(f"\n🔍 {validation_name}:")
            print(f"   Status: {validation_result['status']}")
            print(f"   Description: {validation_result['description']}")
            
            if validation_result.get('details'):
                print(f"   Details: {json.dumps(validation_result['details'], indent=4)}")
            
            if validation_result.get('warnings'):
                print(f"   Warnings:")
                for warning in validation_result['warnings']:
                    print(f"     ⚠️  {warning}")
            
            if validation_result.get('errors'):
                print(f"   Errors:")
                for error in validation_result['errors']:
                    print(f"     ❌ {error}")
    
    # Save detailed report if requested
    if args.save_report:
        report_file = 'risk_2025_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📋 Detailed validation report saved to {report_file}")
    
    # Return appropriate exit code
    summary = results['summary']
    if summary['failed_validations'] > 0:
        print("\n❌ Validation failed - some 2025 updates not properly implemented")
        return 1
    elif summary['warnings'] > 10:
        print("\n⚠️  Validation completed with many warnings")
        return 2
    else:
        print("\n✅ All 2025 risk parameter updates validated successfully")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)