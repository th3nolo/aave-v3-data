#!/usr/bin/env python3
"""
Protocol Value Comparison Tool
Compares fetched Aave V3 data against known protocol values and historical data.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class ProtocolValueComparator:
    """Tool for comparing protocol values against known benchmarks."""
    
    def __init__(self):
        # Reference values for major assets (updated for 2025)
        self.reference_values = {
            'ethereum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'expected_range': {
                        'liquidation_threshold': (0.75, 0.80),
                        'loan_to_value': (0.70, 0.78),
                        'reserve_factor': (0.08, 0.15)
                    }
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'expected_range': {
                        'liquidation_threshold': (0.80, 0.85),
                        'loan_to_value': (0.75, 0.82),
                        'reserve_factor': (0.10, 0.20)
                    }
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,  # Updated from 0.70
                    'loan_to_value': 0.73,          # Updated from 0.65
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,         # Updated from 0.20
                    'expected_range': {
                        'liquidation_threshold': (0.75, 0.80),
                        'loan_to_value': (0.70, 0.75),
                        'reserve_factor': (0.45, 0.55)
                    },
                    'governance_note': "Updated in 2025 governance proposal"
                }
            },
            'polygon': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.00,  # Disabled as collateral
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,
                    'expected_range': {
                        'liquidation_threshold': (0.75, 0.80),
                        'loan_to_value': (0.00, 0.00),  # Should remain 0
                        'reserve_factor': (0.55, 0.65)
                    },
                    'governance_note': "Native USDC disabled as collateral on Polygon"
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,  # Updated from 0.10
                    'expected_range': {
                        'liquidation_threshold': (0.75, 0.80),
                        'loan_to_value': (0.70, 0.78),
                        'reserve_factor': (0.55, 0.65)
                    }
                }
            }
        }
        
        # Historical comparison points
        self.historical_values = {
            '2024': {
                'WBTC': {
                    'liquidation_threshold': 0.70,
                    'loan_to_value': 0.65,
                    'reserve_factor': 0.20
                },
                'DAI': {
                    'loan_to_value': 0.75,
                    'reserve_factor': 0.10
                }
            }
        }
        
        # Critical thresholds that should trigger alerts
        self.critical_thresholds = {
            'liquidation_threshold': {
                'min': 0.50,  # Below 50% is very risky
                'max': 0.95   # Above 95% is unusual
            },
            'loan_to_value': {
                'min': 0.00,  # Can be 0 (disabled)
                'max': 0.90   # Above 90% is very risky
            },
            'reserve_factor': {
                'min': 0.00,
                'max': 0.80   # Above 80% is very high
            },
            'liquidation_bonus': {
                'min': 0.00,
                'max': 0.25   # Above 25% is very high
            }
        }
    
    def compare_data(self, data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Compare data against reference values and return detailed comparison.
        
        Args:
            data: Network data to compare
            
        Returns:
            Comparison results dictionary
        """
        comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_assets': 0,
                'matched_references': 0,
                'within_expected_range': 0,
                'outside_expected_range': 0,
                'critical_alerts': 0
            },
            'network_comparisons': {},
            'critical_alerts': [],
            'governance_changes': [],
            'historical_changes': []
        }
        
        for network_key, assets in data.items():
            network_comparison = self._compare_network(network_key, assets)
            comparison_results['network_comparisons'][network_key] = network_comparison
            
            # Update summary
            comparison_results['summary']['total_assets'] += len(assets)
            comparison_results['summary']['matched_references'] += network_comparison['matched_references']
            comparison_results['summary']['within_expected_range'] += network_comparison['within_expected_range']
            comparison_results['summary']['outside_expected_range'] += network_comparison['outside_expected_range']
            comparison_results['summary']['critical_alerts'] += len(network_comparison['critical_alerts'])
            
            # Collect alerts and changes
            comparison_results['critical_alerts'].extend(network_comparison['critical_alerts'])
            comparison_results['governance_changes'].extend(network_comparison['governance_changes'])
            comparison_results['historical_changes'].extend(network_comparison['historical_changes'])
        
        return comparison_results
    
    def _compare_network(self, network_key: str, assets: List[Dict]) -> Dict[str, Any]:
        """Compare assets in a single network."""
        network_result = {
            'network': network_key,
            'total_assets': len(assets),
            'matched_references': 0,
            'within_expected_range': 0,
            'outside_expected_range': 0,
            'asset_comparisons': [],
            'critical_alerts': [],
            'governance_changes': [],
            'historical_changes': []
        }
        
        reference_network = self.reference_values.get(network_key, {})
        
        for asset in assets:
            symbol = asset.get('symbol', 'UNKNOWN')
            asset_comparison = self._compare_asset(network_key, symbol, asset, reference_network.get(symbol))
            
            network_result['asset_comparisons'].append(asset_comparison)
            
            if asset_comparison['has_reference']:
                network_result['matched_references'] += 1
            
            if asset_comparison['within_expected_range']:
                network_result['within_expected_range'] += 1
            else:
                network_result['outside_expected_range'] += 1
            
            # Collect alerts and changes
            network_result['critical_alerts'].extend(asset_comparison['critical_alerts'])
            network_result['governance_changes'].extend(asset_comparison['governance_changes'])
            network_result['historical_changes'].extend(asset_comparison['historical_changes'])
        
        return network_result
    
    def _compare_asset(self, network_key: str, symbol: str, asset: Dict, reference: Optional[Dict]) -> Dict[str, Any]:
        """Compare a single asset against reference values."""
        asset_comparison = {
            'network': network_key,
            'symbol': symbol,
            'asset_address': asset.get('asset_address', ''),
            'has_reference': reference is not None,
            'within_expected_range': True,
            'parameter_comparisons': {},
            'critical_alerts': [],
            'governance_changes': [],
            'historical_changes': []
        }
        
        if not reference:
            return asset_comparison
        
        # Compare each parameter
        for param, expected_value in reference.items():
            if param in ['expected_range', 'governance_note']:
                continue
            
            if param in asset:
                actual_value = asset[param]
                param_comparison = self._compare_parameter(
                    network_key, symbol, param, actual_value, expected_value, reference
                )
                asset_comparison['parameter_comparisons'][param] = param_comparison
                
                if not param_comparison['within_range']:
                    asset_comparison['within_expected_range'] = False
                
                # Check for critical alerts
                if param in self.critical_thresholds:
                    threshold = self.critical_thresholds[param]
                    if actual_value < threshold['min'] or actual_value > threshold['max']:
                        alert = {
                            'network': network_key,
                            'symbol': symbol,
                            'parameter': param,
                            'value': actual_value,
                            'threshold': threshold,
                            'severity': 'critical'
                        }
                        asset_comparison['critical_alerts'].append(alert)
                
                # Check for governance changes
                if 'governance_note' in reference:
                    change = {
                        'network': network_key,
                        'symbol': symbol,
                        'parameter': param,
                        'current_value': actual_value,
                        'expected_value': expected_value,
                        'note': reference['governance_note']
                    }
                    asset_comparison['governance_changes'].append(change)
                
                # Check for historical changes
                historical_ref = self.historical_values.get('2024', {}).get(symbol, {})
                if param in historical_ref:
                    historical_value = historical_ref[param]
                    if abs(actual_value - historical_value) > 0.05:  # 5% change threshold
                        change = {
                            'network': network_key,
                            'symbol': symbol,
                            'parameter': param,
                            'current_value': actual_value,
                            'historical_value': historical_value,
                            'change': actual_value - historical_value,
                            'change_percent': ((actual_value - historical_value) / historical_value) * 100
                        }
                        asset_comparison['historical_changes'].append(change)
        
        return asset_comparison
    
    def _compare_parameter(self, network_key: str, symbol: str, param: str, actual: float, expected: float, reference: Dict) -> Dict[str, Any]:
        """Compare a single parameter value."""
        comparison = {
            'parameter': param,
            'actual_value': actual,
            'expected_value': expected,
            'difference': actual - expected,
            'difference_percent': ((actual - expected) / expected * 100) if expected != 0 else 0,
            'within_range': True,
            'range_info': None
        }
        
        # Check if within expected range
        expected_range = reference.get('expected_range', {}).get(param)
        if expected_range:
            min_val, max_val = expected_range
            comparison['within_range'] = min_val <= actual <= max_val
            comparison['range_info'] = {
                'min': min_val,
                'max': max_val,
                'within_range': comparison['within_range']
            }
        else:
            # Use tolerance if no specific range
            tolerance = 0.15 if param in ['reserve_factor'] else 0.10  # 15% for reserve factor, 10% for others
            comparison['within_range'] = abs(comparison['difference_percent']) <= tolerance * 100
        
        return comparison
    
    def print_comparison_summary(self, results: Dict[str, Any]):
        """Print a summary of comparison results."""
        summary = results['summary']
        
        print("\n" + "=" * 60)
        print("PROTOCOL VALUE COMPARISON SUMMARY")
        print("=" * 60)
        
        print(f"📊 Total assets analyzed: {summary['total_assets']}")
        print(f"🎯 Assets with reference values: {summary['matched_references']}")
        print(f"✅ Within expected range: {summary['within_expected_range']}")
        print(f"⚠️  Outside expected range: {summary['outside_expected_range']}")
        print(f"🚨 Critical alerts: {summary['critical_alerts']}")
        
        # Print critical alerts
        if results['critical_alerts']:
            print(f"\n🚨 CRITICAL ALERTS ({len(results['critical_alerts'])}):")
            for alert in results['critical_alerts']:
                print(f"   {alert['network']} {alert['symbol']} {alert['parameter']}: "
                      f"{alert['value']} (threshold: {alert['threshold']['min']}-{alert['threshold']['max']})")
        
        # Print governance changes
        if results['governance_changes']:
            print(f"\n📋 GOVERNANCE CHANGES ({len(results['governance_changes'])}):")
            for change in results['governance_changes'][:5]:  # Limit to first 5
                print(f"   {change['network']} {change['symbol']} {change['parameter']}: "
                      f"{change['current_value']} (expected: {change['expected_value']})")
                print(f"      Note: {change['note']}")
        
        # Print significant historical changes
        significant_changes = [c for c in results['historical_changes'] if abs(c['change_percent']) > 20]
        if significant_changes:
            print(f"\n📈 SIGNIFICANT HISTORICAL CHANGES ({len(significant_changes)}):")
            for change in significant_changes[:5]:  # Limit to first 5
                print(f"   {change['network']} {change['symbol']} {change['parameter']}: "
                      f"{change['current_value']} (was: {change['historical_value']}, "
                      f"change: {change['change_percent']:+.1f}%)")
        
        print("=" * 60)
    
    def print_detailed_comparison(self, results: Dict[str, Any], network_filter: Optional[str] = None):
        """Print detailed comparison results."""
        print("\n" + "=" * 80)
        print("DETAILED PROTOCOL VALUE COMPARISON")
        print("=" * 80)
        
        for network_key, network_result in results['network_comparisons'].items():
            if network_filter and network_key != network_filter:
                continue
            
            print(f"\n🌐 Network: {network_key.upper()}")
            print(f"   Assets: {network_result['total_assets']}, "
                  f"With references: {network_result['matched_references']}, "
                  f"In range: {network_result['within_expected_range']}")
            
            for asset_comp in network_result['asset_comparisons']:
                if not asset_comp['has_reference']:
                    continue
                
                symbol = asset_comp['symbol']
                status = "✅" if asset_comp['within_expected_range'] else "⚠️"
                print(f"\n   {status} {symbol}")
                
                for param, param_comp in asset_comp['parameter_comparisons'].items():
                    actual = param_comp['actual_value']
                    expected = param_comp['expected_value']
                    diff_pct = param_comp['difference_percent']
                    
                    range_status = "✅" if param_comp['within_range'] else "❌"
                    print(f"      {range_status} {param}: {actual:.4f} "
                          f"(expected: {expected:.4f}, diff: {diff_pct:+.1f}%)")
                    
                    if param_comp['range_info']:
                        range_info = param_comp['range_info']
                        print(f"         Range: [{range_info['min']:.3f}, {range_info['max']:.3f}]")


