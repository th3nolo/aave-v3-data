#!/usr/bin/env python3
"""
Tests for governance monitoring and parameter tracking functionality.
"""

import sys
import os
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from governance_monitoring import (
    GovernanceMonitor, ParameterChange, GovernanceAlert,
    save_governance_report, validate_against_governance_snapshots
)


class TestGovernanceMonitoring(unittest.TestCase):
    """Test governance monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.temp_dir, "test_governance_history.json")
        self.monitor = GovernanceMonitor(self.test_history_file)
        
        # Sample current data
        self.current_data = {
            "ethereum": [
                {
                    "asset_address": "0xA0b86a33E6441E6C7E8b0c3C4C0C6C6C6C6C6C6C",
                    "symbol": "USDC",
                    "liquidation_threshold": 0.78,
                    "loan_to_value": 0.75,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.10
                },
                {
                    "asset_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "symbol": "WETH",
                    "liquidation_threshold": 0.82,
                    "loan_to_value": 0.80,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.15
                }
            ],
            "polygon": [
                {
                    "asset_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                    "symbol": "USDC",
                    "liquidation_threshold": 0.78,
                    "loan_to_value": 0.75,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.10
                }
            ]
        }
        
        # Sample previous data with changes
        self.previous_data = {
            "ethereum": [
                {
                    "asset_address": "0xA0b86a33E6441E6C7E8b0c3C4C0C6C6C6C6C6C6C",
                    "symbol": "USDC",
                    "liquidation_threshold": 0.75,  # Changed from 0.75 to 0.78
                    "loan_to_value": 0.75,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.10
                },
                {
                    "asset_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "symbol": "WETH",
                    "liquidation_threshold": 0.82,
                    "loan_to_value": 0.80,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.10  # Changed from 0.10 to 0.15
                }
            ],
            "polygon": [
                {
                    "asset_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                    "symbol": "USDC",
                    "liquidation_threshold": 0.78,
                    "loan_to_value": 0.75,
                    "liquidation_bonus": 0.05,
                    "reserve_factor": 0.10
                }
            ]
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_governance_monitor_initialization(self):
        """Test GovernanceMonitor initialization."""
        self.assertIsInstance(self.monitor, GovernanceMonitor)
        self.assertEqual(self.monitor.historical_data_file, self.test_history_file)
        self.assertIsInstance(self.monitor.historical_data, dict)
        self.assertIn('parameter_history', self.monitor.historical_data)
        self.assertIn('governance_posts', self.monitor.historical_data)
    
    def test_parameter_change_tracking(self):
        """Test parameter change detection."""
        changes = self.monitor.track_parameter_changes(self.current_data, self.previous_data)
        
        # Should detect 2 changes: USDC LT and WETH reserve factor
        self.assertEqual(len(changes), 2)
        
        # Check USDC liquidation threshold change
        usdc_change = next((c for c in changes if c.asset == "USDC" and c.parameter == "liquidation_threshold"), None)
        self.assertIsNotNone(usdc_change)
        self.assertEqual(usdc_change.network, "ethereum")
        self.assertEqual(usdc_change.old_value, 0.75)
        self.assertEqual(usdc_change.new_value, 0.78)
        self.assertAlmostEqual(usdc_change.change_percentage, 0.04, places=2)  # 4% change
        
        # Check WETH reserve factor change
        weth_change = next((c for c in changes if c.asset == "WETH" and c.parameter == "reserve_factor"), None)
        self.assertIsNotNone(weth_change)
        self.assertEqual(weth_change.network, "ethereum")
        self.assertEqual(weth_change.old_value, 0.10)
        self.assertEqual(weth_change.new_value, 0.15)
        self.assertAlmostEqual(weth_change.change_percentage, 0.50, places=2)  # 50% change
    
    def test_risk_level_assessment(self):
        """Test risk level assessment for parameter changes."""
        # Test critical change (>10%)
        critical_risk = self.monitor._assess_risk_level("liquidation_threshold", 0.15, 0.70)
        self.assertEqual(critical_risk, "critical")
        
        # Test high risk change (5-10%)
        high_risk = self.monitor._assess_risk_level("liquidation_threshold", 0.08, 0.75)
        self.assertEqual(high_risk, "high")
        
        # Test medium risk change (2-5%)
        medium_risk = self.monitor._assess_risk_level("liquidation_threshold", 0.03, 0.78)
        self.assertEqual(medium_risk, "medium")
        
        # Test low risk change (<2%)
        low_risk = self.monitor._assess_risk_level("liquidation_threshold", 0.01, 0.78)
        self.assertEqual(low_risk, "low")
        
        # Test concerning absolute values
        low_value_risk = self.monitor._assess_risk_level("liquidation_threshold", 0.01, 0.45)  # Below 50%
        self.assertEqual(low_value_risk, "high")
    
    def test_alert_generation(self):
        """Test alert generation based on parameter changes."""
        # Create test parameter changes
        critical_change = ParameterChange(
            asset="USDC",
            network="ethereum",
            parameter="liquidation_threshold",
            old_value=0.80,
            new_value=0.65,  # 15% decrease - critical
            change_percentage=0.1875,
            timestamp=datetime.now(),
            risk_level="critical"
        )
        
        high_risk_change = ParameterChange(
            asset="WETH",
            network="ethereum",
            parameter="reserve_factor",
            old_value=0.10,
            new_value=0.18,  # 80% increase - high risk
            change_percentage=0.80,
            timestamp=datetime.now(),
            risk_level="high"
        )
        
        parameter_changes = [critical_change, high_risk_change]
        governance_posts = []
        
        alerts = self.monitor.generate_alerts(parameter_changes, governance_posts)
        
        # Should generate alerts for critical and high-risk changes
        self.assertGreaterEqual(len(alerts), 2)
        
        # Check for critical alert
        critical_alert = next((a for a in alerts if a.alert_type == "critical_parameter_change"), None)
        self.assertIsNotNone(critical_alert)
        self.assertEqual(critical_alert.severity, "critical")
        self.assertEqual(len(critical_alert.parameter_changes), 1)
        
        # Check for high-risk alert
        high_risk_alert = next((a for a in alerts if a.alert_type == "high_risk_parameter_change"), None)
        self.assertIsNotNone(high_risk_alert)
        self.assertEqual(high_risk_alert.severity, "high")
        self.assertEqual(len(high_risk_alert.parameter_changes), 1)
    
    def test_governance_post_relevance(self):
        """Test governance post relevance detection."""
        # Relevant post
        relevant_post = {
            'title': 'Risk Parameter Update for USDC',
            'content': 'Proposal to update liquidation threshold for USDC from 78% to 80%',
            'description': 'This proposal updates the LT parameter'
        }
        
        self.assertTrue(self.monitor._is_relevant_governance_post(relevant_post))
        
        # Irrelevant post
        irrelevant_post = {
            'title': 'Community Update',
            'content': 'General community news and updates',
            'description': 'Weekly community newsletter'
        }
        
        self.assertFalse(self.monitor._is_relevant_governance_post(irrelevant_post))
    
    def test_relevance_score_calculation(self):
        """Test relevance score calculation for governance posts."""
        high_relevance_post = {
            'title': 'Risk Parameter Update - Liquidation Threshold Changes',
            'content': 'Proposal to update liquidation threshold and loan-to-value ratios',
            'description': 'Critical parameter update affecting multiple assets'
        }
        
        score = self.monitor._calculate_relevance_score(high_relevance_post)
        self.assertGreater(score, 5.0)  # Should have high relevance score
        
        low_relevance_post = {
            'title': 'General Discussion',
            'content': 'Community discussion about future plans',
            'description': 'General community post'
        }
        
        score = self.monitor._calculate_relevance_score(low_relevance_post)
        self.assertEqual(score, 0.0)  # Should have no relevance
    
    @patch('governance_monitoring.urlopen')
    def test_rss_feed_fetching(self, mock_urlopen):
        """Test RSS feed fetching and parsing."""
        # Mock RSS response
        rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Aave Governance</title>
                <item>
                    <title>Risk Parameter Update for USDC</title>
                    <link>https://governance.aave.com/t/risk-parameter-update/123</link>
                    <description>Proposal to update liquidation threshold</description>
                    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>'''
        
        mock_response = MagicMock()
        mock_response.read.return_value = rss_content.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        posts = self.monitor.fetch_rss_feed("https://test.com/feed.rss")
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['title'], 'Risk Parameter Update for USDC')
        self.assertEqual(posts[0]['link'], 'https://governance.aave.com/t/risk-parameter-update/123')
    
    def test_historical_data_management(self):
        """Test historical data loading and saving."""
        # Test saving historical data
        test_data = {
            "parameter_history": self.current_data,
            "governance_posts": [],
            "last_update": datetime.now().isoformat()
        }
        
        self.monitor.historical_data = test_data
        self.monitor._save_historical_data()
        
        # Test loading historical data
        new_monitor = GovernanceMonitor(self.test_history_file)
        self.assertEqual(new_monitor.historical_data["parameter_history"], self.current_data)
    
    def test_governance_validation(self):
        """Test validation against governance snapshots."""
        # Create test governance history
        governance_history = {
            "parameter_changes": [
                {
                    "asset": "USDC",
                    "network": "ethereum",
                    "parameter": "liquidation_threshold",
                    "old_value": 0.75,
                    "new_value": 0.78,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        # Save test governance history
        with open(self.test_history_file, 'w') as f:
            json.dump(governance_history, f)
        
        # Run validation
        validation_results = validate_against_governance_snapshots(
            self.current_data, 
            self.test_history_file
        )
        
        self.assertTrue(validation_results['validation_passed'])
        self.assertEqual(validation_results['networks_validated'], 2)
        self.assertEqual(validation_results['assets_validated'], 3)
        self.assertEqual(validation_results['governance_consistency_score'], 1.0)
    
    def test_complete_monitoring_workflow(self):
        """Test complete governance monitoring workflow."""
        with patch.object(self.monitor, 'monitor_governance_feeds') as mock_feeds:
            # Mock governance posts
            mock_feeds.return_value = [
                {
                    'title': 'Risk Parameter Update',
                    'content': 'Liquidation threshold update',
                    'relevance_score': 6.0,
                    'feed_source': 'aave_governance'
                }
            ]
            
            # Run monitoring
            report = self.monitor.run_governance_monitoring(self.current_data)
            
            # Verify report structure
            self.assertIn('timestamp', report)
            self.assertIn('governance_posts_found', report)
            self.assertIn('parameter_changes_detected', report)
            self.assertIn('alerts_generated', report)
            self.assertIn('summary', report)
            
            # Verify monitoring was executed
            self.assertEqual(report['governance_posts_found'], 1)
            self.assertIsInstance(report['parameter_changes'], list)
            self.assertIsInstance(report['alerts'], list)
    
    def test_save_governance_report(self):
        """Test saving governance monitoring report."""
        test_report = {
            'timestamp': datetime.now().isoformat(),
            'governance_posts_found': 5,
            'parameter_changes_detected': 2,
            'alerts_generated': 1
        }
        
        report_file = os.path.join(self.temp_dir, "test_governance_report.json")
        save_governance_report(test_report, report_file)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(report_file))
        
        with open(report_file, 'r') as f:
            loaded_report = json.load(f)
        
        self.assertEqual(loaded_report['governance_posts_found'], 5)
        self.assertEqual(loaded_report['parameter_changes_detected'], 2)
        self.assertEqual(loaded_report['alerts_generated'], 1)


if __name__ == '__main__':
    unittest.main()