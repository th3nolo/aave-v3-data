#!/usr/bin/env python3
"""
Test script to generate and view HTML output from html_output.py
"""

import sys
import os
import webbrowser
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from html_output import generate_html_output, save_html_output

# Create comprehensive test data with multiple networks and assets
test_data = {
    "ethereum": [
        {
            "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
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
        },
        {
            "asset_address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "symbol": "DAI",
            "liquidation_threshold": 0.77,
            "loan_to_value": 0.75,
            "liquidation_bonus": 0.05,
            "decimals": 18,
            "active": True,
            "frozen": False,
            "borrowing_enabled": True,
            "stable_borrowing_enabled": True,
            "paused": False,
            "borrowable_in_isolation": True,
            "siloed_borrowing": False,
            "reserve_factor": 0.10,
            "liquidation_protocol_fee": 0.10,
            "debt_ceiling": 5000000,
            "emode_category": 1,
            "supply_cap": 2000000,
            "borrow_cap": 1800000
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
        },
        {
            "asset_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
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
            "supply_cap": 10000,
            "borrow_cap": 8000
        }
    ],
    "arbitrum": [
        {
            "asset_address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
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
            "supply_cap": 1500000,
            "borrow_cap": 1200000
        },
        {
            "asset_address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "symbol": "WETH",
            "liquidation_threshold": 0.825,
            "loan_to_value": 0.80,
            "liquidation_bonus": 0.05,
            "decimals": 18,
            "active": True,
            "frozen": True,  # Example of a frozen asset
            "borrowing_enabled": False,
            "stable_borrowing_enabled": False,
            "paused": False,
            "borrowable_in_isolation": False,
            "siloed_borrowing": False,
            "reserve_factor": 0.15,
            "liquidation_protocol_fee": 0.10,
            "debt_ceiling": 0,
            "emode_category": 1,
            "supply_cap": 15000,
            "borrow_cap": 12000
        }
    ]
}

def main():
    """Generate HTML output and optionally open in browser"""
    
    print("🚀 Generating Aave V3 HTML output...")
    
    # Generate HTML content
    html_content = generate_html_output(test_data)
    
    # Save to file
    output_file = "aave_v3_test_output.html"
    success = save_html_output(test_data, output_file)
    
    if success:
        print(f"✅ HTML file successfully generated: {output_file}")
        
        # Get absolute path for the file
        abs_path = os.path.abspath(output_file)
        print(f"📂 File location: {abs_path}")
        
        # Ask if user wants to open in browser
        try:
            response = input("\n🌐 Would you like to open the HTML file in your browser? (y/n): ").strip().lower()
            if response == 'y':
                webbrowser.open(f'file://{abs_path}')
                print("✅ Opening in browser...")
            else:
                print(f"👍 You can manually open the file at: file://{abs_path}")
        except:
            print(f"👍 You can manually open the file at: file://{abs_path}")
            
        # Print some stats about the generated HTML
        print("\n📊 HTML Output Statistics:")
        print(f"   - Networks: {len(test_data)}")
        print(f"   - Total Assets: {sum(len(assets) for assets in test_data.values())}")
        print(f"   - File Size: {os.path.getsize(output_file) / 1024:.2f} KB")
        
    else:
        print("❌ Failed to generate HTML output")

if __name__ == "__main__":
    main()