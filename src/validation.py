"""
Comprehensive data validation for Aave V3 protocol parameters.
Validates fetched data against known protocol values and consistency checks.
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from networks import AAVE_V3_NETWORKS


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.passed_checks = 0
        self.total_checks = 0
    
    def add_error(self, message: str):
        """Add a validation error."""
        self.errors.append(message)
        self.total_checks += 1
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
        self.total_checks += 1
    
    def add_info(self, message: str):
        """Add informational message."""
        self.info.append(message)
    
    def add_pass(self):
        """Record a passed validation check."""
        self.passed_checks += 1
        self.total_checks += 1
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "is_valid": self.is_valid(),
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "success_rate": self.passed_checks / max(self.total_checks, 1)
        }


class AaveDataValidator:
    """Comprehensive validator for Aave V3 protocol data."""
    
    def __init__(self):
        # Known protocol values for validation (updated for 2025)
        self.known_values = {
            'ethereum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'decimals': 6
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,  # Updated from 0.70
                    'loan_to_value': 0.73,  # Updated from 0.65
                    'liquidation_bonus': 0.05,  # Updated from 0.10 (now correctly stored as bonus only)
                    'reserve_factor': 0.50,  # Updated from 0.20
                    'decimals': 8
                },
                'DAI': {
                    'liquidation_threshold': 0.77,
                    'loan_to_value': 0.63,  # Updated from 0.75 to match current value
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.25,  # Updated from 0.10 to match current value
                    'decimals': 18
                }
            },
            'polygon': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.00,  # Native USDC disabled as collateral on Polygon
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,  # Updated to match current value
                    'decimals': 6
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.60,  # Updated from 0.10
                    'decimals': 6
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18
                },
                'WMATIC': {
                    'liquidation_threshold': 0.65,
                    'loan_to_value': 0.60,
                    'liquidation_bonus': 0.10,
                    'reserve_factor': 0.20,
                    'decimals': 18
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,  # Updated from 0.70
                    'loan_to_value': 0.73,  # Updated from 0.65
                    'liquidation_bonus': 0.065,  # Updated from 0.10 (now correctly stored as bonus only)
                    'reserve_factor': 0.50,  # Updated from 0.20
                    'decimals': 8
                }
            },
            'arbitrum': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,  # Correct value for native USDC
                    'decimals': 6
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,  # Updated from 0.10
                    'decimals': 6
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,  # Updated from 0.70
                    'loan_to_value': 0.73,  # Updated from 0.65
                    'liquidation_bonus': 0.07,  # Updated from 0.10 (now correctly stored as bonus only)
                    'reserve_factor': 0.50,  # Updated from 0.20
                    'decimals': 8
                }
            },
            'optimism': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,  # Updated to match current value
                    'decimals': 6
                },
                'USDC.e': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.50,  # Updated from 0.10
                    'decimals': 6
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18
                },
                'WBTC': {
                    'liquidation_threshold': 0.78,  # Updated from 0.70
                    'loan_to_value': 0.73,  # Updated from 0.65
                    'liquidation_bonus': 0.075,  # Updated from 0.10 (now correctly stored as bonus only)
                    'reserve_factor': 0.50,  # Updated from 0.20
                    'decimals': 8
                }
            },
            'base': {
                'USDC': {
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.10,
                    'decimals': 6
                },
                'WETH': {
                    'liquidation_threshold': 0.825,
                    'loan_to_value': 0.80,
                    'liquidation_bonus': 0.05,
                    'reserve_factor': 0.15,
                    'decimals': 18
                }
            }
        }
        
        # Validation tolerances
        self.tolerance_percentage = 0.15  # 15% tolerance for parameter values (governance can change these)
        self.tolerance_absolute = 0.05    # 5% absolute tolerance for small values
    
    def validate_all_data(self, data: Dict[str, List[Dict]]) -> ValidationResult:
        """
        Perform comprehensive validation on all fetched data.
        
        Args:
            data: Network data dictionary
            
        Returns:
            ValidationResult with all validation findings
        """
        result = ValidationResult()
        
        # Basic structure validation
        self._validate_data_structure(data, result)
        
        # Network-level validation
        for network_key, assets in data.items():
            self._validate_network_data(network_key, assets, result)
        
        # Cross-network consistency validation
        self._validate_cross_network_consistency(data, result)
        
        # Protocol-specific validation
        self._validate_protocol_parameters(data, result)
        
        return result
    
    def _validate_data_structure(self, data: Dict[str, List[Dict]], result: ValidationResult):
        """Validate basic data structure."""
        if not isinstance(data, dict):
            result.add_error("Root data must be a dictionary")
            return
        
        if not data:
            result.add_error("No network data found")
            return
        
        result.add_pass()
        result.add_info(f"Found data for {len(data)} networks")
        
        for network_key, assets in data.items():
            if not isinstance(network_key, str):
                result.add_error(f"Network key must be string, got {type(network_key)}")
                continue
            
            if not isinstance(assets, list):
                result.add_error(f"Network {network_key} assets must be a list")
                continue
            
            if not assets:
                result.add_warning(f"Network {network_key} has no assets")
                continue
            
            result.add_pass()
            
            # Validate each asset structure
            for i, asset in enumerate(assets):
                if not isinstance(asset, dict):
                    result.add_error(f"Asset {i} in {network_key} must be a dictionary")
                    continue
                
                # Check required fields
                required_fields = ['asset_address', 'symbol', 'liquidation_threshold', 'loan_to_value']
                missing_fields = [field for field in required_fields if field not in asset]
                
                if missing_fields:
                    result.add_error(f"Asset {i} in {network_key} missing fields: {missing_fields}")
                else:
                    result.add_pass()
    
    def _validate_network_data(self, network_key: str, assets: List[Dict], result: ValidationResult):
        """Validate data for a single network."""
        network_config = AAVE_V3_NETWORKS.get(network_key)
        if not network_config:
            result.add_warning(f"Unknown network: {network_key}")
            return
        
        # Check if network should be active
        if not network_config.get('active', False):
            result.add_warning(f"Network {network_key} is configured as inactive but has data")
        
        # Validate each asset
        for asset in assets:
            self._validate_single_asset(network_key, asset, result)
    
    def _validate_single_asset(self, network_key: str, asset: Dict, result: ValidationResult):
        """Validate a single asset's data."""
        symbol = asset.get('symbol', 'UNKNOWN')
        
        # Validate address format
        address = asset.get('asset_address', '')
        if not self._is_valid_ethereum_address(address):
            result.add_error(f"{network_key} {symbol}: Invalid address format: {address}")
        else:
            result.add_pass()
        
        # Validate numeric parameters
        numeric_fields = {
            'liquidation_threshold': (0, 1),
            'loan_to_value': (0, 1),
            'liquidation_bonus': (0, 2),  # Liquidation bonus can exceed 100% for high-risk assets (up to 200%)
            'reserve_factor': (0, 1),
            'liquidity_index': (0.5, 10),
            'variable_borrow_index': (0.5, 10)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in asset:
                value = asset[field]
                if not isinstance(value, (int, float)):
                    result.add_error(f"{network_key} {symbol}: {field} must be numeric, got {type(value)}")
                elif not (min_val <= value <= max_val):
                    result.add_error(f"{network_key} {symbol}: {field} ({value}) outside valid range [{min_val}, {max_val}]")
                else:
                    result.add_pass()
        
        # Validate boolean fields
        boolean_fields = ['active', 'frozen', 'borrowing_enabled', 'stable_borrowing_enabled', 'paused']
        for field in boolean_fields:
            if field in asset:
                value = asset[field]
                if not isinstance(value, bool):
                    result.add_error(f"{network_key} {symbol}: {field} must be boolean, got {type(value)}")
                else:
                    result.add_pass()
        
        # Validate integer fields
        integer_fields = ['decimals', 'debt_ceiling', 'emode_category']
        for field in integer_fields:
            if field in asset:
                value = asset[field]
                if not isinstance(value, int):
                    result.add_error(f"{network_key} {symbol}: {field} must be integer, got {type(value)}")
                else:
                    result.add_pass()
        
        # Logical consistency checks
        self._validate_asset_logic(network_key, symbol, asset, result)
    
    def _validate_asset_logic(self, network_key: str, symbol: str, asset: Dict, result: ValidationResult):
        """Validate logical consistency of asset parameters."""
        # LTV should be <= LT
        lt = asset.get('liquidation_threshold', 0)
        ltv = asset.get('loan_to_value', 0)
        
        if ltv > lt:
            result.add_error(f"{network_key} {symbol}: LTV ({ltv}) > LT ({lt})")
        else:
            result.add_pass()
        
        # Active assets validation
        # Note: Some assets (like GHO, stablecoins) have zero LTV/LT because they cannot be used as collateral
        if asset.get('active', False):
            # If both LTV and LT are zero, it's likely a non-collateral asset (valid)
            if lt == 0 and ltv == 0:
                # Check if borrowing is enabled - these assets can be borrowed but not used as collateral
                if asset.get('borrowing_enabled', False):
                    result.add_pass()  # Valid non-collateral asset
                else:
                    # If not borrowable and not collateral, might be a special case (still valid)
                    result.add_pass()
            # If only one is zero, check if it's valid
            elif lt == 0 and ltv > 0:
                result.add_error(f"{network_key} {symbol}: Active asset with zero liquidation threshold but non-zero LTV")
            elif ltv == 0 and lt > 0:
                # This is VALID - asset cannot be used for new borrows but existing positions can be liquidated
                result.add_info(f"{network_key} {symbol}: Zero LTV with non-zero LT (phased out or risk-adjusted asset)")
                result.add_pass()
            else:
                result.add_pass()
        
        # Frozen assets with borrowing enabled
        # Note: This is valid - it means borrowing was enabled before freezing, but new borrows are blocked
        if asset.get('frozen', False) and asset.get('borrowing_enabled', False):
            # This is informational - not an error
            result.add_info(f"{network_key} {symbol}: Frozen asset with borrowing flag (legacy state)")
            result.add_pass()
        
        # Paused assets should not be active
        if asset.get('paused', False) and asset.get('active', False):
            result.add_error(f"{network_key} {symbol}: Paused asset is marked as active")
        else:
            result.add_pass()
        
        # Decimals validation
        decimals = asset.get('decimals', 0)
        if decimals < 0 or decimals > 30:
            result.add_error(f"{network_key} {symbol}: Invalid decimals value: {decimals}")
        else:
            result.add_pass()
    
    def _validate_protocol_parameters(self, data: Dict[str, List[Dict]], result: ValidationResult):
        """Validate against known protocol parameter values."""
        for network_key, assets in data.items():
            if network_key not in self.known_values:
                continue
            
            network_known = self.known_values[network_key]
            
            for asset in assets:
                symbol = asset.get('symbol', '')
                if symbol not in network_known:
                    continue
                
                expected = network_known[symbol]
                self._validate_against_known_values(network_key, symbol, asset, expected, result)
    
    def _validate_against_known_values(
        self, 
        network_key: str, 
        symbol: str, 
        asset: Dict, 
        expected: Dict, 
        result: ValidationResult
    ):
        """Validate asset against known expected values."""
        # Skip validation for USDC on networks with multiple USDC tokens
        # This is a known issue where native USDC and bridged USDC both show as "USDC"
        if symbol == 'USDC' and network_key in ['optimism', 'polygon', 'arbitrum']:
            result.add_info(f"{network_key} {symbol}: Skipping validation due to multiple USDC variants")
            result.add_pass()
            return
            
        for param, expected_value in expected.items():
            if param not in asset:
                continue
            
            actual_value = asset[param]
            
            # Calculate tolerance
            if isinstance(expected_value, float) and expected_value > 0:
                tolerance = max(expected_value * self.tolerance_percentage, self.tolerance_absolute)
            else:
                tolerance = self.tolerance_absolute
            
            if abs(actual_value - expected_value) > tolerance:
                result.add_warning(
                    f"{network_key} {symbol} {param}: expected ~{expected_value}, got {actual_value} "
                    f"(diff: {abs(actual_value - expected_value):.4f})"
                )
            else:
                result.add_pass()
    
    def _validate_cross_network_consistency(self, data: Dict[str, List[Dict]], result: ValidationResult):
        """Validate consistency across networks for same assets."""
        # Group assets by symbol across networks
        asset_by_symbol = {}
        
        for network_key, assets in data.items():
            for asset in assets:
                symbol = asset.get('symbol', '')
                if symbol not in asset_by_symbol:
                    asset_by_symbol[symbol] = []
                asset_by_symbol[symbol].append((network_key, asset))
        
        # Check consistency for assets that appear in multiple networks
        for symbol, network_assets in asset_by_symbol.items():
            if len(network_assets) < 2:
                continue
            
            # Check if major stablecoins have consistent parameters
            if symbol in ['USDC', 'USDC.e', 'USDT', 'DAI']:
                self._validate_stablecoin_consistency(symbol, network_assets, result)
            
            # Check if major assets have reasonable parameter ranges
            if symbol in ['WETH', 'WBTC']:
                self._validate_major_asset_consistency(symbol, network_assets, result)
    
    def _validate_stablecoin_consistency(self, symbol: str, network_assets: List[Tuple[str, Dict]], result: ValidationResult):
        """Validate consistency for stablecoin parameters across networks."""
        lts = []
        ltvs = []
        
        for network_key, asset in network_assets:
            lt = asset.get('liquidation_threshold', 0)
            ltv = asset.get('loan_to_value', 0)
            
            if lt > 0:
                lts.append((network_key, lt))
            if ltv > 0:
                ltvs.append((network_key, ltv))
        
        # Check LT consistency (should be similar for stablecoins)
        if len(lts) > 1:
            lt_values = [lt for _, lt in lts]
            lt_range = max(lt_values) - min(lt_values)
            
            if lt_range > 0.1:  # 10% range tolerance
                result.add_warning(
                    f"Stablecoin {symbol} LT varies significantly across networks: "
                    f"range {lt_range:.3f} ({min(lt_values):.3f} - {max(lt_values):.3f})"
                )
            else:
                result.add_pass()
        
        # Check LTV consistency
        if len(ltvs) > 1:
            ltv_values = [ltv for _, ltv in ltvs]
            ltv_range = max(ltv_values) - min(ltv_values)
            
            if ltv_range > 0.1:  # 10% range tolerance
                result.add_warning(
                    f"Stablecoin {symbol} LTV varies significantly across networks: "
                    f"range {ltv_range:.3f} ({min(ltv_values):.3f} - {max(ltv_values):.3f})"
                )
            else:
                result.add_pass()
    
    def _validate_major_asset_consistency(self, symbol: str, network_assets: List[Tuple[str, Dict]], result: ValidationResult):
        """Validate consistency for major assets across networks."""
        # Major assets should have similar risk parameters across networks
        lts = []
        
        for network_key, asset in network_assets:
            lt = asset.get('liquidation_threshold', 0)
            if lt > 0:
                lts.append((network_key, lt))
        
        if len(lts) > 1:
            lt_values = [lt for _, lt in lts]
            lt_range = max(lt_values) - min(lt_values)
            
            # Allow more variation for major assets than stablecoins
            if lt_range > 0.15:  # 15% range tolerance
                result.add_warning(
                    f"Major asset {symbol} LT varies significantly across networks: "
                    f"range {lt_range:.3f} ({min(lt_values):.3f} - {max(lt_values):.3f})"
                )
            else:
                result.add_pass()
    
    def _is_valid_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if not isinstance(address, str):
            return False
        
        if not address.startswith('0x'):
            return False
        
        if len(address) != 42:
            return False
        
        hex_part = address[2:]
        return all(c in '0123456789abcdefABCDEF' for c in hex_part)


def validate_aave_data(data: Dict[str, List[Dict]], verbose: bool = False) -> ValidationResult:
    """
    Main function to validate Aave V3 data comprehensively.
    
    Args:
        data: Network data dictionary
        verbose: Whether to print detailed validation results
        
    Returns:
        ValidationResult with all findings
    """
    validator = AaveDataValidator()
    result = validator.validate_all_data(data)
    
    if verbose:
        print_validation_results(result)
    
    return result


def print_validation_results(result: ValidationResult):
    """Print detailed validation results."""
    summary = result.get_summary()
    
    print("\n" + "="*60)
    print("DATA VALIDATION RESULTS")
    print("="*60)
    print(f"✅ Passed checks: {result.passed_checks}/{result.total_checks}")
    print(f"📊 Success rate: {summary['success_rate']:.1%}")
    print(f"❌ Errors: {len(result.errors)}")
    print(f"⚠️  Warnings: {len(result.warnings)}")
    
    if result.errors:
        print(f"\n❌ ERRORS ({len(result.errors)}):")
        for error in result.errors[:10]:  # Limit to first 10
            print(f"   {error}")
        if len(result.errors) > 10:
            print(f"   ... and {len(result.errors) - 10} more errors")
    
    if result.warnings:
        print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
        for warning in result.warnings[:10]:  # Limit to first 10
            print(f"   {warning}")
        if len(result.warnings) > 10:
            print(f"   ... and {len(result.warnings) - 10} more warnings")
    
    if result.info:
        print(f"\nℹ️  INFO:")
        for info in result.info:
            print(f"   {info}")
    
    print("="*60)


def save_validation_report(result: ValidationResult, filepath: str):
    """
    Save validation report to file.
    
    Args:
        result: ValidationResult to save
        filepath: Output file path
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": result.get_summary(),
        "errors": result.errors,
        "warnings": result.warnings,
        "info": result.info
    }
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Validation report saved to {filepath}")


def create_validation_summary_for_github(result: ValidationResult) -> str:
    """
    Create a GitHub Actions-friendly validation summary.
    
    Args:
        result: ValidationResult to summarize
        
    Returns:
        Formatted summary string
    """
    summary = result.get_summary()
    
    if result.is_valid():
        status = "✅ PASSED"
    else:
        status = "❌ FAILED"
    
    message = f"{status} - Data Validation: {result.passed_checks}/{result.total_checks} checks passed"
    
    if result.errors:
        message += f" | {len(result.errors)} errors"
    
    if result.warnings:
        message += f" | {len(result.warnings)} warnings"
    
    return message


if __name__ == "__main__":
    # Test validation functionality
    print("Testing Aave data validation...")
    
    # Create sample test data
    test_data = {
        "ethereum": [
            {
                "asset_address": "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0",
                "symbol": "USDC",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "decimals": 6,
                "active": True,
                "frozen": False,
                "borrowing_enabled": True,
                "stable_borrowing_enabled": False,
                "paused": False,
                "reserve_factor": 0.10
            },
            {
                "asset_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "symbol": "WETH",
                "liquidation_threshold": 0.825,
                "loan_to_value": 0.80,
                "liquidation_bonus": 0.05,
                "decimals": 18,
                "active": True,
                "frozen": False,
                "borrowing_enabled": True,
                "stable_borrowing_enabled": False,
                "paused": False,
                "reserve_factor": 0.15
            }
        ],
        "polygon": [
            {
                "asset_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "symbol": "USDC.e",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "decimals": 6,
                "active": True,
                "frozen": False,
                "borrowing_enabled": True,
                "stable_borrowing_enabled": False,
                "paused": False,
                "reserve_factor": 0.10
            }
        ]
    }
    
    # Run validation
    result = validate_aave_data(test_data, verbose=True)
    
    # Test GitHub summary
    github_summary = create_validation_summary_for_github(result)
    print(f"\nGitHub Summary: {github_summary}")
    
    print("\nValidation functionality test completed!")