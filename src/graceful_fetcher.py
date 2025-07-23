"""
Graceful data fetching with degradation and monitoring.
Handles network failures gracefully and continues processing other networks.
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_reserves, get_asset_symbol, get_reserve_data
from networks import get_active_networks, get_fallback_urls
from monitoring import (
    get_healthy_rpc_urls, 
    should_skip_unhealthy_network,
    get_network_health_summary,
    create_github_actions_notification,
    save_health_report,
    health_monitor
)


class GracefulDataFetcher:
    """Fetches Aave V3 data with graceful degradation and error handling."""
    
    def __init__(self):
        self.successful_networks = []
        self.failed_networks = []
        self.skipped_networks = []
        self.partial_failures = {}
        self.start_time = datetime.now()
        self.health_monitor = health_monitor  # Use global instance
    
    def fetch_all_networks_data(self, max_failures: int = 5) -> Dict[str, Any]:
        """
        Fetch data from all active networks with graceful degradation.
        
        Args:
            max_failures: Maximum number of network failures before stopping
            
        Returns:
            Dictionary containing data from successful networks
        """
        networks = get_active_networks()
        all_data = {}
        failure_count = 0
        
        # Check if we should enable health checks (disabled by default)
        enable_health_checks = os.getenv('ENABLE_RPC_MONITORING', 'false').lower() == 'true'
        
        if enable_health_checks:
            print(f"Starting data fetch from {len(networks)} networks (health checks enabled)...")
        else:
            print(f"Starting data fetch from {len(networks)} networks...")
        
        for network_key, network_config in networks.items():
            try:
                # Check if network should be skipped due to health issues (only if enabled)
                if enable_health_checks:
                    should_skip, skip_reason = should_skip_unhealthy_network(network_key)
                    if should_skip:
                        print(f"⏭️  Skipping {network_config['name']}: {skip_reason}")
                        self.skipped_networks.append({
                            'network': network_key,
                            'name': network_config['name'],
                            'reason': skip_reason
                        })
                        continue
                
                # Fetch data for this network
                network_data = self.fetch_network_data(network_key, network_config)
                
                if network_data:
                    all_data[network_key] = network_data
                    self.successful_networks.append(network_key)
                    print(f"✅ {network_config['name']}: {len(network_data)} assets")
                else:
                    # Network returned no data
                    failure_count += 1
                    self.failed_networks.append({
                        'network': network_key,
                        'name': network_config['name'],
                        'error': 'No data returned'
                    })
                    print(f"❌ {network_config['name']}: No data returned")
                
            except Exception as e:
                failure_count += 1
                error_msg = str(e)
                self.failed_networks.append({
                    'network': network_key,
                    'name': network_config['name'],
                    'error': error_msg
                })
                print(f"❌ {network_config['name']}: {error_msg}")
                
                # Stop if too many failures
                if failure_count >= max_failures:
                    print(f"⚠️  Stopping after {failure_count} failures to prevent cascade")
                    break
        
        # Print summary
        self.print_fetch_summary()
        
        return all_data
    
    def fetch_network_data(self, network_key: str, network_config: Dict) -> Optional[List[Dict]]:
        """
        Fetch data for a single network with graceful degradation.
        
        Args:
            network_key: Network identifier
            network_config: Network configuration
            
        Returns:
            List of asset data or None if network failed
        """
        try:
            # Check if we should enable health checks (disabled by default)
            enable_health_checks = os.getenv('ENABLE_RPC_MONITORING', 'false').lower() == 'true'
            
            if enable_health_checks:
                # Get healthy RPC URLs with automatic failover
                healthy_urls = get_healthy_rpc_urls(network_key, network_config)
                
                if not healthy_urls:
                    print(f"⚠️  No healthy endpoints for {network_config['name']}")
                    return None
                
                primary_url = healthy_urls[0]
                fallback_urls = healthy_urls[1:] if len(healthy_urls) > 1 else None
            else:
                # Use configured URLs directly without health checks
                primary_url = network_config['rpc']
                fallback_urls = get_fallback_urls(network_config)
                # Limit fallback URLs for speed
                if fallback_urls and len(fallback_urls) > 3:
                    fallback_urls = fallback_urls[:3]
            
            # Get list of reserves
            try:
                reserves = get_reserves(
                    network_config['pool'], 
                    primary_url, 
                    fallback_urls,
                    network_key
                )
            except Exception as e:
                print(f"⚠️  Failed to get reserves for {network_config['name']}: {e}")
                return None
            
            if not reserves:
                print(f"⚠️  No reserves found for {network_config['name']}")
                return None
            
            # Fetch data for each asset with partial failure handling
            network_data = []
            asset_failures = 0
            max_asset_failures = max(len(reserves) // 4, 5)  # Allow 25% failures or min 5
            
            for asset_address in reserves:
                try:
                    asset_data = self.fetch_asset_data(
                        asset_address, 
                        network_config, 
                        primary_url, 
                        fallback_urls,
                        network_key
                    )
                    
                    if asset_data:
                        network_data.append(asset_data)
                    else:
                        asset_failures += 1
                        
                except Exception as e:
                    asset_failures += 1
                    print(f"⚠️  Failed to fetch data for asset {asset_address}: {e}")
                    
                    # Stop if too many asset failures
                    if asset_failures >= max_asset_failures:
                        print(f"⚠️  Too many asset failures ({asset_failures}) for {network_config['name']}")
                        break
            
            # Record partial failures
            if asset_failures > 0:
                self.partial_failures[network_key] = {
                    'network': network_config['name'],
                    'failed_assets': asset_failures,
                    'total_assets': len(reserves),
                    'success_rate': (len(reserves) - asset_failures) / len(reserves)
                }
            
            return network_data if network_data else None
            
        except Exception as e:
            print(f"❌ Network-level error for {network_config['name']}: {e}")
            return None
    
    def fetch_asset_data(
        self, 
        asset_address: str, 
        network_config: Dict, 
        primary_url: str, 
        fallback_urls: Optional[List[str]],
        network_key: str
    ) -> Optional[Dict]:
        """
        Fetch data for a single asset with error handling.
        
        Args:
            asset_address: Asset contract address
            network_config: Network configuration
            primary_url: Primary RPC URL
            fallback_urls: Fallback RPC URLs
            network_key: Network identifier
            
        Returns:
            Asset data dictionary or None if failed
        """
        try:
            # Get asset symbol (graceful failure)
            symbol = get_asset_symbol(
                asset_address, 
                primary_url, 
                fallback_urls,
                network_key
            )
            
            # Get reserve data (critical - must succeed)
            reserve_data = get_reserve_data(
                asset_address, 
                network_config['pool'], 
                primary_url, 
                fallback_urls,
                network_key
            )
            
            # Combine data
            asset_data = {
                'asset_address': asset_address,
                'symbol': symbol,
                **reserve_data
            }
            
            return asset_data
            
        except Exception as e:
            # Asset-level failure - log but don't stop network processing
            print(f"⚠️  Asset {asset_address} failed: {e}")
            return None
    
    def print_fetch_summary(self):
        """Print summary of fetch operation."""
        elapsed = datetime.now() - self.start_time
        
        print("\n" + "="*60)
        print("FETCH SUMMARY")
        print("="*60)
        print(f"⏱️  Total time: {elapsed.total_seconds():.1f}s")
        print(f"✅ Successful networks: {len(self.successful_networks)}")
        print(f"❌ Failed networks: {len(self.failed_networks)}")
        print(f"⏭️  Skipped networks: {len(self.skipped_networks)}")
        
        if self.partial_failures:
            print(f"⚠️  Networks with partial failures: {len(self.partial_failures)}")
            for network_key, failure_info in self.partial_failures.items():
                success_rate = failure_info['success_rate'] * 100
                print(f"   - {failure_info['network']}: {success_rate:.1f}% success rate")
        
        if self.failed_networks:
            print("\nFailed Networks:")
            for failure in self.failed_networks:
                print(f"   - {failure['name']}: {failure['error']}")
        
        if self.skipped_networks:
            print("\nSkipped Networks:")
            for skip in self.skipped_networks:
                print(f"   - {skip['name']}: {skip['reason']}")
        
        print("="*60)
    
    def get_fetch_report(self) -> Dict[str, Any]:
        """
        Get detailed report of fetch operation.
        
        Returns:
            Dictionary with fetch statistics and health information
        """
        elapsed = datetime.now() - self.start_time
        
        return {
            "fetch_summary": {
                "start_time": self.start_time.isoformat(),
                "duration_seconds": elapsed.total_seconds(),
                "successful_networks": len(self.successful_networks),
                "failed_networks": len(self.failed_networks),
                "skipped_networks": len(self.skipped_networks),
                "partial_failures": len(self.partial_failures)
            },
            "successful_networks": self.successful_networks,
            "failed_networks": self.failed_networks,
            "skipped_networks": self.skipped_networks,
            "partial_failures": self.partial_failures,
            "health_summary": get_network_health_summary()
        }
    
    def save_fetch_report(self, filepath: str):
        """
        Save fetch report to file.
        
        Args:
            filepath: Path to save the report
        """
        import json
        
        report = self.get_fetch_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Fetch report saved to {filepath}")
    
    def create_github_notification(self) -> str:
        """
        Create GitHub Actions notification for the fetch operation.
        
        Returns:
            Formatted notification message
        """
        health_summary = get_network_health_summary()
        base_message = create_github_actions_notification(health_summary)
        
        # Add fetch-specific information
        total_networks = len(self.successful_networks) + len(self.failed_networks) + len(self.skipped_networks)
        success_rate = len(self.successful_networks) / max(total_networks, 1) * 100
        
        fetch_info = f"\n\n📊 Fetch Results: {len(self.successful_networks)}/{total_networks} networks successful ({success_rate:.1f}%)"
        
        if self.partial_failures:
            fetch_info += f"\n⚠️  {len(self.partial_failures)} networks had partial failures"
        
        return base_message + fetch_info


def fetch_aave_data_gracefully(max_failures: int = 5, save_reports: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main function to fetch Aave V3 data with graceful degradation.
    
    Args:
        max_failures: Maximum network failures before stopping
        save_reports: Whether to save health and fetch reports
        
    Returns:
        Tuple of (data_dict, fetch_report)
    """
    fetcher = GracefulDataFetcher()
    
    try:
        # Fetch data from all networks
        data = fetcher.fetch_all_networks_data(max_failures)
        
        # Save reports if requested
        if save_reports:
            fetcher.save_fetch_report('fetch_report.json')
            # Health report will be saved by main script
        
        # Get fetch report
        fetch_report = fetcher.get_fetch_report()
        
        return data, fetch_report
        
    except Exception as e:
        print(f"❌ Critical error during data fetch: {e}")
        
        # Still try to save reports for debugging
        if save_reports:
            try:
                fetcher.save_fetch_report('fetch_report_error.json')
                # Health report will be saved by main script
            except Exception:
                pass
        
        raise


if __name__ == "__main__":
    # Test the graceful fetcher
    try:
        data, report = fetch_aave_data_gracefully()
        print(f"\n🎉 Successfully fetched data from {len(data)} networks")
        
        # Print GitHub notification
        fetcher = GracefulDataFetcher()
        fetcher.successful_networks = list(data.keys())
        notification = fetcher.create_github_notification()
        print(f"\n📢 GitHub Notification:\n{notification}")
        
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        sys.exit(1)