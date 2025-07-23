# Governance Monitoring and Parameter Tracking Guide

This guide covers how to monitor Aave governance for parameter changes and track critical updates that affect liquidation risks and protocol behavior.

## 🏛️ Overview

Aave V3 protocol parameters are managed through decentralized governance. This system helps you:
- Monitor governance proposals for parameter changes
- Track historical parameter evolution
- Set up alerts for critical parameter updates
- Validate changes against governance decisions

## 📊 Governance Monitoring System

### Key Parameters to Monitor

#### Critical Risk Parameters
- **Liquidation Threshold (LT)** - Maximum LTV before liquidation
- **Loan-to-Value (LTV)** - Maximum borrowing ratio
- **Liquidation Bonus** - Liquidator incentive percentage
- **Reserve Factor** - Protocol fee on interest

#### Supply/Borrow Management
- **Supply Caps** - Maximum supply amounts per asset
- **Borrow Caps** - Maximum borrow amounts per asset
- **Debt Ceilings** - Maximum debt in isolation mode

#### Status Flags
- **Active/Frozen** - Asset availability status
- **Borrowing Enabled** - Borrowing permission
- **Stable Borrowing** - Stable rate availability

### Governance Sources

#### Primary Sources
1. **Aave Governance Forum** - https://governance.aave.com/
2. **Snapshot Voting** - https://snapshot.org/#/aave.eth
3. **On-chain Governance** - Ethereum governance contracts
4. **BGD Labs Updates** - https://bgdlabs.com/

#### RSS Feeds and APIs
```python
GOVERNANCE_FEEDS = {
    'forum_rss': 'https://governance.aave.com/latest.rss',
    'snapshot_api': 'https://hub.snapshot.org/graphql',
    'github_releases': 'https://api.github.com/repos/bgd-labs/aave-proposals-v3/releases',
    'governance_api': 'https://api.aave.com/governance/proposals'
}
```

## 🔍 Implementation

### RSS Feed Monitoring

```python
#!/usr/bin/env python3
"""Governance RSS feed monitoring implementation."""

import feedparser
import json
import time
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.parse import urljoin

class GovernanceMonitor:
    """Monitor Aave governance for parameter changes."""
    
    def __init__(self):
        self.feeds = {
            'forum': 'https://governance.aave.com/latest.rss',
            'snapshot': 'https://snapshot.org/api/spaces/aave.eth/proposals'
        }
        self.keywords = [
            'liquidation threshold', 'LTV', 'loan-to-value',
            'reserve factor', 'supply cap', 'borrow cap',
            'risk parameters', 'parameter update', 'chaos labs'
        ]
    
    def check_forum_updates(self):
        """Check Aave governance forum for new posts."""
        try:
            feed = feedparser.parse(self.feeds['forum'])
            recent_posts = []
            
            # Check posts from last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for entry in feed.entries:
                post_time = datetime(*entry.published_parsed[:6])
                if post_time > cutoff_time:
                    # Check if post contains parameter-related keywords
                    content = (entry.title + ' ' + entry.summary).lower()
                    if any(keyword in content for keyword in self.keywords):
                        recent_posts.append({
                            'title': entry.title,
                            'link': entry.link,
                            'published': post_time.isoformat(),
                            'summary': entry.summary[:200] + '...',
                            'keywords_found': [kw for kw in self.keywords if kw in content]
                        })
            
            return recent_posts
            
        except Exception as e:
            print(f"Error checking forum updates: {e}")
            return []
    
    def check_snapshot_proposals(self):
        """Check Snapshot for new governance proposals."""
        try:
            # GraphQL query for recent proposals
            query = """
            {
              proposals(
                where: {
                  space: "aave.eth",
                  created_gte: %d
                },
                orderBy: "created",
                orderDirection: desc
              ) {
                id
                title
                body
                choices
                start
                end
                state
                author
                created
              }
            }
            """ % int((datetime.now() - timedelta(days=7)).timestamp())
            
            # This would require a GraphQL client in a real implementation
            # For now, return placeholder
            return []
            
        except Exception as e:
            print(f"Error checking Snapshot proposals: {e}")
            return []
    
    def generate_alert(self, updates):
        """Generate alert for governance updates."""
        if not updates:
            return None
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': 'governance_update',
            'updates_count': len(updates),
            'updates': updates,
            'action_required': self.assess_criticality(updates)
        }
        
        return alert
    
    def assess_criticality(self, updates):
        """Assess if updates require immediate attention."""
        critical_keywords = ['liquidation threshold', 'emergency', 'pause', 'freeze']
        
        for update in updates:
            content = (update.get('title', '') + ' ' + update.get('summary', '')).lower()
            if any(keyword in content for keyword in critical_keywords):
                return 'high'
        
        return 'medium' if updates else 'low'

# Usage example
def monitor_governance():
    """Main governance monitoring function."""
    monitor = GovernanceMonitor()
    
    # Check for updates
    forum_updates = monitor.check_forum_updates()
    snapshot_updates = monitor.check_snapshot_proposals()
    
    all_updates = forum_updates + snapshot_updates
    
    if all_updates:
        alert = monitor.generate_alert(all_updates)
        
        # Save alert to file
        with open('governance_alert.json', 'w') as f:
            json.dump(alert, f, indent=2)
        
        print(f"🚨 Governance Alert: {len(all_updates)} updates found")
        for update in all_updates:
            print(f"  - {update['title']}")
    else:
        print("✅ No recent governance updates")
    
    return all_updates

if __name__ == "__main__":
    monitor_governance()
```

