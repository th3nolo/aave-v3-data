"""
JSON output generation for Aave V3 data.
Handles serialization of structured reserve data with metadata for LLM consumption.
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from networks import get_active_networks


class AaveDataJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Aave data with proper formatting."""
    
    def encode(self, obj):
        """Encode with consistent formatting for LLM consumption."""
        return super().encode(obj)
    
    def iterencode(self, obj, _one_shot=False):
        """Iterate encoding with proper decimal formatting."""
        return super().iterencode(obj, _one_shot)


def format_asset_data_for_json(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format asset data for JSON output with proper types and precision.
    
    Args:
        asset_data: Raw asset data dictionary
        
    Returns:
        Formatted asset data for JSON serialization
    """
    formatted = {}
    
    # Copy basic fields
    formatted['asset_address'] = asset_data.get('asset_address', '')
    formatted['symbol'] = asset_data.get('symbol', 'UNKNOWN')
    
    # Format decimal values with proper precision
    decimal_fields = [
        'liquidation_threshold',
        'loan_to_value', 
        'liquidation_bonus',
        'reserve_factor',
        'liquidation_protocol_fee',
        'liquidity_index',
        'variable_borrow_index',
        'current_liquidity_rate',
        'current_variable_borrow_rate'
    ]
    
    for field in decimal_fields:
        if field in asset_data:
            value = asset_data[field]
            if isinstance(value, (int, float)):
                # Format to 6 decimal places for precision
                formatted[field] = round(float(value), 6)
            else:
                formatted[field] = 0.0
        else:
            formatted[field] = 0.0
    
    # Integer fields
    integer_fields = [
        'decimals',
        'debt_ceiling',
        'emode_category',
        'last_update_timestamp'
    ]
    
    for field in integer_fields:
        if field in asset_data:
            value = asset_data[field]
            if isinstance(value, (int, float)):
                formatted[field] = int(value)
            else:
                formatted[field] = 0
        else:
            formatted[field] = 0
    
    # Boolean fields
    boolean_fields = [
        'active',
        'frozen',
        'borrowing_enabled',
        'stable_borrowing_enabled',
        'paused',
        'borrowable_in_isolation',
        'siloed_borrowing'
    ]
    
    for field in boolean_fields:
        if field in asset_data:
            formatted[field] = bool(asset_data[field])
        else:
            formatted[field] = False
    
    # Address fields
    address_fields = [
        'a_token_address',
        'variable_debt_token_address',
        'stable_debt_token_address'
    ]
    
    for field in address_fields:
        if field in asset_data:
            formatted[field] = asset_data[field]
        else:
            formatted[field] = ''
    
    # Supply and borrow caps (new 2025 parameters)
    cap_fields = [
        'supply_cap',
        'borrow_cap'
    ]
    
    for field in cap_fields:
        if field in asset_data:
            value = asset_data[field]
            if isinstance(value, (int, float)):
                formatted[field] = int(value)
            else:
                formatted[field] = 0
        else:
            formatted[field] = 0
    
    return formatted


def create_json_metadata(
    data: Dict[str, List[Dict]], 
    fetch_report: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create metadata for JSON output including data freshness and network status.
    
    Args:
        data: Network data dictionary
        fetch_report: Optional fetch report with statistics
        
    Returns:
        Metadata dictionary
    """
    now = datetime.now(timezone.utc)
    
    # Calculate network statistics
    total_networks = len(get_active_networks())
    successful_networks = len(data)
    total_assets = sum(len(assets) for assets in data.values())
    
    metadata = {
        "generated_at": now.isoformat(),
        "generated_timestamp": int(now.timestamp()),
        "last_updated": now.isoformat(),  # Add last_updated field as expected by tests
        "data_version": "1.0",
        "schema_version": "aave-v3-2025",
        "network_summary": {
            "total_active_networks": total_networks,
            "successful_networks": successful_networks,
            "failed_networks": total_networks - successful_networks,
            "success_rate": round(successful_networks / max(total_networks, 1), 4),
            "total_assets": total_assets
        },
        "data_freshness": {
            "last_update": now.isoformat(),
            "update_frequency": "daily",
            "next_update_estimate": (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                                   timedelta(days=1)).isoformat()
        }
    }
    
    # Add fetch report information if available
    if fetch_report:
        fetch_summary = fetch_report.get('fetch_summary', {})
        metadata["fetch_statistics"] = {
            "duration_seconds": fetch_summary.get('duration_seconds', 0),
            "partial_failures": fetch_summary.get('partial_failures', 0),
            "skipped_networks": fetch_summary.get('skipped_networks', 0)
        }
        
        # Add network health information
        if 'health_summary' in fetch_report:
            health = fetch_report['health_summary']
            metadata["network_health"] = {
                "healthy_networks": health.get('healthy_networks', 0),
                "unhealthy_networks": health.get('unhealthy_networks', 0),
                "monitoring_enabled": health.get('monitoring_enabled', False)
            }
    
    # Add network list for reference
    metadata["networks"] = list(data.keys())
    
    return metadata


def generate_json_output(
    data: Dict[str, List[Dict]], 
    fetch_report: Optional[Dict] = None,
    include_metadata: bool = True
) -> str:
    """
    Generate JSON output from Aave V3 data with proper formatting.
    
    Args:
        data: Network data dictionary
        fetch_report: Optional fetch report
        include_metadata: Whether to include metadata
        
    Returns:
        JSON string formatted for LLM consumption
    """
    # Format all asset data
    formatted_data = {}
    
    for network_key, assets in data.items():
        formatted_assets = []
        for asset in assets:
            formatted_asset = format_asset_data_for_json(asset)
            formatted_assets.append(formatted_asset)
        
        # Sort assets by symbol for consistency
        formatted_assets.sort(key=lambda x: x.get('symbol', ''))
        formatted_data[network_key] = formatted_assets
    
    # Create output structure with networks at root level
    output = {
        "networks": formatted_data  # Change key from "aave_v3_data" to "networks"
    }
    
    # Add metadata if requested
    if include_metadata:
        output["metadata"] = create_json_metadata(data, fetch_report)
    
    # Generate JSON with consistent formatting
    json_output = json.dumps(
        output,
        cls=AaveDataJSONEncoder,
        indent=2,
        separators=(',', ': '),
        ensure_ascii=False,
        sort_keys=True
    )
    
    return json_output


def save_json_output(
    data: Dict[str, List[Dict]], 
    filepath: str,
    fetch_report: Optional[Dict] = None,
    include_metadata: bool = True
) -> bool:
    """
    Save JSON output to file.
    
    Args:
        data: Network data dictionary
        filepath: Output file path
        fetch_report: Optional fetch report
        include_metadata: Whether to include metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        json_content = generate_json_output(data, fetch_report, include_metadata)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        print(f"📄 JSON output saved to {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save JSON output: {e}")
        return False


def validate_json_schema(data: Dict[str, List[Dict]]) -> List[str]:
    """
    Validate JSON data structure and types.
    
    Args:
        data: Network data dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Root data must be a dictionary")
        return errors
    
    for network_key, assets in data.items():
        if not isinstance(network_key, str):
            errors.append(f"Network key must be string, got {type(network_key)}")
            continue
        
        if not isinstance(assets, list):
            errors.append(f"Network {network_key} assets must be a list")
            continue
        
        for i, asset in enumerate(assets):
            if not isinstance(asset, dict):
                errors.append(f"Asset {i} in {network_key} must be a dictionary")
                continue
            
            # Validate required fields
            required_fields = ['asset_address', 'symbol']
            for field in required_fields:
                if field not in asset:
                    errors.append(f"Asset {i} in {network_key} missing required field: {field}")
            
            # Validate field types
            if 'asset_address' in asset and not isinstance(asset['asset_address'], str):
                errors.append(f"Asset {i} in {network_key} asset_address must be string")
            
            if 'symbol' in asset and not isinstance(asset['symbol'], str):
                errors.append(f"Asset {i} in {network_key} symbol must be string")
            
            # Validate decimal fields with appropriate ranges
            decimal_field_ranges = {
                'liquidation_threshold': (0, 1),
                'loan_to_value': (0, 1),
                'liquidation_bonus': (0, 2)  # Can exceed 100% for high-risk assets
            }
            
            for field, (min_val, max_val) in decimal_field_ranges.items():
                if field in asset:
                    value = asset[field]
                    if not isinstance(value, (int, float)):
                        errors.append(f"Asset {i} in {network_key} {field} must be numeric")
                    elif value < min_val or value > max_val:
                        errors.append(f"Asset {i} in {network_key} {field} must be between {min_val} and {max_val}")
    
    return errors


def create_json_summary(data: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Create summary statistics for JSON data.
    
    Args:
        data: Network data dictionary
        
    Returns:
        Summary statistics dictionary
    """
    summary = {
        "total_networks": len(data),
        "total_assets": sum(len(assets) for assets in data.values()),
        "networks": {}
    }
    
    for network_key, assets in data.items():
        network_summary = {
            "asset_count": len(assets),
            "active_assets": sum(1 for asset in assets if asset.get('active', False)),
            "borrowable_assets": sum(1 for asset in assets if asset.get('borrowing_enabled', False)),
            "symbols": [asset.get('symbol', 'UNKNOWN') for asset in assets]
        }
        summary["networks"][network_key] = network_summary
    
    return summary


if __name__ == "__main__":
    # Test JSON output functionality
    print("Testing JSON output functionality...")
    
    # Create sample data for testing
    sample_data = {
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
                "borrowable_in_isolation": True,
                "siloed_borrowing": False,
                "reserve_factor": 0.10,
                "liquidation_protocol_fee": 0.10,
                "debt_ceiling": 0,
                "emode_category": 1,
                "supply_cap": 1000000,
                "borrow_cap": 900000
            }
        ]
    }
    
    # Test JSON generation
    json_output = generate_json_output(sample_data)
    print("✅ JSON generation successful")
    
    # Test validation
    errors = validate_json_schema(sample_data)
    if errors:
        print(f"❌ Validation errors: {errors}")
    else:
        print("✅ JSON validation successful")
    
    # Test summary
    summary = create_json_summary(sample_data)
    print(f"✅ JSON summary: {summary}")
    
    print("JSON output functionality test completed!")