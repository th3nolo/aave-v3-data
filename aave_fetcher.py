#!/usr/bin/env python3
"""
Aave V3 Data Fetcher - Main script with performance optimization and parallel processing.
Fetches Aave V3 protocol data from multiple blockchain networks efficiently.
"""

import sys
import os
import time
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from networks import get_active_networks, validate_all_networks, get_fallback_urls
from graceful_fetcher import fetch_aave_data_gracefully, GracefulDataFetcher
from json_output import save_json_output, validate_json_schema
from html_output import save_html_output
from monitoring import (
    get_network_health_summary, save_health_report, health_monitor, profiler,
    save_performance_report, save_debug_report, print_performance_summary,
    configure_debug_logging, log_network_summary
)
from validation import validate_aave_data, save_validation_report, create_validation_summary_for_github
from utils import get_reserves, get_asset_symbol, get_reserve_data
from ultra_fast_fetcher import fetch_aave_data_ultra_fast
from governance_monitoring import governance_monitor, save_governance_report, validate_against_governance_snapshots
from governance_html_output import save_governance_html_output


class PerformanceMonitor:
    """Monitor and report performance metrics during execution."""
    
    def __init__(self):
        self.start_time = time.time()
        self.network_times = {}
        self.total_assets = 0
        self.total_rpc_calls = 0
        self.github_actions_limit = 600  # 10 minutes in seconds
    
    def start_network(self, network_key: str):
        """Record start time for a network."""
        self.network_times[network_key] = {'start': time.time()}
    
    def finish_network(self, network_key: str, asset_count: int):
        """Record completion time and asset count for a network."""
        if network_key in self.network_times:
            self.network_times[network_key]['end'] = time.time()
            self.network_times[network_key]['duration'] = (
                self.network_times[network_key]['end'] - 
                self.network_times[network_key]['start']
            )
            self.network_times[network_key]['assets'] = asset_count
            self.total_assets += asset_count
    
    def get_elapsed_time(self) -> float:
        """Get total elapsed time in seconds."""
        return time.time() - self.start_time
    
    def is_approaching_limit(self, buffer_seconds: int = 60) -> bool:
        """Check if we're approaching GitHub Actions time limit."""
        return self.get_elapsed_time() > (self.github_actions_limit - buffer_seconds)
    
    def print_performance_report(self):
        """Print detailed performance report."""
        total_time = self.get_elapsed_time()
        
        print("\n" + "="*70)
        print("PERFORMANCE REPORT")
        print("="*70)
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print(f"📊 Total assets processed: {self.total_assets}")
        print(f"🌐 Networks processed: {len(self.network_times)}")
        
        if self.total_assets > 0:
            print(f"⚡ Average time per asset: {total_time / self.total_assets:.2f}s")
        
        # GitHub Actions compliance
        if total_time < 300:  # 5 minutes
            print("✅ Excellent performance - well under GitHub Actions limits")
        elif total_time < 480:  # 8 minutes
            print("✅ Good performance - within GitHub Actions limits")
        elif total_time < 540:  # 9 minutes
            print("⚠️  Approaching GitHub Actions time limit")
        else:
            print("🔴 Exceeding recommended GitHub Actions time limit")
        
        # Network breakdown
        if self.network_times:
            print("\nNetwork Performance:")
            sorted_networks = sorted(
                self.network_times.items(),
                key=lambda x: x[1].get('duration', 0),
                reverse=True
            )
            
            for network_key, timing in sorted_networks:
                duration = timing.get('duration', 0)
                assets = timing.get('assets', 0)
                if assets > 0:
                    avg_time = duration / assets
                    print(f"  {network_key:12} {duration:6.1f}s ({assets:3d} assets, {avg_time:.2f}s/asset)")
                else:
                    print(f"  {network_key:12} {duration:6.1f}s (failed)")
        
        print("="*70)