### Historical Parameter Tracking

```python
#!/usr/bin/env python3
"""Historical parameter tracking implementation."""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

class ParameterTracker:
    """Track historical changes to Aave V3 parameters."""
    
    def __init__(self, db_path='parameter_history.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for parameter tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                network TEXT NOT NULL,
                asset_symbol TEXT NOT NULL,
                asset_address TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                change_percentage REAL,
                governance_proposal TEXT,
                change_reason TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON parameter_history(timestamp);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_network_asset ON parameter_history(network, asset_symbol);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_parameter ON parameter_history(parameter_name);
        ''')
        
        conn.commit()
        conn.close()
    
    def record_parameter_change(self, network: str, asset_symbol: str, asset_address: str,
                              parameter_name: str, old_value: float, new_value: float,
                              governance_proposal: str = None, change_reason: str = None):
        """Record a parameter change in the database."""
        
        change_percentage = ((new_value - old_value) / old_value * 100) if old_value != 0 else 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO parameter_history 
            (timestamp, network, asset_symbol, asset_address, parameter_name, 
             old_value, new_value, change_percentage, governance_proposal, change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            network,
            asset_symbol,
            asset_address,
            parameter_name,
            old_value,
            new_value,
            change_percentage,
            governance_proposal,
            change_reason
        ))
        
        conn.commit()
        conn.close()
    
    def detect_parameter_changes(self, current_data: Dict, previous_data: Dict):
        """Detect changes between current and previous parameter data."""
        changes = []
        
        for network, assets in current_data.get('networks', {}).items():
            if network not in previous_data.get('networks', {}):
                continue
            
            previous_assets = {asset['asset_address']: asset 
                             for asset in previous_data['networks'][network]}
            
            for asset in assets:
                asset_address = asset['asset_address']
                if asset_address not in previous_assets:
                    continue
                
                previous_asset = previous_assets[asset_address]
                
                # Check each parameter for changes
                parameters_to_check = [
                    'liquidation_threshold', 'loan_to_value', 'liquidation_bonus',
                    'reserve_factor', 'supply_cap', 'borrow_cap'
                ]
                
                for param in parameters_to_check:
                    if param in asset and param in previous_asset:
                        current_value = asset[param]
                        previous_value = previous_asset[param]
                        
                        # Detect significant changes (>1% for most parameters)
                        threshold = 0.01 if param not in ['supply_cap', 'borrow_cap'] else 0.05
                        
                        if abs(current_value - previous_value) > threshold:
                            changes.append({
                                'network': network,
                                'asset_symbol': asset['symbol'],
                                'asset_address': asset_address,
                                'parameter': param,
                                'old_value': previous_value,
                                'new_value': current_value,
                                'change_percentage': ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
                            })
        
        return changes
    
    def get_parameter_history(self, network: str = None, asset_symbol: str = None, 
                            parameter_name: str = None, days: int = 30):
        """Get parameter change history with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM parameter_history 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days)
        
        params = []
        if network:
            query += ' AND network = ?'
            params.append(network)
        if asset_symbol:
            query += ' AND asset_symbol = ?'
            params.append(asset_symbol)
        if parameter_name:
            query += ' AND parameter_name = ?'
            params.append(parameter_name)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        columns = ['id', 'timestamp', 'network', 'asset_symbol', 'asset_address',
                  'parameter_name', 'old_value', 'new_value', 'change_percentage',
                  'governance_proposal', 'change_reason']
        
        return [dict(zip(columns, row)) for row in results]
    
    def generate_change_report(self, days: int = 7):
        """Generate a report of recent parameter changes."""
        changes = self.get_parameter_history(days=days)
        
        if not changes:
            return {'message': 'No parameter changes in the last {} days'.format(days)}
        
        # Group changes by significance
        critical_changes = [c for c in changes if abs(c['change_percentage']) > 10]
        significant_changes = [c for c in changes if 5 < abs(c['change_percentage']) <= 10]
        minor_changes = [c for c in changes if abs(c['change_percentage']) <= 5]
        
        report = {
            'period_days': days,
            'total_changes': len(changes),
            'critical_changes': len(critical_changes),
            'significant_changes': len(significant_changes),
            'minor_changes': len(minor_changes),
            'changes_by_network': {},
            'changes_by_parameter': {},
            'recent_changes': changes[:10]  # Most recent 10 changes
        }
        
        # Group by network
        for change in changes:
            network = change['network']
            if network not in report['changes_by_network']:
                report['changes_by_network'][network] = 0
            report['changes_by_network'][network] += 1
        
        # Group by parameter type
        for change in changes:
            param = change['parameter_name']
            if param not in report['changes_by_parameter']:
                report['changes_by_parameter'][param] = 0
            report['changes_by_parameter'][param] += 1
        
        return report

# Usage example
def track_parameter_changes():
    """Main parameter tracking function."""
    tracker = ParameterTracker()
    
    # Load current and previous data
    try:
        with open('aave_v3_data.json', 'r') as f:
            current_data = json.load(f)
        
        with open('aave_v3_data_previous.json', 'r') as f:
            previous_data = json.load(f)
    except FileNotFoundError:
        print("Data files not found. Run the fetcher first.")
        return
    
    # Detect changes
    changes = tracker.detect_parameter_changes(current_data, previous_data)
    
    if changes:
        print(f"🔍 Detected {len(changes)} parameter changes:")
        
        for change in changes:
            # Record in database
            tracker.record_parameter_change(
                change['network'],
                change['asset_symbol'],
                change['asset_address'],
                change['parameter'],
                change['old_value'],
                change['new_value']
            )
            
            print(f"  {change['network']}/{change['asset_symbol']}: "
                  f"{change['parameter']} changed from {change['old_value']:.4f} "
                  f"to {change['new_value']:.4f} ({change['change_percentage']:+.2f}%)")
    
    # Generate weekly report
    report = tracker.generate_change_report(days=7)
    
    with open('parameter_change_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📊 Weekly report: {report['total_changes']} total changes")
    print(f"   Critical: {report['critical_changes']}, "
          f"Significant: {report['significant_changes']}, "
          f"Minor: {report['minor_changes']}")

if __name__ == "__main__":
    track_parameter_changes()
```

