"""
HTML table generation for Aave V3 data.
Creates responsive HTML tables grouped by network with proper styling.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from networks import AAVE_V3_NETWORKS


def format_percentage(value: float) -> str:
    """
    Format decimal value as percentage.
    
    Args:
        value: Decimal value (0.78 = 78%)
        
    Returns:
        Formatted percentage string
    """
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return "0.00%"


def format_boolean(value: bool) -> str:
    """
    Format boolean value for display.
    
    Args:
        value: Boolean value
        
    Returns:
        Formatted string with emoji
    """
    if value:
        return "✅ Yes"
    return "❌ No"


def format_large_number(value: int) -> str:
    """
    Format large numbers with appropriate units.
    
    Args:
        value: Integer value
        
    Returns:
        Formatted string with units
    """
    if not isinstance(value, (int, float)) or value == 0:
        return "0"
    
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(int(value))


def format_address(address: str) -> str:
    """
    Format address for display with truncation.
    
    Args:
        address: Ethereum address
        
    Returns:
        Formatted address string
    """
    if not address or len(address) < 10:
        return address
    
    return f"{address[:6]}...{address[-4:]}"


def get_css_styles() -> str:
    """
    Get CSS styles for HTML table formatting.
    
    Returns:
        CSS style string
    """
    return """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header p {
            margin: 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .metadata {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .metadata-item {
            text-align: center;
        }
        
        .metadata-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        
        .metadata-label {
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .network-section {
            margin: 0;
            border-bottom: 1px solid #dee2e6;
        }
        
        .network-section:last-child {
            border-bottom: none;
        }
        
        .network-header {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            margin: 0;
            font-size: 1.3em;
            font-weight: 500;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .network-stats {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .table-container {
            overflow-x: auto;
            padding: 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 0.9em;
        }
        
        th {
            background: #f8f9fa;
            color: #495057;
            font-weight: 600;
            padding: 12px 8px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            white-space: nowrap;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 10px 8px;
            border-bottom: 1px solid #f1f3f4;
            vertical-align: middle;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .symbol-cell {
            font-weight: bold;
            color: #667eea;
            min-width: 80px;
        }
        
        .address-cell {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.8em;
            color: #6c757d;
            min-width: 120px;
        }
        
        .percentage-cell {
            text-align: right;
            font-weight: 500;
            min-width: 70px;
        }
        
        .boolean-cell {
            text-align: center;
            min-width: 60px;
        }
        
        .number-cell {
            text-align: right;
            font-weight: 500;
            min-width: 80px;
        }
        
        .status-active {
            color: #28a745;
        }
        
        .status-inactive {
            color: #dc3545;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .metadata {
                padding: 15px;
            }
            
            .metadata-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
            }
            
            .network-header {
                padding: 12px 20px;
                font-size: 1.1em;
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            table {
                font-size: 0.8em;
            }
            
            th, td {
                padding: 8px 6px;
            }
        }
        
        @media (max-width: 480px) {
            .metadata-grid {
                grid-template-columns: 1fr;
            }
            
            .network-header {
                padding: 10px 15px;
            }
            
            th, td {
                padding: 6px 4px;
            }
            
            .address-cell {
                font-size: 0.7em;
            }
        }
    </style>
    """


def create_table_headers() -> str:
    """
    Create HTML table headers.
    
    Returns:
        HTML string for table headers
    """
    headers = [
        "Symbol",
        "Asset Address", 
        "Liquidation Threshold",  # Changed from "LT" to full name
        "LTV", # Loan to Value
        "LB",  # Liquidation Bonus
        "Active",
        "Frozen",
        "Borrowing",
        "Stable Borrow",
        "Paused",
        "Isolation",
        "Reserve Factor",
        "Debt Ceiling",
        "eMode",
        "Supply Cap",
        "Borrow Cap"
    ]
    
    header_html = "<tr>\n"
    for header in headers:
        header_html += f"        <th>{header}</th>\n"
    header_html += "    </tr>"
    
    return header_html


def create_asset_row(asset: Dict[str, Any]) -> str:
    """
    Create HTML table row for a single asset.
    
    Args:
        asset: Asset data dictionary
        
    Returns:
        HTML string for table row
    """
    # Extract and format values
    symbol = asset.get('symbol', 'UNKNOWN')
    address = asset.get('asset_address', '')
    lt = format_percentage(asset.get('liquidation_threshold', 0))
    ltv = format_percentage(asset.get('loan_to_value', 0))
    lb = format_percentage(asset.get('liquidation_bonus', 0))
    active = format_boolean(asset.get('active', False))
    frozen = format_boolean(asset.get('frozen', False))
    borrowing = format_boolean(asset.get('borrowing_enabled', False))
    stable_borrow = format_boolean(asset.get('stable_borrowing_enabled', False))
    paused = format_boolean(asset.get('paused', False))
    isolation = format_boolean(asset.get('borrowable_in_isolation', False))
    reserve_factor = format_percentage(asset.get('reserve_factor', 0))
    debt_ceiling = format_large_number(asset.get('debt_ceiling', 0))
    emode = asset.get('emode_category', 0)
    supply_cap = format_large_number(asset.get('supply_cap', 0))
    borrow_cap = format_large_number(asset.get('borrow_cap', 0))
    
    # Create row HTML
    row_html = "    <tr>\n"
    row_html += f"        <td class=\"symbol-cell\">{symbol}</td>\n"
    row_html += f"        <td class=\"address-cell\">{format_address(address)}</td>\n"
    row_html += f"        <td class=\"percentage-cell\">{lt}</td>\n"
    row_html += f"        <td class=\"percentage-cell\">{ltv}</td>\n"
    row_html += f"        <td class=\"percentage-cell\">{lb}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{active}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{frozen}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{borrowing}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{stable_borrow}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{paused}</td>\n"
    row_html += f"        <td class=\"boolean-cell\">{isolation}</td>\n"
    row_html += f"        <td class=\"percentage-cell\">{reserve_factor}</td>\n"
    row_html += f"        <td class=\"number-cell\">{debt_ceiling}</td>\n"
    row_html += f"        <td class=\"number-cell\">{emode}</td>\n"
    row_html += f"        <td class=\"number-cell\">{supply_cap}</td>\n"
    row_html += f"        <td class=\"number-cell\">{borrow_cap}</td>\n"
    row_html += "    </tr>"
    
    return row_html


def create_network_table(network_key: str, assets: List[Dict[str, Any]]) -> str:
    """
    Create HTML table for a single network.
    
    Args:
        network_key: Network identifier
        assets: List of asset data
        
    Returns:
        HTML string for network table section
    """
    # Get network info
    network_config = AAVE_V3_NETWORKS.get(network_key, {})
    network_name = network_config.get('name', network_key.title())
    
    # Calculate network statistics
    total_assets = len(assets)
    active_assets = sum(1 for asset in assets if asset.get('active', False))
    borrowable_assets = sum(1 for asset in assets if asset.get('borrowing_enabled', False))
    
    # Sort assets by symbol
    sorted_assets = sorted(assets, key=lambda x: x.get('symbol', ''))
    
    # Create network section HTML
    html = f"""
<div class="network-section">
    <div class="network-header">
        <span>{network_name}</span>
        <span class="network-stats">{total_assets} assets • {active_assets} active • {borrowable_assets} borrowable</span>
    </div>
    <div class="table-container">
        <table>
            {create_table_headers()}
"""
    
    # Add asset rows
    for asset in sorted_assets:
        html += "\n" + create_asset_row(asset)
    
    html += """
        </table>
    </div>
</div>"""
    
    return html


def create_metadata_section(
    data: Dict[str, List[Dict]], 
    fetch_report: Optional[Dict] = None
) -> str:
    """
    Create metadata section for HTML output.
    
    Args:
        data: Network data dictionary
        fetch_report: Optional fetch report
        
    Returns:
        HTML string for metadata section
    """
    # Calculate statistics
    total_networks = len(data)
    total_assets = sum(len(assets) for assets in data.values())
    total_active = sum(
        sum(1 for asset in assets if asset.get('active', False))
        for assets in data.values()
    )
    
    # Get generation time
    now = datetime.now(timezone.utc)
    generation_time = now.strftime("%Y-%m-%d %H:%M UTC")
    
    # Create metadata HTML
    html = f"""
<div class="metadata">
    <div class="metadata-grid">
        <div class="metadata-item">
            <span class="metadata-value">{total_networks}</span>
            <span class="metadata-label">Networks</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-value">{total_assets}</span>
            <span class="metadata-label">Total Assets</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-value">{total_active}</span>
            <span class="metadata-label">Active Assets</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-value">{generation_time}</span>
            <span class="metadata-label">Last Updated</span>
        </div>
    </div>
</div>"""
    
    return html


def generate_html_output(
    data: Dict[str, List[Dict]], 
    fetch_report: Optional[Dict] = None,
    title: str = "Aave V3 Protocol Data"
) -> str:
    """
    Generate complete HTML output from Aave V3 data.
    
    Args:
        data: Network data dictionary
        fetch_report: Optional fetch report
        title: Page title
        
    Returns:
        Complete HTML string
    """
    # Sort networks by name for consistent display
    sorted_networks = sorted(
        data.items(), 
        key=lambda x: AAVE_V3_NETWORKS.get(x[0], {}).get('name', x[0])
    )
    
    # Create HTML structure
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {get_css_styles()}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Aave V3 Protocol Data</h1>
            <p>Real-time liquidation thresholds, LTV ratios, and protocol parameters across all supported networks</p>
        </div>
        
        {create_metadata_section(data, fetch_report)}
"""
    
    # Add network tables
    for network_key, assets in sorted_networks:
        if assets:  # Only include networks with data
            html += "\n" + create_network_table(network_key, assets)
    
    # Add footer
    now = datetime.now(timezone.utc)
    html += f"""
        
        <div class="footer">
            <p>
                Data automatically updated daily from on-chain sources • 
                Generated on {now.strftime("%Y-%m-%d at %H:%M UTC")} • 
                <a href="https://github.com/aave/aave-v3-core" target="_blank">Aave V3 Protocol</a>
            </p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def save_html_output(
    data: Dict[str, List[Dict]], 
    filepath: str,
    fetch_report: Optional[Dict] = None,
    title: str = "Aave V3 Protocol Data"
) -> bool:
    """
    Save HTML output to file.
    
    Args:
        data: Network data dictionary
        filepath: Output file path
        fetch_report: Optional fetch report
        title: Page title
        
    Returns:
        True if successful, False otherwise
    """
    try:
        html_content = generate_html_output(data, fetch_report, title)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML output saved to {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save HTML output: {e}")
        return False


def validate_html_structure(html_content: str) -> List[str]:
    """
    Validate HTML structure and content.
    
    Args:
        html_content: HTML string to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Basic HTML structure checks
    required_elements = [
        '<!DOCTYPE html>',
        '<html',
        '<head>',
        '<title>',
        '<body>',
        '</html>'
    ]
    
    for element in required_elements:
        if element not in html_content:
            errors.append(f"Missing required HTML element: {element}")
    
    # Check for CSS styles
    if '<style>' not in html_content:
        errors.append("Missing CSS styles")
    
    # Check for table structure
    if '<table>' not in html_content:
        errors.append("Missing table structure")
    
    if '<th>' not in html_content:
        errors.append("Missing table headers")
    
    # Check for responsive meta tag
    if 'viewport' not in html_content:
        errors.append("Missing responsive viewport meta tag")
    
    return errors


if __name__ == "__main__":
    # Test HTML output functionality
    print("Testing HTML output functionality...")
    
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
                "borrowable_in_isolation": False,
                "siloed_borrowing": False,
                "reserve_factor": 0.15,
                "liquidation_protocol_fee": 0.10,
                "debt_ceiling": 0,
                "emode_category": 1,
                "supply_cap": 50000,
                "borrow_cap": 40000
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
                "borrowable_in_isolation": True,
                "siloed_borrowing": False,
                "reserve_factor": 0.10,
                "liquidation_protocol_fee": 0.10,
                "debt_ceiling": 0,
                "emode_category": 1,
                "supply_cap": 2000000,
                "borrow_cap": 1800000
            }
        ]
    }
    
    # Test HTML generation
    html_output = generate_html_output(sample_data)
    print("✅ HTML generation successful")
    
    # Test validation
    errors = validate_html_structure(html_output)
    if errors:
        print(f"❌ Validation errors: {errors}")
    else:
        print("✅ HTML validation successful")
    
    # Test saving to file
    success = save_html_output(sample_data, "test_output.html")
    if success:
        print("✅ HTML file save successful")
    else:
        print("❌ HTML file save failed")
    
    print("HTML output functionality test completed!")