def load_data_file(filepath: str) -> Dict[str, List[Dict]]:
    """Load data from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Data file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return {}


def main():
    """Main entry point for protocol value comparison."""
    parser = argparse.ArgumentParser(description='Aave V3 Protocol Value Comparison Tool')
    parser.add_argument('--data-file', default='aave_v3_data.json', help='JSON data file to compare')
    parser.add_argument('--save-report', help='Save comparison report to file')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed comparison')
    parser.add_argument('--network', help='Filter to specific network')
    parser.add_argument('--critical-only', action='store_true', help='Show only critical alerts')
    parser.add_argument('--governance-focus', action='store_true', help='Focus on governance changes')
    
    args = parser.parse_args()
    
    print("📊 Aave V3 Protocol Value Comparison Tool")
    print("=" * 50)
    
    # Load data
    data = load_data_file(args.data_file)
    if not data:
        print("❌ No data to compare")
        return 1
    
    print(f"📈 Loaded data for {len(data)} networks")
    
    # Create comparator and run comparison
    comparator = ProtocolValueComparator()
    results = comparator.compare_data(data)
    
    # Print results
    if args.critical_only:
        if results['critical_alerts']:
            print(f"\n🚨 CRITICAL ALERTS ({len(results['critical_alerts'])}):")
            for alert in results['critical_alerts']:
                print(f"   {alert['network']} {alert['symbol']} {alert['parameter']}: "
                      f"{alert['value']} (safe range: {alert['threshold']['min']}-{alert['threshold']['max']})")
        else:
            print("\n✅ No critical alerts found")
    elif args.governance_focus:
        if results['governance_changes']:
            print(f"\n📋 GOVERNANCE CHANGES ({len(results['governance_changes'])}):")
            for change in results['governance_changes']:
                print(f"   {change['network']} {change['symbol']} {change['parameter']}: "
                      f"{change['current_value']} (expected: {change['expected_value']})")
                print(f"      {change['note']}")
        else:
            print("\n✅ No governance changes detected")
    else:
        comparator.print_comparison_summary(results)
        
        if args.detailed:
            comparator.print_detailed_comparison(results, args.network)
    
    # Save report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📋 Comparison report saved to {args.save_report}")
    
    # Return appropriate exit code
    if results['summary']['critical_alerts'] > 0:
        print(f"\n🚨 Found {results['summary']['critical_alerts']} critical alerts")
        return 2  # Warning exit code
    elif results['summary']['outside_expected_range'] > 0:
        print(f"\n⚠️  {results['summary']['outside_expected_range']} assets outside expected range")
        return 0  # Success but with warnings
    else:
        print(f"\n✅ All assets within expected ranges")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)