def fetch_network_data_parallel(network_key: str, network_config: Dict, performance_monitor: PerformanceMonitor) -> Tuple[str, Optional[List[Dict]]]:
    """
    Fetch data for a single network (designed for parallel execution) with enhanced monitoring.
    
    Args:
        network_key: Network identifier
        network_config: Network configuration
        performance_monitor: Performance monitoring instance
        
    Returns:
        Tuple of (network_key, asset_data_list)
    """
    performance_monitor.start_network(network_key)
    
    # Start monitoring for this network
    network_metrics = health_monitor.start_network_monitoring(network_key, network_config['name'])
    
    try:
        print(f"🔄 Starting {network_config['name']}...")
        
        # Use graceful fetcher for individual network
        fetcher = GracefulDataFetcher()
        
        with profiler.profile_operation(f"fetch_network_{network_key}"):
            network_data = fetcher.fetch_network_data(network_key, network_config)
        
        if network_data:
            asset_count = len(network_data)
            performance_monitor.finish_network(network_key, asset_count)
            health_monitor.finish_network_monitoring(network_key, asset_count)
            
            duration = performance_monitor.network_times[network_key]['duration']
            print(f"✅ {network_config['name']}: {asset_count} assets ({duration:.1f}s)")
            
            # Log network summary
            log_network_summary(
                network_key, 
                network_config['name'], 
                asset_count, 
                duration,
                network_metrics.total_rpc_calls,
                network_metrics.success_rate
            )
            
            return network_key, network_data
        else:
            performance_monitor.finish_network(network_key, 0)
            health_monitor.finish_network_monitoring(network_key, 0)
            print(f"❌ {network_config['name']}: No data returned")
            return network_key, None
            
    except Exception as e:
        performance_monitor.finish_network(network_key, 0)
        health_monitor.finish_network_monitoring(network_key, 0)
        print(f"❌ {network_config['name']}: {str(e)}")
        
        # Log the error
        if network_key in health_monitor.network_metrics:
            health_monitor.network_metrics[network_key].errors.append(str(e))
        
        return network_key, None


def fetch_data_with_parallel_processing(max_workers: int = 4, timeout_per_network: int = 120) -> Tuple[Dict[str, List[Dict]], Dict[str, Any]]:
    """
    Fetch data from all networks using parallel processing with performance optimizations.
    
    Args:
        max_workers: Maximum number of concurrent network fetches
        timeout_per_network: Timeout per network in seconds
        
    Returns:
        Tuple of (data_dict, performance_report)
    """
    from network_prioritization import (
        get_prioritized_networks, get_worker_allocation, 
        record_network_performance, get_execution_strategy
    )
    from performance_cache import performance_cache
    
    performance_monitor = PerformanceMonitor()
    networks = get_active_networks()
    all_data = {}
    
    # Get execution strategy based on time constraints
    strategy = get_execution_strategy(0, 540, networks)  # 9 minute limit for safety
    
    print(f"🚀 Starting {strategy['mode']} data fetch from {len(networks)} networks")
    print(f"   Strategy: {strategy['max_workers']} max workers, {strategy['timeout_multiplier']:.1f}x timeout")
    
    # Get prioritized networks
    prioritized_networks = get_prioritized_networks(networks)
    
    # Allocate workers based on network priority
    worker_allocation = get_worker_allocation(strategy['max_workers'], networks)
    
    # Use ThreadPoolExecutor for I/O-bound network operations
    with ThreadPoolExecutor(max_workers=strategy['max_workers']) as executor:
        # Submit network fetch tasks with priority-based allocation
        future_to_network = {}
        
        for network_key, network_config, priority in prioritized_networks:
            # Skip if strategy says critical only and this isn't critical
            if strategy['mode'] == 'critical_only' and priority.tier.value > 1:
                continue
            
            # Calculate adjusted timeout
            adjusted_timeout = timeout_per_network * strategy['timeout_multiplier'] * priority.timeout_multiplier
            
            future = executor.submit(
                fetch_network_data_parallel_optimized, 
                network_key, 
                network_config, 
                performance_monitor,
                adjusted_timeout,
                priority
            )
            future_to_network[future] = network_key
        
        # Process completed tasks
        total_timeout = timeout_per_network * len(future_to_network) * strategy['timeout_multiplier']
        
        for future in as_completed(future_to_network, timeout=total_timeout):
            network_key = future_to_network[future]
            
            try:
                result_network_key, network_data, execution_time = future.result(timeout=timeout_per_network)
                
                if network_data:
                    all_data[result_network_key] = network_data
                    record_network_performance(result_network_key, execution_time, True)
                else:
                    record_network_performance(result_network_key, execution_time, False)
                
                # Check if we're approaching time limits
                if performance_monitor.is_approaching_limit():
                    print("⚠️  Approaching time limit - may cancel remaining networks")
                    break
                    
            except Exception as e:
                print(f"❌ Network {network_key} failed with exception: {e}")
                record_network_performance(network_key, timeout_per_network, False)
                continue
    
    # Save cache after processing
    performance_cache.save()
    
    # Create performance report
    performance_report = {
        "total_time": performance_monitor.get_elapsed_time(),
        "total_assets": performance_monitor.total_assets,
        "networks_processed": len(performance_monitor.network_times),
        "successful_networks": len(all_data),
        "network_timings": performance_monitor.network_times,
        "github_actions_compliant": performance_monitor.get_elapsed_time() < 540,
        "execution_strategy": strategy['mode'],
        "cache_stats": performance_cache.get_cache_stats()
    }
    
    performance_monitor.print_performance_report()
    
    return all_data, performance_report