### Alert System Implementation

```python
#!/usr/bin/env python3
"""Alert system for critical parameter changes."""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

class AlertSystem:
    """Alert system for critical Aave parameter changes."""
    
    def __init__(self, config_file='alert_config.json'):
        self.config = self.load_config(config_file)
        self.alert_thresholds = {
            'liquidation_threshold': 0.05,  # 5% change threshold
            'loan_to_value': 0.05,
            'liquidation_bonus': 0.10,
            'reserve_factor': 0.20,
            'supply_cap': 0.25,
            'borrow_cap': 0.25
        }
    
    def load_config(self, config_file: str) -> Dict:
        """Load alert configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'recipients': []
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                },
                'github_issue': {
                    'enabled': True,
                    'repository': '',
                    'token': ''
                }
            }
    
    def assess_alert_level(self, changes: List[Dict]) -> str:
        """Assess the alert level based on parameter changes."""
        if not changes:
            return 'none'
        
        critical_params = ['liquidation_threshold', 'loan_to_value']
        high_impact_changes = 0
        critical_changes = 0
        
        for change in changes:
            param = change['parameter']
            change_pct = abs(change['change_percentage'])
            
            if param in critical_params and change_pct > 5:
                critical_changes += 1
            elif change_pct > 10:
                high_impact_changes += 1
        
        if critical_changes > 0:
            return 'critical'
        elif high_impact_changes > 2:
            return 'high'
        elif len(changes) > 5:
            return 'medium'
        else:
            return 'low'
    
    def create_alert_message(self, changes: List[Dict], alert_level: str) -> Dict:
        """Create formatted alert message."""
        timestamp = datetime.now().isoformat()
        
        # Group changes by network and asset
        grouped_changes = {}
        for change in changes:
            key = f"{change['network']}/{change['asset_symbol']}"
            if key not in grouped_changes:
                grouped_changes[key] = []
            grouped_changes[key].append(change)
        
        # Create message
        message = {
            'timestamp': timestamp,
            'alert_level': alert_level,
            'total_changes': len(changes),
            'affected_assets': len(grouped_changes),
            'summary': self.create_summary(changes),
            'detailed_changes': grouped_changes,
            'recommendations': self.create_recommendations(changes, alert_level)
        }
        
        return message
    
    def create_summary(self, changes: List[Dict]) -> str:
        """Create a summary of changes."""
        if not changes:
            return "No significant parameter changes detected."
        
        networks = set(change['network'] for change in changes)
        parameters = set(change['parameter'] for change in changes)
        
        summary = f"Detected {len(changes)} parameter changes across {len(networks)} networks. "
        summary += f"Affected parameters: {', '.join(parameters)}."
        
        # Highlight critical changes
        critical_changes = [c for c in changes if c['parameter'] in ['liquidation_threshold', 'loan_to_value'] and abs(c['change_percentage']) > 5]
        if critical_changes:
            summary += f" ⚠️ {len(critical_changes)} critical risk parameter changes detected."
        
        return summary
    
    def create_recommendations(self, changes: List[Dict], alert_level: str) -> List[str]:
        """Create recommendations based on changes."""
        recommendations = []
        
        if alert_level == 'critical':
            recommendations.append("🚨 Immediate review required - critical risk parameters changed")
            recommendations.append("📊 Update liquidation monitoring systems")
            recommendations.append("🔍 Verify changes against governance proposals")
        
        elif alert_level == 'high':
            recommendations.append("⚠️ Review parameter changes within 24 hours")
            recommendations.append("📈 Monitor market impact of changes")
        
        elif alert_level == 'medium':
            recommendations.append("📋 Review changes during next maintenance window")
            recommendations.append("📊 Update documentation and monitoring")
        
        # Parameter-specific recommendations
        lt_changes = [c for c in changes if c['parameter'] == 'liquidation_threshold']
        if lt_changes:
            recommendations.append("🎯 Update liquidation threshold monitoring")
        
        cap_changes = [c for c in changes if 'cap' in c['parameter']]
        if cap_changes:
            recommendations.append("💰 Review supply/borrow capacity planning")
        
        return recommendations
    
    def send_github_issue_alert(self, message: Dict):
        """Create GitHub issue for parameter changes."""
        if not self.config['github_issue']['enabled']:
            return
        
        try:
            import requests
            
            title = f"Aave Parameter Changes Detected - {message['alert_level'].upper()} Alert"
            
            body = f"""
# Aave V3 Parameter Changes Alert

**Alert Level:** {message['alert_level'].upper()}
**Timestamp:** {message['timestamp']}
**Total Changes:** {message['total_changes']}
**Affected Assets:** {message['affected_assets']}

## Summary
{message['summary']}

## Recommendations
"""
            for rec in message['recommendations']:
                body += f"- {rec}\n"
            
            body += "\n## Detailed Changes\n"
            for asset, changes in message['detailed_changes'].items():
                body += f"\n### {asset}\n"
                for change in changes:
                    body += f"- **{change['parameter']}**: {change['old_value']:.4f} → {change['new_value']:.4f} ({change['change_percentage']:+.2f}%)\n"
            
            # Create GitHub issue
            url = f"https://api.github.com/repos/{self.config['github_issue']['repository']}/issues"
            headers = {
                'Authorization': f"token {self.config['github_issue']['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                'title': title,
                'body': body,
                'labels': ['alert', f"priority-{message['alert_level']}"]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            print(f"✅ GitHub issue created: {response.json()['html_url']}")
            
        except Exception as e:
            print(f"❌ Failed to create GitHub issue: {e}")
    
    def send_alert(self, changes: List[Dict]):
        """Send alert through configured channels."""
        if not changes:
            return
        
        alert_level = self.assess_alert_level(changes)
        message = self.create_alert_message(changes, alert_level)
        
        # Save alert to file
        alert_filename = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(alert_filename, 'w') as f:
            json.dump(message, f, indent=2)
        
        print(f"🚨 {alert_level.upper()} Alert: {message['summary']}")
        
        # Send through configured channels
        if self.config['github_issue']['enabled']:
            self.send_github_issue_alert(message)
        
        return message

# Usage example
def run_alert_system():
    """Main alert system function."""
    alert_system = AlertSystem()
    
    # This would typically be called after detecting parameter changes
    # For demo purposes, we'll load from a changes file
    try:
        with open('detected_changes.json', 'r') as f:
            changes = json.load(f)
        
        if changes:
            alert_system.send_alert(changes)
        else:
            print("✅ No parameter changes detected")
            
    except FileNotFoundError:
        print("No changes file found. Run parameter detection first.")

if __name__ == "__main__":
    run_alert_system()
```

