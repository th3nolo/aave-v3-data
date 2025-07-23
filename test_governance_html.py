#!/usr/bin/env python3
"""
Test script for governance HTML output generation.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from governance_html_output import save_governance_html_output


def create_test_governance_report():
    """Create a test governance monitoring report."""
    return {
        'timestamp': datetime.now().isoformat(),
        'governance_posts_found': 15,
        'parameter_changes_detected': 3,
        'alerts_generated': 2,
        'governance_posts': [
            {
                'title': 'Risk Parameter Update for USDC on Ethereum',
                'link': 'https://governance.aave.com/t/risk-parameter-update-usdc/123',
                'description': 'Proposal to update liquidation threshold for USDC from 78% to 80% to improve protocol safety.',
                'pub_date': '2025-01-20T10:00:00Z',
                'feed_source': 'aave_governance',
                'relevance_score': 8.5
            },
            {
                'title': 'Quarterly Risk Assessment - Q1 2025',
                'link': 'https://governance.aave.com/t/quarterly-risk-assessment/124',
                'description': 'Comprehensive risk assessment covering all major assets across networks.',
                'pub_date': '2025-01-19T15:30:00Z',
                'feed_source': 'risk_updates',
                'relevance_score': 7.2
            },
            {
                'title': 'New Asset Listing: wstETH on Base',
                'link': 'https://governance.aave.com/t/new-asset-listing-wsteth/125',
                'description': 'Proposal to add wstETH as collateral on Base network with initial risk parameters.',
                'pub_date': '2025-01-18T09:15:00Z',
                'feed_source': 'aave_governance',
                'relevance_score': 6.8
            }
        ],
        'parameter_changes': [
            {
                'asset': 'USDC',
                'network': 'ethereum',
                'parameter': 'liquidation_threshold',
                'old_value': 0.78,
                'new_value': 0.80,
                'change_percentage': 0.026,
                'risk_level': 'medium'
            },
            {
                'asset': 'WETH',
                'network': 'polygon',
                'parameter': 'reserve_factor',
                'old_value': 0.15,
                'new_value': 0.20,
                'change_percentage': 0.333,
                'risk_level': 'critical'
            },
            {
                'asset': 'WBTC',
                'network': 'arbitrum',
                'parameter': 'loan_to_value',
                'old_value': 0.70,
                'new_value': 0.68,
                'change_percentage': 0.029,
                'risk_level': 'medium'
            }
        ],
        'alerts': [
            {
                'alert_type': 'critical_parameter_change',
                'message': 'CRITICAL: 1 critical parameter changes detected',
                'severity': 'critical',
                'parameter_changes_count': 1
            },
            {
                'alert_type': 'high_relevance_governance_activity',
                'message': 'INFO: 2 high-relevance governance posts detected',
                'severity': 'low',
                'parameter_changes_count': 0
            }
        ],
        'summary': {
            'critical_changes': 1,
            'high_risk_changes': 0,
            'medium_risk_changes': 2,
            'low_risk_changes': 0,
            'critical_alerts': 1,
            'high_severity_alerts': 0
        }
    }


def create_test_validation_report():
    """Create a test governance validation report."""
    return {
        'timestamp': datetime.now().isoformat(),
        'validation_passed': True,
        'validation_errors': [],
        'validation_warnings': [
            'Minor discrepancy in USDC reserve factor on Polygon (expected 0.10, found 0.101)'
        ],
        'governance_consistency_score': 0.95,
        'networks_validated': 5,
        'assets_validated': 45
    }


def test_governance_html_generation():
    """Test governance HTML generation."""
    print("🧪 Testing Governance HTML Generation")
    print("=" * 50)
    
    # Create test data
    governance_report = create_test_governance_report()
    validation_report = create_test_validation_report()
    
    print("📊 Test data created:")
    print(f"   Governance posts: {governance_report['governance_posts_found']}")
    print(f"   Parameter changes: {governance_report['parameter_changes_detected']}")
    print(f"   Alerts: {governance_report['alerts_generated']}")
    print(f"   Validation score: {validation_report['governance_consistency_score']:.1%}")
    
    # Generate HTML
    print("\n📄 Generating HTML output...")
    try:
        success = save_governance_html_output(
            governance_report,
            validation_report,
            'test_governance_monitoring.html'
        )
        
        if success:
            print("✅ HTML generation successful!")
            print("   📄 File: test_governance_monitoring.html")
            
            # Check file size
            file_size = os.path.getsize('test_governance_monitoring.html')
            print(f"   📏 File size: {file_size:,} bytes")
            
            # Verify HTML structure
            with open('test_governance_monitoring.html', 'r') as f:
                content = f.read()
                
            print("   🔍 HTML validation:")
            print(f"      Contains DOCTYPE: {'<!DOCTYPE html>' in content}")
            print(f"      Contains title: {'Aave V3 Governance Monitoring' in content}")
            print(f"      Contains summary section: {'📊 Summary' in content}")
            print(f"      Contains alerts section: {'🚨 Alerts' in content}")
            print(f"      Contains parameter changes: {'📈 Parameter Changes' in content}")
            print(f"      Contains governance posts: {'🏛️ Recent Governance Activity' in content}")
            print(f"      Contains validation section: {'🔍 Governance Validation' in content}")
            
            return True
            
        else:
            print("❌ HTML generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ HTML generation error: {e}")
        return False


def test_html_content_accuracy():
    """Test HTML content accuracy."""
    print("\n🔍 Testing HTML Content Accuracy")
    print("-" * 40)
    
    governance_report = create_test_governance_report()
    validation_report = create_test_validation_report()
    
    # Generate HTML
    save_governance_html_output(
        governance_report,
        validation_report,
        'test_content_accuracy.html'
    )
    
    # Read and verify content
    with open('test_content_accuracy.html', 'r') as f:
        content = f.read()
    
    # Check specific content
    checks = [
        ('USDC parameter change', 'USDC' in content and ('liquidation_threshold' in content or 'Liquidation Threshold' in content)),
        ('Critical alert', 'CRITICAL: 1 critical parameter changes detected' in content),
        ('Governance post title', 'Risk Parameter Update for USDC on Ethereum' in content),
        ('Validation score', '95.0%' in content or '95%' in content),
        ('Networks validated', '5' in content),
        ('Assets validated', '45' in content)
    ]
    
    passed_checks = 0
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if check_result:
            passed_checks += 1
    
    print(f"\n   📊 Content accuracy: {passed_checks}/{len(checks)} checks passed")
    
    return passed_checks == len(checks)


if __name__ == "__main__":
    print("🚀 Governance HTML Output Test Suite")
    print("=" * 50)
    
    success = True
    
    try:
        success &= test_governance_html_generation()
        success &= test_html_content_accuracy()
        
        if success:
            print("\n✅ All HTML generation tests passed!")
            print("\nGenerated test files:")
            print("   📄 test_governance_monitoring.html")
            print("   📄 test_content_accuracy.html")
            print("\nTo view the HTML output:")
            print("   Open test_governance_monitoring.html in your browser")
            exit(0)
        else:
            print("\n❌ Some HTML generation tests failed!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        exit(1)