def fetch_network_data_parallel_optimized(
    network_key: str, 
    network_config: Dict, 
    performance_monitor: PerformanceMonitor,
    timeout: float,
    priority
) -> Tuple[str, Optional[List[Dict]], float]:
    """
    Optimized network data fetching with caching and prioritization.
    
    Args:
        network_key: Network identifier
        network_config: Network configuration
        performance_monitor: Performance monitoring instance
        timeout: Network timeout
        priority: Network priority configuration
        
    Returns:
        Tuple of (network_key, asset_data_list, execution_time)
    """
    from performance_cache import (
        get_cached_reserve_list, cache_reserve_list,
        get_cached_symbol, cache_symbol
    )
    
    start_time = time.time()
    performance_monitor.start_network(network_key)
    
    # Start monitoring for this network
    network_metrics = health_monitor.start_network_monitoring(network_key, network_config['name'])
    
    try:
        print(f"🔄 Starting {network_config['name']} (Priority: {priority.tier.name})...")
        
        # Try to get cached reserve list first
        reserves = get_cached_reserve_list(network_key)
        
        if not reserves:
            # Use graceful fetcher for individual network
            fetcher = GracefulDataFetcher()
            
            with profiler.profile_operation(f"fetch_reserves_{network_key}"):
                reserves = get_reserves(
                    network_config['pool'], 
                    network_config['rpc'], 
                    get_fallback_urls(network_config),
                    network_key
                )
            
            if reserves:
                # Cache the reserve list
                cache_reserve_list(network_key, reserves, priority.weight)
        
        if not reserves:
            execution_time = time.time() - start_time
            performance_monitor.finish_network(network_key, 0)
            health_monitor.finish_network_monitoring(network_key, 0)
            print(f"❌ {network_config['name']}: No reserves found")
            return network_key, None, execution_time
        
        # Fetch network data with caching
        with profiler.profile_operation(f"fetch_network_{network_key}"):
            fetcher = GracefulDataFetcher()
            network_data = fetcher.fetch_network_data(network_key, network_config)
        
        execution_time = time.time() - start_time
        
        if network_data:
            asset_count = len(network_data)
            performance_monitor.finish_network(network_key, asset_count)
            health_monitor.finish_network_monitoring(network_key, asset_count)
            
            # Cache symbols for future use
            for asset in network_data:
                if 'symbol' in asset and 'asset_address' in asset:
                    cache_symbol(asset['asset_address'], asset['symbol'], network_key)
            
            duration = performance_monitor.network_times[network_key]['duration']
            print(f"✅ {network_config['name']}: {asset_count} assets ({duration:.1f}s)")
            
            # Log network summary
            log_network_summary(
                network_key, 
                network_config['name'], 
                asset_count, 
                duration,
                network_metrics.total_rpc_calls,
                network_metrics.success_rate
            )
            
            return network_key, network_data, execution_time
        else:
            performance_monitor.finish_network(network_key, 0)
            health_monitor.finish_network_monitoring(network_key, 0)
            print(f"❌ {network_config['name']}: No data returned")
            return network_key, None, execution_time
            
    except Exception as e:
        execution_time = time.time() - start_time
        performance_monitor.finish_network(network_key, 0)
        health_monitor.finish_network_monitoring(network_key, 0)
        print(f"❌ {network_config['name']}: {str(e)}")
        
        # Log the error
        if network_key in health_monitor.network_metrics:
            health_monitor.network_metrics[network_key].errors.append(str(e))
        
        return network_key, None, execution_time


