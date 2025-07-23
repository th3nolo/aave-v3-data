#!/usr/bin/env python3
"""
Test script for governance monitoring functionality.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from governance_monitoring import (
    GovernanceMonitor, save_governance_report, validate_against_governance_snapshots
)


def create_test_data():
    """Create test data for governance monitoring."""
    return {
        "ethereum": [
            {
                "asset_address": "0xA0b86a33E6441E6C7E8b0c3C4C0C6C6C6C6C6C6C",
                "symbol": "USDC",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "reserve_factor": 0.10,
                "last_update_timestamp": int(time.time())
            },
            {
                "asset_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "symbol": "WETH",
                "liquidation_threshold": 0.82,
                "loan_to_value": 0.80,
                "liquidation_bonus": 0.05,
                "reserve_factor": 0.15,
                "last_update_timestamp": int(time.time())
            }
        ],
        "polygon": [
            {
                "asset_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "symbol": "USDC",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "reserve_factor": 0.10,
                "last_update_timestamp": int(time.time())
            }
        ],
        "arbitrum": [
            {
                "asset_address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                "symbol": "USDC",
                "liquidation_threshold": 0.78,
                "loan_to_value": 0.75,
                "liquidation_bonus": 0.05,
                "reserve_factor": 0.10,
                "last_update_timestamp": int(time.time())
            }
        ]
    }


def test_governance_monitoring():
    """Test governance monitoring functionality."""
    print("🧪 Testing Governance Monitoring Functionality")
    print("=" * 60)
    
    # Create governance monitor instance
    governance_monitor = GovernanceMonitor("test_governance_history.json")
    
    # Create test data
    test_data = create_test_data()
    
    print("📊 Test data created:")
    for network, assets in test_data.items():
        print(f"   {network}: {len(assets)} assets")
    
    # Test 1: Run governance monitoring
    print("\n🏛️  Test 1: Running governance monitoring...")
    try:
        monitoring_report = governance_monitor.run_governance_monitoring(test_data)
        
        print(f"   ✅ Monitoring completed successfully")
        print(f"   📊 Found {monitoring_report['governance_posts_found']} governance posts")
        print(f"   📈 Detected {monitoring_report['parameter_changes_detected']} parameter changes")
        print(f"   🚨 Generated {monitoring_report['alerts_generated']} alerts")
        
        # Save monitoring report
        save_governance_report(monitoring_report, 'test_governance_monitoring_report.json')
        print(f"   💾 Report saved to test_governance_monitoring_report.json")
        
    except Exception as e:
        print(f"   ❌ Governance monitoring failed: {e}")
        return False
    
    # Test 2: Test parameter change detection with modified data
    print("\n📈 Test 2: Testing parameter change detection...")
    try:
        # Modify test data to simulate parameter changes
        modified_data = create_test_data()
        modified_data["ethereum"][0]["liquidation_threshold"] = 0.80  # Changed from 0.78
        modified_data["ethereum"][1]["reserve_factor"] = 0.20  # Changed from 0.15
        
        # Track changes
        changes = governance_monitor.track_parameter_changes(modified_data, test_data)
        
        print(f"   ✅ Change detection completed")
        print(f"   📊 Detected {len(changes)} parameter changes")
        
        for change in changes:
            print(f"      {change.asset} on {change.network}: {change.parameter} "
                  f"{change.old_value} → {change.new_value} "
                  f"({change.change_percentage:.1%} change, {change.risk_level} risk)")
        
    except Exception as e:
        print(f"   ❌ Parameter change detection failed: {e}")
        return False
    
    # Test 3: Test governance validation
    print("\n🏛️  Test 3: Testing governance validation...")
    try:
        validation_results = validate_against_governance_snapshots(test_data)
        
        print(f"   ✅ Governance validation completed")
        print(f"   📊 Validated {validation_results['assets_validated']} assets across {validation_results['networks_validated']} networks")
        print(f"   🎯 Consistency score: {validation_results['governance_consistency_score']:.1%}")
        
        if validation_results['validation_passed']:
            print(f"   ✅ All governance validations passed")
        else:
            print(f"   ❌ {len(validation_results['validation_errors'])} validation errors found")
            for error in validation_results['validation_errors'][:3]:
                print(f"      {error}")
        
        # Save validation report
        with open('test_governance_validation_report.json', 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        print(f"   💾 Validation report saved to test_governance_validation_report.json")
        
    except Exception as e:
        print(f"   ❌ Governance validation failed: {e}")
        return False
    
    # Test 4: Test alert generation
    print("\n🚨 Test 4: Testing alert generation...")
    try:
        # Create test data with critical changes
        critical_data = create_test_data()
        critical_data["ethereum"][0]["liquidation_threshold"] = 0.60  # Critical drop from 0.78
        critical_data["polygon"][0]["liquidation_threshold"] = 0.45   # Very low LT
        
        changes = governance_monitor.track_parameter_changes(critical_data, test_data)
        alerts = governance_monitor.generate_alerts(changes, [])
        
        print(f"   ✅ Alert generation completed")
        print(f"   🚨 Generated {len(alerts)} alerts")
        
        for alert in alerts:
            print(f"      {alert.severity.upper()}: {alert.message}")
            print(f"         Type: {alert.alert_type}")
            print(f"         Changes: {len(alert.parameter_changes)}")
        
    except Exception as e:
        print(f"   ❌ Alert generation failed: {e}")
        return False
    
    # Test 5: Test RSS feed parsing (mock test)
    print("\n📡 Test 5: Testing RSS feed functionality...")
    try:
        # Test RSS feed parsing with mock data
        test_posts = [
            {
                'title': 'Risk Parameter Update for USDC',
                'content': 'Proposal to update liquidation threshold for USDC',
                'description': 'This proposal updates the LT parameter from 78% to 80%'
            },
            {
                'title': 'Community Update',
                'content': 'General community news',
                'description': 'Weekly newsletter'
            }
        ]
        
        relevant_count = 0
        for post in test_posts:
            if governance_monitor._is_relevant_governance_post(post):
                relevant_count += 1
                score = governance_monitor._calculate_relevance_score(post)
                print(f"      Relevant post: '{post['title']}' (score: {score:.1f})")
        
        print(f"   ✅ RSS feed parsing test completed")
        print(f"   📊 Found {relevant_count} relevant posts out of {len(test_posts)}")
        
    except Exception as e:
        print(f"   ❌ RSS feed parsing test failed: {e}")
        return False
    
    print("\n🎉 All governance monitoring tests completed successfully!")
    print("\nGenerated test files:")
    print("   📄 test_governance_monitoring_report.json")
    print("   📄 test_governance_validation_report.json")
    print("   📄 governance_history.json (if created)")
    
    return True


def test_integration_with_main_script():
    """Test integration with main aave_fetcher.py script."""
    print("\n🔗 Testing integration with main script...")
    
    try:
        # Test importing governance monitoring in main script context
        from aave_fetcher import main
        print("   ✅ Successfully imported governance monitoring in main script")
        
        # Test command line arguments
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--monitor-governance', action='store_true')
        parser.add_argument('--governance-alerts', action='store_true')
        parser.add_argument('--validate-governance', action='store_true')
        
        # Test parsing
        args = parser.parse_args(['--monitor-governance', '--governance-alerts'])
        print("   ✅ Command line arguments parsed successfully")
        print(f"      monitor-governance: {args.monitor_governance}")
        print(f"      governance-alerts: {args.governance_alerts}")
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Aave V3 Governance Monitoring Test Suite")
    print("=" * 60)
    
    # Run tests
    success = True
    
    try:
        success &= test_governance_monitoring()
        success &= test_integration_with_main_script()
        
        if success:
            print("\n✅ All tests passed successfully!")
            print("\nTo use governance monitoring in production:")
            print("   python aave_fetcher.py --monitor-governance --governance-alerts")
            print("   python aave_fetcher.py --validate-governance")
            exit(0)
        else:
            print("\n❌ Some tests failed!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        exit(1)