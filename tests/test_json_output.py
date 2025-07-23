"""
Tests for JSON output functionality.
"""

import unittest
import json
import sys
import os
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from json_output import (
    format_asset_data_for_json,
    create_json_metadata,
    generate_json_output,
    validate_json_schema,
    create_json_summary,
    AaveDataJSONEncoder
)


class TestJSONOutput(unittest.TestCase):
    """Test cases for JSON output functionality."""
    
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
            'borrow_cap': 900000,
            'liquidity_index': 1.0234,
            'variable_borrow_index': 1.0456,
            'current_liquidity_rate': 0.0234,
            'current_variable_borrow_rate': 0.0456,
            'last_update_timestamp': 1704067200,
            'a_token_address': '0x1234567890123456789012345678901234567890',
            'variable_debt_token_address': '0x0987654321098765432109876543210987654321'
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
    
    def test_format_asset_data_for_json(self):
        """Test asset data formatting for JSON."""
        formatted = format_asset_data_for_json(self.sample_asset_data)
        
        # Test required fields are present
        self.assertIn('asset_address', formatted)
        self.assertIn('symbol', formatted)
        self.assertIn('liquidation_threshold', formatted)
        self.assertIn('loan_to_value', formatted)
        
        # Test data types
        self.assertIsInstance(formatted['asset_address'], str)
        self.assertIsInstance(formatted['symbol'], str)
        self.assertIsInstance(formatted['liquidation_threshold'], float)
        self.assertIsInstance(formatted['decimals'], int)
        self.assertIsInstance(formatted['active'], bool)
        
        # Test decimal precision
        self.assertEqual(formatted['liquidation_threshold'], 0.78)
        self.assertEqual(formatted['liquidity_index'], 1.0234)
        
        # Test supply/borrow caps
        self.assertEqual(formatted['supply_cap'], 1000000)
        self.assertEqual(formatted['borrow_cap'], 900000)
    
    def test_format_asset_data_missing_fields(self):
        """Test formatting with missing fields."""
        minimal_data = {
            'asset_address': '0x123',
            'symbol': 'TEST'
        }
        
        formatted = format_asset_data_for_json(minimal_data)
        
        # Test default values
        self.assertEqual(formatted['liquidation_threshold'], 0.0)
        self.assertEqual(formatted['decimals'], 0)
        self.assertEqual(formatted['active'], False)
        self.assertEqual(formatted['supply_cap'], 0)
    
    def test_create_json_metadata(self):
        """Test metadata creation."""
        metadata = create_json_metadata(self.sample_network_data)
        
        # Test required fields
        self.assertIn('generated_at', metadata)
        self.assertIn('generated_timestamp', metadata)
        self.assertIn('data_version', metadata)
        self.assertIn('schema_version', metadata)
        self.assertIn('network_summary', metadata)
        self.assertIn('data_freshness', metadata)
        self.assertIn('networks', metadata)
        
        # Test network summary
        network_summary = metadata['network_summary']
        self.assertEqual(network_summary['successful_networks'], 2)
        self.assertEqual(network_summary['total_assets'], 2)
        self.assertGreater(network_summary['success_rate'], 0)
        
        # Test networks list
        self.assertEqual(set(metadata['networks']), {'ethereum', 'polygon'})
    
    def test_create_json_metadata_with_fetch_report(self):
        """Test metadata creation with fetch report."""
        fetch_report = {
            'fetch_summary': {
                'duration_seconds': 45.2,
                'partial_failures': 1,
                'skipped_networks': 0
            },
            'health_summary': {
                'healthy_networks': 10,
                'unhealthy_networks': 2,
                'monitoring_enabled': True
            }
        }
        
        metadata = create_json_metadata(self.sample_network_data, fetch_report)
        
        # Test fetch statistics
        self.assertIn('fetch_statistics', metadata)
        fetch_stats = metadata['fetch_statistics']
        self.assertEqual(fetch_stats['duration_seconds'], 45.2)
        self.assertEqual(fetch_stats['partial_failures'], 1)
        
        # Test network health
        self.assertIn('network_health', metadata)
        health = metadata['network_health']
        self.assertEqual(health['healthy_networks'], 10)
        self.assertEqual(health['monitoring_enabled'], True)
    
    def test_generate_json_output(self):
        """Test JSON output generation."""
        json_output = generate_json_output(self.sample_network_data)
        
        # Test it's valid JSON
        parsed = json.loads(json_output)
        
        # Test structure
        self.assertIn('aave_v3_data', parsed)
        self.assertIn('metadata', parsed)
        
        # Test data content
        data = parsed['aave_v3_data']
        self.assertIn('ethereum', data)
        self.assertIn('polygon', data)
        
        # Test asset data
        eth_assets = data['ethereum']
        self.assertEqual(len(eth_assets), 1)
        self.assertEqual(eth_assets[0]['symbol'], 'USDC')
        self.assertEqual(eth_assets[0]['liquidation_threshold'], 0.78)
    
    def test_generate_json_output_without_metadata(self):
        """Test JSON output generation without metadata."""
        json_output = generate_json_output(self.sample_network_data, include_metadata=False)
        
        parsed = json.loads(json_output)
        
        # Test structure
        self.assertIn('aave_v3_data', parsed)
        self.assertNotIn('metadata', parsed)
    
    def test_validate_json_schema_valid(self):
        """Test JSON schema validation with valid data."""
        errors = validate_json_schema(self.sample_network_data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_json_schema_invalid_root(self):
        """Test JSON schema validation with invalid root type."""
        errors = validate_json_schema("not a dict")
        self.assertGreater(len(errors), 0)
        self.assertIn("Root data must be a dictionary", errors[0])
    
    def test_validate_json_schema_missing_fields(self):
        """Test JSON schema validation with missing required fields."""
        invalid_data = {
            'ethereum': [
                {
                    'symbol': 'USDC'
                    # Missing asset_address
                }
            ]
        }
        
        errors = validate_json_schema(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('missing required field: asset_address' in error for error in errors))
    
    def test_validate_json_schema_invalid_types(self):
        """Test JSON schema validation with invalid field types."""
        invalid_data = {
            'ethereum': [
                {
                    'asset_address': 123,  # Should be string
                    'symbol': 'USDC',
                    'liquidation_threshold': 'invalid'  # Should be numeric
                }
            ]
        }
        
        errors = validate_json_schema(invalid_data)
        self.assertGreater(len(errors), 0)
    
    def test_validate_json_schema_invalid_ranges(self):
        """Test JSON schema validation with values out of range."""
        invalid_data = {
            'ethereum': [
                {
                    'asset_address': '0x123',
                    'symbol': 'USDC',
                    'liquidation_threshold': 1.5  # Should be <= 1
                }
            ]
        }
        
        errors = validate_json_schema(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('must be between 0 and 1' in error for error in errors))
    
    def test_create_json_summary(self):
        """Test JSON summary creation."""
        summary = create_json_summary(self.sample_network_data)
        
        # Test summary structure
        self.assertIn('total_networks', summary)
        self.assertIn('total_assets', summary)
        self.assertIn('networks', summary)
        
        # Test summary values
        self.assertEqual(summary['total_networks'], 2)
        self.assertEqual(summary['total_assets'], 2)
        
        # Test network summaries
        self.assertIn('ethereum', summary['networks'])
        self.assertIn('polygon', summary['networks'])
        
        eth_summary = summary['networks']['ethereum']
        self.assertEqual(eth_summary['asset_count'], 1)
        self.assertEqual(eth_summary['active_assets'], 1)
        self.assertEqual(eth_summary['borrowable_assets'], 1)
        self.assertIn('USDC', eth_summary['symbols'])
    
    def test_aave_data_json_encoder(self):
        """Test custom JSON encoder."""
        encoder = AaveDataJSONEncoder()
        
        # Test encoding
        test_data = {'test': 123.456789}
        encoded = encoder.encode(test_data)
        
        # Should be valid JSON
        parsed = json.loads(encoded)
        self.assertEqual(parsed['test'], 123.456789)
    
    def test_json_output_sorting(self):
        """Test that JSON output is consistently sorted."""
        # Create data with multiple assets in random order
        test_data = {
            'ethereum': [
                {'asset_address': '0x3', 'symbol': 'WETH'},
                {'asset_address': '0x1', 'symbol': 'USDC'},
                {'asset_address': '0x2', 'symbol': 'DAI'}
            ]
        }
        
        json_output = generate_json_output(test_data)
        parsed = json.loads(json_output)
        
        # Assets should be sorted by symbol
        assets = parsed['aave_v3_data']['ethereum']
        symbols = [asset['symbol'] for asset in assets]
        self.assertEqual(symbols, ['DAI', 'USDC', 'WETH'])
    
    def test_json_output_precision(self):
        """Test decimal precision in JSON output."""
        test_data = {
            'ethereum': [
                {
                    'asset_address': '0x123',
                    'symbol': 'TEST',
                    'liquidation_threshold': 0.123456789,
                    'liquidity_index': 1.987654321
                }
            ]
        }
        
        json_output = generate_json_output(test_data)
        parsed = json.loads(json_output)
        
        asset = parsed['aave_v3_data']['ethereum'][0]
        
        # Should be rounded to 6 decimal places
        self.assertEqual(asset['liquidation_threshold'], 0.123457)
        self.assertEqual(asset['liquidity_index'], 1.987654)


if __name__ == '__main__':
    unittest.main()