def run_comprehensive_validation(data: Dict[str, List[Dict]], save_report: bool = True) -> Tuple[bool, str]:
    """
    Run comprehensive data validation and return results.
    
    Args:
        data: Fetched network data
        save_report: Whether to save validation report to file
        
    Returns:
        Tuple of (is_valid, summary_message)
    """
    print("🔍 Running comprehensive data validation...")
    
    # Run validation
    validation_result = validate_aave_data(data, verbose=False)
    
    # Print summary
    summary = validation_result.get_summary()
    print(f"   ✅ Passed: {validation_result.passed_checks}/{validation_result.total_checks} checks")
    print(f"   📊 Success rate: {summary['success_rate']:.1%}")
    
    if validation_result.errors:
        print(f"   ❌ Errors: {len(validation_result.errors)}")
        # Show first few errors
        for error in validation_result.errors[:3]:
            print(f"      {error}")
        if len(validation_result.errors) > 3:
            print(f"      ... and {len(validation_result.errors) - 3} more errors")
    
    if validation_result.warnings:
        print(f"   ⚠️  Warnings: {len(validation_result.warnings)}")
        # Show first few warnings
        for warning in validation_result.warnings[:3]:
            print(f"      {warning}")
        if len(validation_result.warnings) > 3:
            print(f"      ... and {len(validation_result.warnings) - 3} more warnings")
    
    # Save validation report if requested
    if save_report:
        try:
            save_validation_report(validation_result, 'validation_report.json')
        except Exception as e:
            print(f"⚠️  Failed to save validation report: {e}")
    
    # Create summary for return
    github_summary = create_validation_summary_for_github(validation_result)
    
    return validation_result.is_valid(), github_summary


