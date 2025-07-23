"""
Governance monitoring and parameter tracking for Aave V3 protocol.
Monitors RSS feeds, tracks parameter changes, and provides alerts for critical updates.
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
import re
import os


class ParameterChange(NamedTuple):
    """Represents a parameter change detected in governance."""
    asset: str
    network: str
    parameter: str
    old_value: float
    new_value: float
    change_percentage: float
    timestamp: datetime
    proposal_id: Optional[str] = None
    proposal_title: Optional[str] = None
    risk_level: str = "medium"


class GovernanceAlert(NamedTuple):
    """Represents an alert for critical parameter changes."""
    alert_type: str
    message: str
    parameter_changes: List[ParameterChange]
    timestamp: datetime
    severity: str  # "low", "medium", "high", "critical"


class GovernanceMonitor:
    """Monitor Aave governance for parameter changes and critical updates."""
    
    def __init__(self, historical_data_file: str = "governance_history.json"):
        self.historical_data_file = historical_data_file
        self.historical_data = self._load_historical_data()
        
        # RSS feeds to monitor
        self.rss_feeds = {
            "aave_governance": "https://governance.aave.com/latest.rss",
            "aave_forum": "https://governance.aave.com/c/governance/5.rss",
            "risk_updates": "https://governance.aave.com/c/risk/6.rss"
        }
        
        # Critical parameter thresholds for alerts
        self.critical_thresholds = {
            "liquidation_threshold": {
                "major_change": 0.05,  # 5% change is major
                "critical_change": 0.10,  # 10% change is critical
                "min_value": 0.50,  # Below 50% LT is concerning
                "max_value": 0.95   # Above 95% LT is unusual
            },
            "loan_to_value": {
                "major_change": 0.05,
                "critical_change": 0.10,
                "min_value": 0.40,
                "max_value": 0.90
            },
            "liquidation_bonus": {
                "major_change": 0.02,  # 2% change in liquidation bonus
                "critical_change": 0.05,
                "min_value": 0.01,
                "max_value": 0.20
            },
            "reserve_factor": {
                "major_change": 0.05,
                "critical_change": 0.10,
                "min_value": 0.00,
                "max_value": 0.50
            }
        }
        
        # Keywords to look for in governance posts
        self.governance_keywords = [
            "liquidation threshold", "LT", "loan-to-value", "LTV",
            "liquidation bonus", "reserve factor", "risk parameter",
            "parameter update", "risk assessment", "collateral",
            "borrow cap", "supply cap", "debt ceiling"
        ]
    
    def _load_historical_data(self) -> Dict[str, Any]:
        """Load historical parameter data from file."""
        if os.path.exists(self.historical_data_file):
            try:
                with open(self.historical_data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not load historical data: {e}")
        
        return {
            "parameter_history": {},
            "governance_posts": [],
            "last_update": None,
            "alerts_generated": []
        }
    
    def _save_historical_data(self):
        """Save historical parameter data to file."""
        try:
            with open(self.historical_data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2, default=str)
        except IOError as e:
            print(f"⚠️  Warning: Could not save historical data: {e}")
    
    def fetch_rss_feed(self, feed_url: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch and parse RSS feed for governance updates.
        
        Args:
            feed_url: URL of the RSS feed
            timeout: Request timeout in seconds
            
        Returns:
            List of parsed RSS items
        """
        try:
            headers = {
                'User-Agent': 'Aave-V3-Data-Fetcher/1.0 (Governance Monitor)'
            }
            request = Request(feed_url, headers=headers)
            
            with urlopen(request, timeout=timeout) as response:
                content = response.read().decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(content)
            items = []
            
            # Handle both RSS 2.0 and Atom feeds
            if root.tag == 'rss':
                # RSS 2.0 format
                for item in root.findall('.//item'):
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'description': description.text if description is not None else '',
                        'pub_date': pub_date.text if pub_date is not None else '',
                        'content': description.text if description is not None else ''
                    })
            else:
                # Atom format
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in root.findall('.//atom:entry', namespace):
                    title = entry.find('atom:title', namespace)
                    link = entry.find('atom:link', namespace)
                    content = entry.find('atom:content', namespace)
                    updated = entry.find('atom:updated', namespace)
                    
                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.get('href') if link is not None else '',
                        'description': content.text if content is not None else '',
                        'pub_date': updated.text if updated is not None else '',
                        'content': content.text if content is not None else ''
                    })
            
            return items
            
        except (URLError, HTTPError, ET.ParseError) as e:
            print(f"⚠️  Warning: Could not fetch RSS feed {feed_url}: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Warning: Unexpected error fetching RSS feed {feed_url}: {e}")
            return []
    
    def monitor_governance_feeds(self) -> List[Dict[str, Any]]:
        """
        Monitor all configured RSS feeds for governance updates.
        
        Returns:
            List of relevant governance posts
        """
        all_posts = []
        
        for feed_name, feed_url in self.rss_feeds.items():
            print(f"🔍 Monitoring {feed_name} feed...")
            
            try:
                posts = self.fetch_rss_feed(feed_url)
                
                # Filter for relevant posts
                relevant_posts = []
                for post in posts:
                    if self._is_relevant_governance_post(post):
                        post['feed_source'] = feed_name
                        post['relevance_score'] = self._calculate_relevance_score(post)
                        relevant_posts.append(post)
                
                all_posts.extend(relevant_posts)
                print(f"   Found {len(relevant_posts)} relevant posts from {feed_name}")
                
            except Exception as e:
                print(f"❌ Error monitoring {feed_name}: {e}")
                continue
        
        # Sort by relevance score and recency
        all_posts.sort(key=lambda x: (x.get('relevance_score', 0), x.get('pub_date', '')), reverse=True)
        
        return all_posts
    
    def _is_relevant_governance_post(self, post: Dict[str, Any]) -> bool:
        """Check if a governance post is relevant to parameter monitoring."""
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        description = post.get('description', '').lower()
        
        full_text = f"{title} {content} {description}"
        
        # Check for governance keywords
        for keyword in self.governance_keywords:
            if keyword.lower() in full_text:
                return True
        
        # Check for specific patterns
        patterns = [
            r'risk\s+parameter',
            r'liquidation\s+threshold',
            r'loan.to.value',
            r'ltv\s+ratio',
            r'collateral\s+factor',
            r'borrow\s+cap',
            r'supply\s+cap',
            r'debt\s+ceiling',
            r'reserve\s+factor'
        ]
        
        for pattern in patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_relevance_score(self, post: Dict[str, Any]) -> float:
        """Calculate relevance score for a governance post."""
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        description = post.get('description', '').lower()
        
        full_text = f"{title} {content} {description}"
        score = 0.0
        
        # High-priority keywords
        high_priority = ['liquidation threshold', 'loan-to-value', 'risk parameter', 'parameter update']
        for keyword in high_priority:
            if keyword in full_text:
                score += 3.0
        
        # Medium-priority keywords
        medium_priority = ['liquidation bonus', 'reserve factor', 'borrow cap', 'supply cap']
        for keyword in medium_priority:
            if keyword in full_text:
                score += 2.0
        
        # General keywords
        for keyword in self.governance_keywords:
            if keyword.lower() in full_text:
                score += 1.0
        
        # Boost score for recent posts (within last 7 days)
        try:
            pub_date = post.get('pub_date', '')
            if pub_date:
                # Simple heuristic - boost recent posts
                if 'hour' in pub_date or 'minute' in pub_date or 'day' in pub_date:
                    score += 1.0
        except:
            pass
        
        return score
    
    def track_parameter_changes(self, current_data: Dict[str, List[Dict]], 
                              previous_data: Optional[Dict[str, List[Dict]]] = None) -> List[ParameterChange]:
        """
        Track parameter changes between current and historical data.
        
        Args:
            current_data: Current protocol data
            previous_data: Previous protocol data (if None, uses historical data)
            
        Returns:
            List of detected parameter changes
        """
        if previous_data is None:
            previous_data = self.historical_data.get('parameter_history', {})
        
        changes = []
        
        for network, assets in current_data.items():
            previous_network_data = previous_data.get(network, [])
            previous_assets = {asset['asset_address']: asset for asset in previous_network_data}
            
            for asset in assets:
                asset_address = asset['asset_address']
                symbol = asset.get('symbol', 'UNKNOWN')
                
                if asset_address in previous_assets:
                    previous_asset = previous_assets[asset_address]
                    
                    # Check each parameter for changes
                    parameters_to_check = [
                        'liquidation_threshold', 'loan_to_value', 
                        'liquidation_bonus', 'reserve_factor'
                    ]
                    
                    for param in parameters_to_check:
                        current_value = asset.get(param)
                        previous_value = previous_asset.get(param)
                        
                        if (current_value is not None and previous_value is not None and 
                            current_value != previous_value):
                            
                            change_percentage = abs(current_value - previous_value) / max(previous_value, 0.001)
                            
                            change = ParameterChange(
                                asset=symbol,
                                network=network,
                                parameter=param,
                                old_value=previous_value,
                                new_value=current_value,
                                change_percentage=change_percentage,
                                timestamp=datetime.now(),
                                risk_level=self._assess_risk_level(param, change_percentage, current_value)
                            )
                            
                            changes.append(change)
        
        return changes
    
    def _assess_risk_level(self, parameter: str, change_percentage: float, new_value: float) -> str:
        """Assess the risk level of a parameter change."""
        thresholds = self.critical_thresholds.get(parameter, {})
        
        # Check for critical changes
        if change_percentage >= thresholds.get('critical_change', 0.10):
            return "critical"
        
        # Check for major changes
        if change_percentage >= thresholds.get('major_change', 0.05):
            return "high"
        
        # Check for concerning absolute values
        min_value = thresholds.get('min_value', 0)
        max_value = thresholds.get('max_value', 1)
        
        if new_value <= min_value or new_value >= max_value:
            return "high"
        
        # Medium risk for smaller changes
        if change_percentage >= 0.02:  # 2% change
            return "medium"
        
        return "low"
    
    def generate_alerts(self, parameter_changes: List[ParameterChange], 
                       governance_posts: List[Dict[str, Any]]) -> List[GovernanceAlert]:
        """
        Generate alerts based on parameter changes and governance activity.
        
        Args:
            parameter_changes: List of detected parameter changes
            governance_posts: List of relevant governance posts
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        # Group changes by risk level
        critical_changes = [c for c in parameter_changes if c.risk_level == "critical"]
        high_risk_changes = [c for c in parameter_changes if c.risk_level == "high"]
        
        # Critical parameter change alerts
        if critical_changes:
            alert = GovernanceAlert(
                alert_type="critical_parameter_change",
                message=f"CRITICAL: {len(critical_changes)} critical parameter changes detected",
                parameter_changes=critical_changes,
                timestamp=datetime.now(),
                severity="critical"
            )
            alerts.append(alert)
        
        # High-risk parameter change alerts
        if high_risk_changes:
            alert = GovernanceAlert(
                alert_type="high_risk_parameter_change",
                message=f"HIGH RISK: {len(high_risk_changes)} high-risk parameter changes detected",
                parameter_changes=high_risk_changes,
                timestamp=datetime.now(),
                severity="high"
            )
            alerts.append(alert)
        
        # Liquidation threshold specific alerts
        lt_changes = [c for c in parameter_changes if c.parameter == "liquidation_threshold"]
        if lt_changes:
            # Check for concerning LT patterns
            low_lt_assets = [c for c in lt_changes if c.new_value < 0.60]  # Below 60% LT
            if low_lt_assets:
                alert = GovernanceAlert(
                    alert_type="low_liquidation_threshold",
                    message=f"WARNING: {len(low_lt_assets)} assets with low liquidation thresholds (<60%)",
                    parameter_changes=low_lt_assets,
                    timestamp=datetime.now(),
                    severity="medium"
                )
                alerts.append(alert)
        
        # Governance activity alerts
        high_relevance_posts = [p for p in governance_posts if p.get('relevance_score', 0) >= 5.0]
        if high_relevance_posts:
            alert = GovernanceAlert(
                alert_type="high_relevance_governance_activity",
                message=f"INFO: {len(high_relevance_posts)} high-relevance governance posts detected",
                parameter_changes=[],
                timestamp=datetime.now(),
                severity="low"
            )
            alerts.append(alert)
        
        return alerts
    
    def update_historical_data(self, current_data: Dict[str, List[Dict]], 
                             governance_posts: List[Dict[str, Any]],
                             parameter_changes: List[ParameterChange],
                             alerts: List[GovernanceAlert]):
        """Update historical data with current information."""
        # Update parameter history
        self.historical_data['parameter_history'] = current_data
        self.historical_data['last_update'] = datetime.now().isoformat()
        
        # Add new governance posts (keep last 100)
        existing_posts = self.historical_data.get('governance_posts', [])
        all_posts = existing_posts + governance_posts
        
        # Remove duplicates based on title and link
        seen = set()
        unique_posts = []
        for post in all_posts:
            key = (post.get('title', ''), post.get('link', ''))
            if key not in seen:
                seen.add(key)
                unique_posts.append(post)
        
        # Keep only the most recent 100 posts
        self.historical_data['governance_posts'] = unique_posts[-100:]
        
        # Add parameter changes to history
        if 'parameter_changes' not in self.historical_data:
            self.historical_data['parameter_changes'] = []
        
        # Convert ParameterChange objects to dictionaries
        change_dicts = []
        for change in parameter_changes:
            change_dict = {
                'asset': change.asset,
                'network': change.network,
                'parameter': change.parameter,
                'old_value': change.old_value,
                'new_value': change.new_value,
                'change_percentage': change.change_percentage,
                'timestamp': change.timestamp.isoformat(),
                'risk_level': change.risk_level
            }
            change_dicts.append(change_dict)
        
        self.historical_data['parameter_changes'].extend(change_dicts)
        
        # Keep only the last 500 parameter changes
        self.historical_data['parameter_changes'] = self.historical_data['parameter_changes'][-500:]
        
        # Add alerts to history
        if 'alerts_generated' not in self.historical_data:
            self.historical_data['alerts_generated'] = []
        
        # Convert GovernanceAlert objects to dictionaries
        alert_dicts = []
        for alert in alerts:
            alert_dict = {
                'alert_type': alert.alert_type,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity,
                'parameter_changes_count': len(alert.parameter_changes)
            }
            alert_dicts.append(alert_dict)
        
        self.historical_data['alerts_generated'].extend(alert_dicts)
        
        # Keep only the last 200 alerts
        self.historical_data['alerts_generated'] = self.historical_data['alerts_generated'][-200:]
        
        # Save updated historical data
        self._save_historical_data()
    
    def run_governance_monitoring(self, current_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Run complete governance monitoring process.
        
        Args:
            current_data: Current protocol data
            
        Returns:
            Dictionary containing monitoring results
        """
        print("🏛️  Starting governance monitoring...")
        
        # Monitor RSS feeds
        governance_posts = self.monitor_governance_feeds()
        
        # Track parameter changes
        parameter_changes = self.track_parameter_changes(current_data)
        
        # Generate alerts
        alerts = self.generate_alerts(parameter_changes, governance_posts)
        
        # Update historical data
        self.update_historical_data(current_data, governance_posts, parameter_changes, alerts)
        
        # Create monitoring report
        monitoring_report = {
            'timestamp': datetime.now().isoformat(),
            'governance_posts_found': len(governance_posts),
            'parameter_changes_detected': len(parameter_changes),
            'alerts_generated': len(alerts),
            'governance_posts': governance_posts[:10],  # Top 10 most relevant
            'parameter_changes': [
                {
                    'asset': change.asset,
                    'network': change.network,
                    'parameter': change.parameter,
                    'old_value': change.old_value,
                    'new_value': change.new_value,
                    'change_percentage': change.change_percentage,
                    'risk_level': change.risk_level
                }
                for change in parameter_changes
            ],
            'alerts': [
                {
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'severity': alert.severity,
                    'parameter_changes_count': len(alert.parameter_changes)
                }
                for alert in alerts
            ],
            'summary': {
                'critical_changes': len([c for c in parameter_changes if c.risk_level == "critical"]),
                'high_risk_changes': len([c for c in parameter_changes if c.risk_level == "high"]),
                'medium_risk_changes': len([c for c in parameter_changes if c.risk_level == "medium"]),
                'low_risk_changes': len([c for c in parameter_changes if c.risk_level == "low"]),
                'critical_alerts': len([a for a in alerts if a.severity == "critical"]),
                'high_severity_alerts': len([a for a in alerts if a.severity == "high"])
            }
        }
        
        print(f"   📊 Found {len(governance_posts)} relevant governance posts")
        print(f"   📈 Detected {len(parameter_changes)} parameter changes")
        print(f"   🚨 Generated {len(alerts)} alerts")
        
        if parameter_changes:
            critical_count = monitoring_report['summary']['critical_changes']
            high_risk_count = monitoring_report['summary']['high_risk_changes']
            
            if critical_count > 0:
                print(f"   🔴 CRITICAL: {critical_count} critical parameter changes!")
            if high_risk_count > 0:
                print(f"   🟠 HIGH RISK: {high_risk_count} high-risk parameter changes!")
        
        return monitoring_report