## 🔧 Integration with Main Fetcher

### Automated Governance Monitoring

Add to the main fetcher workflow:

```python
# In aave_fetcher.py
def run_with_governance_monitoring():
    """Run fetcher with governance monitoring."""
    
    # 1. Backup previous data
    if os.path.exists('aave_v3_data.json'):
        shutil.copy('aave_v3_data.json', 'aave_v3_data_previous.json')
    
    # 2. Fetch new data
    main()
    
    # 3. Check for governance updates
    governance_updates = monitor_governance()
    
    # 4. Detect parameter changes
    if os.path.exists('aave_v3_data_previous.json'):
        tracker = ParameterTracker()
        with open('aave_v3_data.json', 'r') as f:
            current_data = json.load(f)
        with open('aave_v3_data_previous.json', 'r') as f:
            previous_data = json.load(f)
        
        changes = tracker.detect_parameter_changes(current_data, previous_data)
        
        if changes:
            # Record changes
            for change in changes:
                tracker.record_parameter_change(
                    change['network'], change['asset_symbol'], 
                    change['asset_address'], change['parameter'],
                    change['old_value'], change['new_value']
                )
            
            # Send alerts
            alert_system = AlertSystem()
            alert_system.send_alert(changes)
    
    # 5. Generate governance report
    generate_governance_report(governance_updates, changes if 'changes' in locals() else [])
```