def main():
    """Main entry point for the Aave V3 data fetcher with comprehensive monitoring and debugging."""
    parser = argparse.ArgumentParser(description='Aave V3 Data Fetcher with Performance Optimization and Monitoring')
    parser.add_argument('--turbo', action='store_true', help='🚀 TURBO MODE: Ultra-fast multicall3 + max parallel execution (best performance)')
    parser.add_argument('--ultra-fast', action='store_true', help='Use ultra-fast mode with Multicall3 (recommended)')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--sequential', action='store_true', help='Use sequential processing')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum concurrent workers (default: 4)')
    parser.add_argument('--output-json', default='aave_v3_data.json', help='JSON output file')
    parser.add_argument('--output-html', default='aave_v3_data.html', help='HTML output file')
    parser.add_argument('--validate', action='store_true', help='Validate data against known values')
    parser.add_argument('--skip-reports', action='store_true', help='Skip saving health/fetch reports')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout per network in seconds')
    
    # New monitoring and debugging arguments
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--log-file', help='Save logs to file')
    parser.add_argument('--save-debug-report', action='store_true', help='Save comprehensive debug report')
    parser.add_argument('--save-performance-report', action='store_true', help='Save detailed performance report')
    parser.add_argument('--include-rpc-history', action='store_true', help='Include RPC call history in debug report')
    parser.add_argument('--validate-freshness', action='store_true', help='Validate data freshness and timestamps')
    
    # Governance monitoring arguments
    parser.add_argument('--monitor-governance', action='store_true', help='Enable governance monitoring and parameter tracking')
    parser.add_argument('--governance-alerts', action='store_true', help='Generate alerts for critical parameter changes')
    parser.add_argument('--validate-governance', action='store_true', help='Validate data against governance snapshots')
    
    args = parser.parse_args()
    
    # Configure logging and monitoring
    configure_debug_logging(args.debug, args.log_file)
    
    print("🚀 Aave V3 Data Fetcher - Performance Optimized with Monitoring")
    print("=" * 70)
    
    if args.debug:
        print("🔍 Debug logging enabled")
    if args.log_file:
        print(f"📝 Logging to file: {args.log_file}")
    if args.save_debug_report:
        print("🐛 Debug report will be saved")
    if args.save_performance_report:
        print("📊 Performance report will be saved")
    
    # Validate network configurations
    print("🔍 Validating network configurations...")
    is_valid, validation_errors = validate_all_networks()
    if not is_valid:
        print("❌ Network configuration validation failed:")
        for network, errors in validation_errors.items():
            for error in errors:
                print(f"   {network}: {error}")
        return 1
    print("✅ Network configurations valid")
    
    # Choose fetching strategy
    try:
        if args.turbo:
            print("🚀🚀 TURBO MODE ACTIVATED - Maximum performance!")
            print("   ⚡ Ultra-fast Multicall3 optimization")
            print("   ⚡ Maximum parallel execution")
            data, fetch_report = fetch_aave_data_ultra_fast(
                max_network_workers=12,  # Max parallel for turbo mode
                save_reports=not args.skip_reports
            )
            performance_report = fetch_report.get('fetch_summary', {})
        elif args.ultra_fast:
            print("⚡⚡ Using ULTRA-FAST mode with Multicall3 optimization")
            data, fetch_report = fetch_aave_data_ultra_fast(
                max_network_workers=args.max_workers if args.max_workers > 4 else 8,
                save_reports=not args.skip_reports
            )
            performance_report = fetch_report.get('fetch_summary', {})
        elif args.sequential:
            print("🔄 Using sequential processing with graceful degradation")
            data, fetch_report = fetch_aave_data_gracefully(
                max_failures=5,
                save_reports=not args.skip_reports
            )
            performance_report = fetch_report.get('fetch_summary', {})
        else:
            # Default to parallel processing
            print(f"⚡ Using parallel processing with {args.max_workers} workers")
            data, performance_report = fetch_data_with_parallel_processing(
                max_workers=args.max_workers,
                timeout_per_network=args.timeout
            )
        
        if not data:
            print("❌ No data fetched from any network")
            return 1
        
        print(f"\n✅ Successfully fetched data from {len(data)} networks")
        
        # Run comprehensive data validation
        validation_passed = True
        validation_summary = ""
        
        if args.validate:
            validation_passed, validation_summary = run_comprehensive_validation(
                data, 
                save_report=not args.skip_reports
            )
            
            if not validation_passed:
                print("❌ Data validation failed - check validation_report.json for details")
            else:
                print("✅ Data validation passed")
        else:
            # Always run basic validation even if --validate not specified
            print("🔍 Running basic data validation...")
            validation_result = validate_aave_data(data, verbose=False)
            validation_passed = validation_result.is_valid()
            validation_summary = create_validation_summary_for_github(validation_result)
            
            if validation_result.errors:
                print(f"⚠️  Found {len(validation_result.errors)} validation errors")
            if validation_result.warnings:
                print(f"⚠️  Found {len(validation_result.warnings)} validation warnings")
        
        # Run governance monitoring if requested
        governance_report = None
        if args.monitor_governance or args.governance_alerts:
            print("\n🏛️  Running governance monitoring...")
            try:
                governance_report = governance_monitor.run_governance_monitoring(data)
                
                # Save governance report if not skipping reports
                if not args.skip_reports:
                    save_governance_report(governance_report, 'governance_monitoring_report.json')
                
                # Show governance summary
                summary = governance_report.get('summary', {})
                if summary.get('critical_changes', 0) > 0:
                    print(f"🔴 CRITICAL: {summary['critical_changes']} critical parameter changes detected!")
                if summary.get('high_risk_changes', 0) > 0:
                    print(f"🟠 HIGH RISK: {summary['high_risk_changes']} high-risk parameter changes detected!")
                if summary.get('critical_alerts', 0) > 0:
                    print(f"🚨 {summary['critical_alerts']} critical alerts generated!")
                
            except Exception as e:
                print(f"⚠️  Governance monitoring failed: {e}")
        
        # Validate against governance snapshots if requested
        governance_validation = None
        if args.validate_governance:
            print("\n🏛️  Validating against governance snapshots...")
            try:
                governance_validation = validate_against_governance_snapshots(data)
                
                if not governance_validation['validation_passed']:
                    print(f"❌ Governance validation failed - {len(governance_validation['validation_errors'])} errors found")
                    for error in governance_validation['validation_errors'][:3]:
                        print(f"   {error}")
                    if len(governance_validation['validation_errors']) > 3:
                        print(f"   ... and {len(governance_validation['validation_errors']) - 3} more errors")
                else:
                    print(f"✅ Governance validation passed - consistency score: {governance_validation['governance_consistency_score']:.1%}")
                
                # Save governance validation report if not skipping reports
                if not args.skip_reports:
                    with open('governance_validation_report.json', 'w') as f:
                        json.dump(governance_validation, f, indent=2, default=str)
                    print("📊 Governance validation report saved")
                
            except Exception as e:
                print(f"⚠️  Governance validation failed: {e}")
        
        # Generate governance HTML output if governance monitoring was run
        if governance_report and not args.skip_reports:
            print("\n📄 Generating governance HTML output...")
            try:
                html_success = save_governance_html_output(
                    governance_report, 
                    governance_validation,
                    'governance_monitoring.html'
                )
                
                if html_success:
                    print("✅ Governance HTML page generated successfully")
                    print("   🌐 Available at: governance_monitoring.html")
                else:
                    print("❌ Failed to generate governance HTML page")
                
            except Exception as e:
                print(f"⚠️  Governance HTML generation failed: {e}")
        
        # Validate data freshness if requested
        if args.validate_freshness:
            print("🕒 Validating data freshness...")
            freshness_info = health_monitor.validate_data_freshness(data)
            
            print(f"   📊 Freshness score: {freshness_info.freshness_score:.1%}")
            print(f"   ✅ Fresh networks: {freshness_info.networks_with_fresh_data}")
            print(f"   ⚠️  Stale networks: {freshness_info.networks_with_stale_data}")
            
            if freshness_info.stale_networks:
                print(f"   🔍 Stale networks: {', '.join(freshness_info.stale_networks)}")
            
            if freshness_info.validation_errors:
                print(f"   ❌ Freshness validation errors: {len(freshness_info.validation_errors)}")
            
            if freshness_info.validation_warnings:
                print(f"   ⚠️  Freshness validation warnings: {len(freshness_info.validation_warnings)}")
            
            # Save freshness report if not skipping reports
            if not args.skip_reports:
                try:
                    freshness_report = {
                        "timestamp": freshness_info.timestamp.isoformat(),
                        "freshness_score": freshness_info.freshness_score,
                        "networks_checked": freshness_info.networks_checked,
                        "networks_with_fresh_data": freshness_info.networks_with_fresh_data,
                        "networks_with_stale_data": freshness_info.networks_with_stale_data,
                        "stale_networks": freshness_info.stale_networks,
                        "validation_errors": freshness_info.validation_errors,
                        "validation_warnings": freshness_info.validation_warnings,
                        "oldest_data_age_hours": freshness_info.oldest_data_age.total_seconds() / 3600 if freshness_info.oldest_data_age else None,
                        "newest_data_age_hours": freshness_info.newest_data_age.total_seconds() / 3600 if freshness_info.newest_data_age else None
                    }
                    
                    with open('freshness_report.json', 'w') as f:
                        json.dump(freshness_report, f, indent=2)
                    
                    print("📊 Freshness report saved to freshness_report.json")
                    
                except Exception as e:
                    print(f"⚠️  Failed to save freshness report: {e}")
        
        # Validate JSON schema
        print("\n📋 Validating JSON schema...")
        schema_errors = validate_json_schema(data)
        if schema_errors:
            print("❌ JSON schema validation failed:")
            for error in schema_errors[:5]:  # Limit to first 5 errors
                print(f"   {error}")
            return 1
        print("✅ JSON schema validation passed")
        
        # Save outputs
        print(f"\n💾 Saving outputs...")
        
        # Save JSON output
        json_success = save_json_output(
            data, 
            args.output_json,
            fetch_report=performance_report if 'fetch_summary' in str(performance_report) else None,
            include_metadata=True
        )
        
        # Save HTML output
        html_success = save_html_output(
            data,
            args.output_html,
            fetch_report=performance_report if 'fetch_summary' in str(performance_report) else None
        )
        
        if not (json_success and html_success):
            print("❌ Failed to save some outputs")
            return 1
        
        # Save health report if not skipped
        if not args.skip_reports:
            try:
                save_health_report('health_report.json')
                print("📊 Health report saved")
            except Exception as e:
                print(f"⚠️  Failed to save health report: {e}")
        
        # Save performance report if requested
        if args.save_performance_report or not args.skip_reports:
            try:
                save_performance_report('performance_report.json')
                print("📊 Performance report saved")
            except Exception as e:
                print(f"⚠️  Failed to save performance report: {e}")
        
        # Save debug report if requested
        if args.save_debug_report:
            try:
                save_debug_report('debug_report.json', args.include_rpc_history)
                print("🐛 Debug report saved")
            except Exception as e:
                print(f"⚠️  Failed to save debug report: {e}")
        
        # Print performance summary
        if args.debug or args.save_performance_report:
            print_performance_summary()
        
        # Final summary
        total_assets = sum(len(assets) for assets in data.values())
        execution_time = performance_report.get('total_time', 0)
        
        print(f"\n🎉 Execution completed successfully!")
        print(f"   📊 {len(data)} networks, {total_assets} assets")
        print(f"   ⏱️  {execution_time:.1f}s execution time")
        print(f"   📄 JSON: {args.output_json}")
        print(f"   🌐 HTML: {args.output_html}")
        
        # Show governance outputs if generated
        if governance_report and not args.skip_reports:
            print(f"   🏛️  Governance HTML: governance_monitoring.html")
            print(f"   📊 Governance JSON: governance_monitoring_report.json")
        
        # Show monitoring summary
        if len(health_monitor.network_metrics) > 0:
            total_rpc_calls = sum(m.total_rpc_calls for m in health_monitor.network_metrics.values())
            successful_calls = sum(m.successful_rpc_calls for m in health_monitor.network_metrics.values())
            success_rate = successful_calls / max(total_rpc_calls, 1)
            
            print(f"   📡 {total_rpc_calls} RPC calls, {success_rate:.1%} success rate")
            
            if success_rate < 0.9:
                print("⚠️  Warning: Low RPC success rate detected")
        
        # GitHub Actions compliance check
        if execution_time > 540:  # 9 minutes
            print("⚠️  Warning: Execution time approaching GitHub Actions limits")
            return 2  # Warning exit code
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)