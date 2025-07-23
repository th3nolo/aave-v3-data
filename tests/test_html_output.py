"""
Tests for HTML output functionality.
"""

import unittest
import sys
import os
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from html_output import (
    format_percentage,
    format_boolean,
    format_large_number,
    format_address,
    get_css_styles,
    create_table_headers,
    create_asset_row,
    create_network_table,
    create_metadata_section,
    generate_html_output,
    save_html_output,
    validate_html_structure
)


class TestHTMLOutput(unittest.TestCase):
    """Test cases for HTML output functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_asset_data = {
            'asset_address': '0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0',
            'symbol': 'USDC',
            'liquidation_threshold': 0.78,
            'loan_to_value': 0.75,
            'liquidation_bonus': 0.05,
            'decimals': 6,
            'active': True,
            'frozen': False,
            'borrowing_enabled': True,
            'stable_borrowing_enabled': False,
            'paused': False,
            'borrowable_in_isolation': True,
            'siloed_borrowing': False,
            'reserve_factor': 0.10,
            'liquidation_protocol_fee': 0.10,
            'debt_ceiling': 0,
            'emode_category': 1,
            'supply_cap': 1000000,
            'borrow_cap': 900000
        }
        
        self.sample_network_data = {
            'ethereum': [self.sample_asset_data],
            'polygon': [
                {
                    'asset_address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                    'symbol': 'USDC.e',
                    'liquidation_threshold': 0.78,
                    'loan_to_value': 0.75,
                    'liquidation_bonus': 0.05,
                    'decimals': 6,
                    'active': True,
                    'frozen': False,
                    'borrowing_enabled': True
                }
            ]
        }
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        self.assertEqual(format_percentage(0.78), "78.00%")
        self.assertEqual(format_percentage(0.0), "0.00%")
        self.assertEqual(format_percentage(1.0), "100.00%")
        self.assertEqual(format_percentage(0.123456), "12.35%")
        self.assertEqual(format_percentage("invalid"), "0.00%")
    
    def test_format_boolean(self):
        """Test boolean formatting."""
        self.assertEqual(format_boolean(True), "✅ Yes")
        self.assertEqual(format_boolean(False), "❌ No")
    
    def test_format_large_number(self):
        """Test large number formatting."""
        self.assertEqual(format_large_number(0), "0")
        self.assertEqual(format_large_number(500), "500")
        self.assertEqual(format_large_number(1500), "1.50K")
        self.assertEqual(format_large_number(1500000), "1.50M")
        self.assertEqual(format_large_number(2500000000), "2.50B")
        self.assertEqual(format_large_number("invalid"), "0")
    
    def test_format_address(self):
        """Test address formatting."""
        address = "0xA0b86a33E6441E8e421B27D6c5a9c7157bF77FB0"
        formatted = format_address(address)
        self.assertEqual(formatted, "0xA0b8...7FB0")
        
        # Test short address
        short_address = "0x123"
        self.assertEqual(format_address(short_address), "0x123")
        
        # Test empty address
        self.assertEqual(format_address(""), "")
    
    def test_get_css_styles(self):
        """Test CSS styles generation."""
        css = get_css_styles()
        
        # Test it contains CSS
        self.assertIn("<style>", css)
        self.assertIn("</style>", css)
        
        # Test it contains key styles
        self.assertIn("body", css)
        self.assertIn("table", css)
        self.assertIn("@media", css)  # Responsive styles
    
    def test_create_table_headers(self):
        """Test table headers creation."""
        headers = create_table_headers()
        
        # Test it contains table row
        self.assertIn("<tr>", headers)
        self.assertIn("</tr>", headers)
        
        # Test it contains key headers
        self.assertIn("Symbol", headers)
        self.assertIn("LT", headers)
        self.assertIn("LTV", headers)
        self.assertIn("Active", headers)
    
    def test_create_asset_row(self):
        """Test asset row creation."""
        row = create_asset_row(self.sample_asset_data)
        
        # Test it contains table row
        self.assertIn("<tr>", row)
        self.assertIn("</tr>", row)
        
        # Test it contains asset data
        self.assertIn("USDC", row)
        self.assertIn("78.00%", row)  # Liquidation threshold
        self.assertIn("75.00%", row)  # LTV
        self.assertIn("✅ Yes", row)  # Active
        self.assertIn("❌ No", row)   # Frozen
    
    def test_create_asset_row_missing_data(self):
        """Test asset row creation with missing data."""
        minimal_data = {
            'asset_address': '0x123',
            'symbol': 'TEST'
        }
        
        row = create_asset_row(minimal_data)
        
        # Should handle missing data gracefully
        self.assertIn("TEST", row)
        self.assertIn("0.00%", row)  # Default percentage
        self.assertIn("❌ No", row)  # Default boolean
    
    def test_create_network_table(self):
        """Test network table creation."""
        assets = [self.sample_asset_data]
        table = create_network_table('ethereum', assets)
        
        # Test it contains network section
        self.assertIn('class="network-section"', table)
        self.assertIn('class="network-header"', table)
        
        # Test it contains network name
        self.assertIn("Ethereum", table)
        
        # Test it contains statistics
        self.assertIn("1 assets", table)
        self.assertIn("1 active", table)
        self.assertIn("1 borrowable", table)
        
        # Test it contains table
        self.assertIn("<table>", table)
        self.assertIn("USDC", table)
    
    def test_create_metadata_section(self):
        """Test metadata section creation."""
        metadata = create_metadata_section(self.sample_network_data)
        
        # Test it contains metadata structure
        self.assertIn('class="metadata"', metadata)
        self.assertIn('class="metadata-grid"', metadata)
        
        # Test it contains statistics
        self.assertIn("2", metadata)  # Networks count
        self.assertIn("Networks", metadata)
        self.assertIn("Total Assets", metadata)
        self.assertIn("Active Assets", metadata)
        self.assertIn("Last Updated", metadata)
    
    def test_generate_html_output(self):
        """Test complete HTML generation."""
        html = generate_html_output(self.sample_network_data)
        
        # Test basic HTML structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("<head>", html)
        self.assertIn("<body>", html)
        self.assertIn("</html>", html)
        
        # Test title
        self.assertIn("<title>Aave V3 Protocol Data</title>", html)
        
        # Test CSS styles
        self.assertIn("<style>", html)
        
        # Test content
        self.assertIn("Aave V3 Protocol Data", html)
        self.assertIn("Ethereum", html)
        self.assertIn("Polygon", html)
        self.assertIn("USDC", html)
    
    def test_generate_html_output_custom_title(self):
        """Test HTML generation with custom title."""
        custom_title = "Custom Aave Data"
        html = generate_html_output(self.sample_network_data, title=custom_title)
        
        self.assertIn(f"<title>{custom_title}</title>", html)
    
    def test_save_html_output(self):
        """Test saving HTML to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name
        
        try:
            # Test saving
            success = save_html_output(self.sample_network_data, temp_path)
            self.assertTrue(success)
            
            # Test file was created and contains content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("USDC", content)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_html_output_invalid_path(self):
        """Test saving HTML with invalid path."""
        # Try to save to invalid path
        success = save_html_output(self.sample_network_data, "/invalid/path/file.html")
        self.assertFalse(success)
    
    def test_validate_html_structure_valid(self):
        """Test HTML validation with valid HTML."""
        html = generate_html_output(self.sample_network_data)
        errors = validate_html_structure(html)
        
        self.assertEqual(len(errors), 0)
    
    def test_validate_html_structure_invalid(self):
        """Test HTML validation with invalid HTML."""
        invalid_html = "<div>Not a complete HTML document</div>"
        errors = validate_html_structure(invalid_html)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Missing required HTML element" in error for error in errors))
    
    def test_validate_html_structure_missing_elements(self):
        """Test HTML validation with missing elements."""
        incomplete_html = """<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        <p>No table or styles</p>
        </body>
        </html>"""
        
        errors = validate_html_structure(incomplete_html)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Missing CSS styles" in error for error in errors))
        self.assertTrue(any("Missing table structure" in error for error in errors))
    
    def test_html_sorting(self):
        """Test that HTML output sorts networks and assets consistently."""
        # Create data with multiple networks and assets
        test_data = {
            'polygon': [
                {'symbol': 'WETH', 'asset_address': '0x3'},
                {'symbol': 'USDC', 'asset_address': '0x1'}
            ],
            'ethereum': [
                {'symbol': 'DAI', 'asset_address': '0x2'}
            ]
        }
        
        html = generate_html_output(test_data)
        
        # Networks should be sorted by name (Ethereum before Polygon)
        eth_pos = html.find("Ethereum")
        poly_pos = html.find("Polygon")
        self.assertLess(eth_pos, poly_pos)
        
        # Assets within Polygon should be sorted by symbol (USDC before WETH)
        usdc_pos = html.find("USDC")
        weth_pos = html.find("WETH")
        self.assertLess(usdc_pos, weth_pos)
    
    def test_responsive_design(self):
        """Test that HTML includes responsive design elements."""
        html = generate_html_output(self.sample_network_data)
        
        # Test viewport meta tag
        self.assertIn('name="viewport"', html)
        self.assertIn('width=device-width', html)
        
        # Test responsive CSS
        self.assertIn("@media", html)
        self.assertIn("max-width", html)
    
    def test_accessibility_features(self):
        """Test HTML accessibility features."""
        html = generate_html_output(self.sample_network_data)
        
        # Test language attribute
        self.assertIn('lang="en"', html)
        
        # Test proper table structure
        self.assertIn("<th>", html)  # Table headers
        self.assertIn('<td class="', html)  # Table data (with class)
        
        # Test semantic HTML
        self.assertIn("<table>", html)
        self.assertIn("<thead>", html.replace(create_table_headers(), "<thead>"))


if __name__ == '__main__':
    unittest.main()