### GitHub Actions Integration

Update the workflow to include governance monitoring:

```yaml
# In .github/workflows/update-aave-data.yml
- name: Run Aave Data Fetcher with Governance Monitoring
  run: |
    python aave_fetcher.py --ultra-fast --validate
    python governance_monitor.py
    python parameter_tracker.py

- name: Upload Governance Reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: governance-reports
    path: |
      governance_alert.json
      parameter_change_report.json
      alert_*.json
```

## 📊 Usage Examples

### Daily Monitoring

```bash
# Run complete governance monitoring
python governance_monitor.py

# Check for parameter changes
python parameter_tracker.py

# Generate alerts if needed
python alert_system.py
```

### Historical Analysis

```bash
# Get parameter history for USDC on Ethereum
python -c "
from parameter_tracker import ParameterTracker
tracker = ParameterTracker()
history = tracker.get_parameter_history('ethereum', 'USDC', 'liquidation_threshold', 90)
for change in history:
    print(f'{change[\"timestamp\"]}: {change[\"old_value\"]} -> {change[\"new_value\"]}')
"

# Generate monthly change report
python -c "
from parameter_tracker import ParameterTracker
tracker = ParameterTracker()
report = tracker.generate_change_report(30)
print(json.dumps(report, indent=2))
"
```

### Alert Configuration

Create `alert_config.json`:

```json
{
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "recipients": ["admin@yourcompany.com"]
  },
  "github_issue": {
    "enabled": true,
    "repository": "your-username/your-repo",
    "token": "your-github-token"
  },
  "webhook": {
    "enabled": false,
    "url": "https://hooks.slack.com/services/...",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

## 📈 Monitoring Dashboard

### Key Metrics to Track

1. **Parameter Volatility**
   - Frequency of changes per parameter type
   - Magnitude of changes over time
   - Networks with most frequent changes

2. **Governance Activity**
   - Proposal frequency
   - Voting participation
   - Implementation timeline

3. **Risk Assessment**
   - Critical parameter changes
   - Market impact correlation
   - Liquidation risk evolution

### Sample Dashboard Queries

```python
# Parameter change frequency
def get_change_frequency(days=30):
    tracker = ParameterTracker()
    changes = tracker.get_parameter_history(days=days)
    
    frequency = {}
    for change in changes:
        param = change['parameter_name']
        frequency[param] = frequency.get(param, 0) + 1
    
    return frequency

# Most volatile assets
def get_volatile_assets(days=30):
    tracker = ParameterTracker()
    changes = tracker.get_parameter_history(days=days)
    
    volatility = {}
    for change in changes:
        key = f"{change['network']}/{change['asset_symbol']}"
        if key not in volatility:
            volatility[key] = {'count': 0, 'total_change': 0}
        volatility[key]['count'] += 1
        volatility[key]['total_change'] += abs(change['change_percentage'])
    
    # Sort by total change magnitude
    return sorted(volatility.items(), key=lambda x: x[1]['total_change'], reverse=True)
```

This comprehensive governance monitoring system ensures you stay informed about critical parameter changes and can respond quickly to protect your positions and applications.