def save_governance_report(monitoring_report: Dict[str, Any], filename: str = "governance_monitoring_report.json"):
    """Save governance monitoring report to file."""
    try:
        with open(filename, 'w') as f:
            json.dump(monitoring_report, f, indent=2, default=str)
        print(f"📊 Governance monitoring report saved to {filename}")
    except IOError as e:
        print(f"⚠️  Warning: Could not save governance report: {e}")


def validate_against_governance_snapshots(current_data: Dict[str, List[Dict]], 
                                        governance_history_file: str = "governance_history.json") -> Dict[str, Any]:
    """
    Validate current data against governance snapshots and proposal outcomes.
    
    Args:
        current_data: Current protocol data
        governance_history_file: Path to governance history file
        
    Returns:
        Validation results
    """
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'validation_passed': True,
        'validation_errors': [],
        'validation_warnings': [],
        'governance_consistency_score': 1.0,
        'networks_validated': 0,
        'assets_validated': 0
    }
    
    try:
        # Load governance history
        if os.path.exists(governance_history_file):
            with open(governance_history_file, 'r') as f:
                governance_history = json.load(f)
        else:
            print("⚠️  No governance history file found - skipping governance validation")
            return validation_results
        
        # Get recent parameter changes from history
        recent_changes = governance_history.get('parameter_changes', [])
        
        # Validate against recent governance decisions
        for network, assets in current_data.items():
            validation_results['networks_validated'] += 1
            
            for asset in assets:
                validation_results['assets_validated'] += 1
                asset_address = asset['asset_address']
                symbol = asset.get('symbol', 'UNKNOWN')
                
                # Check if current parameters align with recent governance changes
                for change in recent_changes[-50:]:  # Check last 50 changes
                    if (change['network'] == network and 
                        change['asset'] == symbol):
                        
                        current_value = asset.get(change['parameter'])
                        expected_value = change['new_value']
                        
                        if current_value is not None and expected_value is not None:
                            # Allow for small rounding differences
                            tolerance = 0.001
                            if abs(current_value - expected_value) > tolerance:
                                error_msg = (
                                    f"Governance mismatch: {symbol} on {network} "
                                    f"{change['parameter']} is {current_value}, "
                                    f"expected {expected_value} from governance change"
                                )
                                validation_results['validation_errors'].append(error_msg)
                                validation_results['validation_passed'] = False
        
        # Calculate governance consistency score
        total_checks = len(validation_results['validation_errors']) + len(validation_results['validation_warnings'])
        if total_checks > 0:
            error_weight = len(validation_results['validation_errors']) * 1.0
            warning_weight = len(validation_results['validation_warnings']) * 0.5
            validation_results['governance_consistency_score'] = max(0.0, 1.0 - (error_weight + warning_weight) / 10.0)
        
        print(f"🏛️  Governance validation: {validation_results['assets_validated']} assets checked")
        print(f"   ✅ Consistency score: {validation_results['governance_consistency_score']:.2%}")
        
        if validation_results['validation_errors']:
            print(f"   ❌ {len(validation_results['validation_errors'])} governance inconsistencies found")
        
        if validation_results['validation_warnings']:
            print(f"   ⚠️  {len(validation_results['validation_warnings'])} governance warnings")
        
    except Exception as e:
        validation_results['validation_passed'] = False
        validation_results['validation_errors'].append(f"Governance validation failed: {str(e)}")
        print(f"❌ Governance validation error: {e}")
    
    return validation_results


# Global governance monitor instance
governance_monitor = GovernanceMonitor()