"""
HTML output generation for governance monitoring data.
Creates human-readable HTML pages for governance reports and parameter tracking.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


def generate_governance_html(monitoring_report: Dict[str, Any], 
                           validation_report: Optional[Dict[str, Any]] = None,
                           output_file: str = "governance_monitoring.html") -> bool:
    """
    Generate HTML page for governance monitoring data.
    
    Args:
        monitoring_report: Governance monitoring report data
        validation_report: Optional governance validation report
        output_file: Output HTML file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        html_content = _create_governance_html_content(monitoring_report, validation_report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 Governance HTML report saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate governance HTML: {e}")
        return False


def _create_governance_html_content(monitoring_report: Dict[str, Any], 
                                  validation_report: Optional[Dict[str, Any]] = None) -> str:
    """Create the complete HTML content for governance monitoring."""
    
    timestamp = monitoring_report.get('timestamp', datetime.now().isoformat())
    summary = monitoring_report.get('summary', {})
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aave V3 Governance Monitoring</title>
    <style>
        {_get_governance_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏛️ Aave V3 Governance Monitoring</h1>
            <p class="subtitle">Real-time parameter tracking and governance activity monitoring</p>
            <div class="timestamp">Last updated: {_format_timestamp(timestamp)}</div>
        </header>

        {_create_summary_section(summary)}
        
        {_create_alerts_section(monitoring_report.get('alerts', []))}
        
        {_create_parameter_changes_section(monitoring_report.get('parameter_changes', []))}
        
        {_create_governance_posts_section(monitoring_report.get('governance_posts', []))}
        
        {_create_validation_section(validation_report) if validation_report else ''}
        
        {_create_footer()}
    </div>
</body>
</html>"""
    
    return html


def _get_governance_css() -> str:
    """Get CSS styles for governance HTML page."""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 15px;
        }
        
        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .section {
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .summary-card.critical {
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }
        
        .summary-card.warning {
            border-left-color: #f39c12;
            background: #fef9e7;
        }
        
        .summary-card.success {
            border-left-color: #27ae60;
            background: #f0f9f4;
        }
        
        .summary-number {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .summary-label {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .alert {
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .alert.critical {
            background: #fdf2f2;
            border-left-color: #e74c3c;
            color: #c0392b;
        }
        
        .alert.high {
            background: #fef9e7;
            border-left-color: #f39c12;
            color: #d68910;
        }
        
        .alert.medium {
            background: #e8f4fd;
            border-left-color: #3498db;
            color: #2980b9;
        }
        
        .alert.low {
            background: #f0f9f4;
            border-left-color: #27ae60;
            color: #229954;
        }
        
        .alert-header {
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .alert-message {
            font-size: 0.95em;
        }
        
        .changes-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .changes-table th,
        .changes-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .changes-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .changes-table tr:hover {
            background: #f8f9fa;
        }
        
        .risk-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .risk-critical {
            background: #e74c3c;
            color: white;
        }
        
        .risk-high {
            background: #f39c12;
            color: white;
        }
        
        .risk-medium {
            background: #3498db;
            color: white;
        }
        
        .risk-low {
            background: #27ae60;
            color: white;
        }
        
        .change-value {
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }
        
        .change-positive {
            color: #27ae60;
        }
        
        .change-negative {
            color: #e74c3c;
        }
        
        .posts-grid {
            display: grid;
            gap: 15px;
        }
        
        .post-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .post-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .post-title a {
            color: #2c3e50;
            text-decoration: none;
        }
        
        .post-title a:hover {
            color: #3498db;
            text-decoration: underline;
        }
        
        .post-meta {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        
        .post-description {
            color: #555;
            line-height: 1.5;
        }
        
        .relevance-score {
            background: #3498db;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .validation-score {
            font-size: 1.5em;
            font-weight: bold;
            color: #27ae60;
        }
        
        .validation-score.warning {
            color: #f39c12;
        }
        
        .validation-score.error {
            color: #e74c3c;
        }
        
        .no-data {
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            padding: 40px;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .footer-links {
            margin-top: 10px;
        }
        
        .footer-links a {
            color: #3498db;
            text-decoration: none;
            margin: 0 10px;
        }
        
        .footer-links a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            header h1 {
                font-size: 2em;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .changes-table {
                font-size: 0.9em;
            }
            
            .changes-table th,
            .changes-table td {
                padding: 8px;
            }
        }
    """


def _format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p UTC')
    except:
        return timestamp_str


def _create_summary_section(summary: Dict[str, Any]) -> str:
    """Create the summary statistics section."""
    critical_changes = summary.get('critical_changes', 0)
    high_risk_changes = summary.get('high_risk_changes', 0)
    medium_risk_changes = summary.get('medium_risk_changes', 0)
    low_risk_changes = summary.get('low_risk_changes', 0)
    critical_alerts = summary.get('critical_alerts', 0)
    high_severity_alerts = summary.get('high_severity_alerts', 0)
    
    total_changes = critical_changes + high_risk_changes + medium_risk_changes + low_risk_changes
    total_alerts = critical_alerts + high_severity_alerts
    
    return f"""
    <div class="section">
        <h2>📊 Summary</h2>
        <div class="summary-grid">
            <div class="summary-card {'critical' if critical_changes > 0 else 'success'}">
                <div class="summary-number">{critical_changes}</div>
                <div class="summary-label">Critical Changes</div>
            </div>
            <div class="summary-card {'warning' if high_risk_changes > 0 else 'success'}">
                <div class="summary-number">{high_risk_changes}</div>
                <div class="summary-label">High Risk Changes</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{total_changes}</div>
                <div class="summary-label">Total Parameter Changes</div>
            </div>
            <div class="summary-card {'critical' if critical_alerts > 0 else 'warning' if total_alerts > 0 else 'success'}">
                <div class="summary-number">{total_alerts}</div>
                <div class="summary-label">Active Alerts</div>
            </div>
        </div>
    </div>
    """


def _create_alerts_section(alerts: List[Dict[str, Any]]) -> str:
    """Create the alerts section."""
    if not alerts:
        return f"""
        <div class="section">
            <h2>🚨 Alerts</h2>
            <div class="no-data">No active alerts</div>
        </div>
        """
    
    alerts_html = ""
    for alert in alerts:
        severity = alert.get('severity', 'medium')
        alert_type = alert.get('alert_type', '')
        message = alert.get('message', '')
        changes_count = alert.get('parameter_changes_count', 0)
        
        alerts_html += f"""
        <div class="alert {severity}">
            <div class="alert-header">{_get_severity_emoji(severity)} {alert_type.replace('_', ' ').title()}</div>
            <div class="alert-message">{message}</div>
            {f'<div style="margin-top: 8px; font-size: 0.9em;">Affects {changes_count} parameter changes</div>' if changes_count > 0 else ''}
        </div>
        """
    
    return f"""
    <div class="section">
        <h2>🚨 Alerts</h2>
        {alerts_html}
    </div>
    """


def _create_parameter_changes_section(parameter_changes: List[Dict[str, Any]]) -> str:
    """Create the parameter changes section."""
    if not parameter_changes:
        return f"""
        <div class="section">
            <h2>📈 Parameter Changes</h2>
            <div class="no-data">No parameter changes detected</div>
        </div>
        """
    
    # Sort changes by risk level and change percentage
    risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_changes = sorted(parameter_changes, 
                          key=lambda x: (risk_order.get(x.get('risk_level', 'low'), 3), 
                                       -x.get('change_percentage', 0)))
    
    table_rows = ""
    for change in sorted_changes:
        asset = change.get('asset', 'Unknown')
        network = change.get('network', 'Unknown')
        parameter = change.get('parameter', 'Unknown')
        old_value = change.get('old_value', 0)
        new_value = change.get('new_value', 0)
        change_percentage = change.get('change_percentage', 0)
        risk_level = change.get('risk_level', 'low')
        
        # Format values based on parameter type
        if parameter in ['liquidation_threshold', 'loan_to_value', 'reserve_factor']:
            old_formatted = f"{old_value:.1%}"
            new_formatted = f"{new_value:.1%}"
        else:
            old_formatted = f"{old_value:.4f}"
            new_formatted = f"{new_value:.4f}"
        
        change_direction = "positive" if new_value > old_value else "negative"
        change_arrow = "↗️" if new_value > old_value else "↘️"
        
        table_rows += f"""
        <tr>
            <td>{asset}</td>
            <td>{network.title()}</td>
            <td>{parameter.replace('_', ' ').title()}</td>
            <td class="change-value">{old_formatted}</td>
            <td class="change-value change-{change_direction}">{change_arrow} {new_formatted}</td>
            <td>{change_percentage:.1%}</td>
            <td><span class="risk-badge risk-{risk_level}">{risk_level}</span></td>
        </tr>
        """
    
    return f"""
    <div class="section">
        <h2>📈 Parameter Changes</h2>
        <table class="changes-table">
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Network</th>
                    <th>Parameter</th>
                    <th>Old Value</th>
                    <th>New Value</th>
                    <th>Change %</th>
                    <th>Risk Level</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """


def _create_governance_posts_section(governance_posts: List[Dict[str, Any]]) -> str:
    """Create the governance posts section."""
    if not governance_posts:
        return f"""
        <div class="section">
            <h2>🏛️ Governance Activity</h2>
            <div class="no-data">No relevant governance posts found</div>
        </div>
        """
    
    posts_html = ""
    for post in governance_posts[:10]:  # Show top 10 posts
        title = post.get('title', 'Untitled')
        link = post.get('link', '#')
        description = post.get('description', '')
        pub_date = post.get('pub_date', '')
        feed_source = post.get('feed_source', 'Unknown')
        relevance_score = post.get('relevance_score', 0)
        
        # Truncate description if too long
        if len(description) > 200:
            description = description[:200] + "..."
        
        posts_html += f"""
        <div class="post-card">
            <div class="post-title">
                <a href="{link}" target="_blank">{title}</a>
            </div>
            <div class="post-meta">
                Source: {feed_source.replace('_', ' ').title()} | 
                Relevance: <span class="relevance-score">{relevance_score:.1f}</span>
                {f' | {pub_date}' if pub_date else ''}
            </div>
            <div class="post-description">{description}</div>
        </div>
        """
    
    return f"""
    <div class="section">
        <h2>🏛️ Recent Governance Activity</h2>
        <div class="posts-grid">
            {posts_html}
        </div>
    </div>
    """


def _create_validation_section(validation_report: Dict[str, Any]) -> str:
    """Create the governance validation section."""
    if not validation_report:
        return ""
    
    validation_passed = validation_report.get('validation_passed', True)
    consistency_score = validation_report.get('governance_consistency_score', 1.0)
    networks_validated = validation_report.get('networks_validated', 0)
    assets_validated = validation_report.get('assets_validated', 0)
    validation_errors = validation_report.get('validation_errors', [])
    validation_warnings = validation_report.get('validation_warnings', [])
    
    score_class = "error" if consistency_score < 0.8 else "warning" if consistency_score < 0.95 else ""
    status_emoji = "✅" if validation_passed else "❌"
    
    errors_html = ""
    if validation_errors:
        errors_html = "<h3>❌ Validation Errors</h3><ul>"
        for error in validation_errors[:5]:  # Show first 5 errors
            errors_html += f"<li>{error}</li>"
        if len(validation_errors) > 5:
            errors_html += f"<li><em>... and {len(validation_errors) - 5} more errors</em></li>"
        errors_html += "</ul>"
    
    warnings_html = ""
    if validation_warnings:
        warnings_html = "<h3>⚠️ Validation Warnings</h3><ul>"
        for warning in validation_warnings[:5]:  # Show first 5 warnings
            warnings_html += f"<li>{warning}</li>"
        if len(validation_warnings) > 5:
            warnings_html += f"<li><em>... and {len(validation_warnings) - 5} more warnings</em></li>"
        warnings_html += "</ul>"
    
    return f"""
    <div class="section">
        <h2>🔍 Governance Validation</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-number">{status_emoji}</div>
                <div class="summary-label">Validation Status</div>
            </div>
            <div class="summary-card">
                <div class="validation-score {score_class}">{consistency_score:.1%}</div>
                <div class="summary-label">Consistency Score</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{assets_validated}</div>
                <div class="summary-label">Assets Validated</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{networks_validated}</div>
                <div class="summary-label">Networks Validated</div>
            </div>
        </div>
        {errors_html}
        {warnings_html}
    </div>
    """


def _get_severity_emoji(severity: str) -> str:
    """Get emoji for alert severity."""
    emoji_map = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }
    return emoji_map.get(severity, '🔵')


def _create_footer() -> str:
    """Create the footer section."""
    return f"""
    <footer>
        <div>
            Generated by Aave V3 Data Fetcher | 
            <strong>Governance Monitoring System</strong>
        </div>
        <div class="footer-links">
            <a href="aave_v3_data.html">📊 Protocol Data</a>
            <a href="aave_v3_data.json">📄 JSON API</a>
            <a href="governance_monitoring_report.json">🏛️ Governance JSON</a>
            <a href="https://governance.aave.com" target="_blank">🗳️ Aave Governance</a>
        </div>
    </footer>
    """


def save_governance_html_output(monitoring_report: Dict[str, Any], 
                              validation_report: Optional[Dict[str, Any]] = None,
                              output_file: str = "governance_monitoring.html") -> bool:
    """
    Save governance monitoring data as HTML file.
    
    Args:
        monitoring_report: Governance monitoring report data
        validation_report: Optional governance validation report
        output_file: Output HTML file path
        
    Returns:
        True if successful, False otherwise
    """
    return generate_governance_html(monitoring_report, validation_report, output_file)