"""
Monitoring and health check functionality for RPC endpoints and network operations.
Provides graceful degradation, automatic failover, comprehensive logging, and debugging capabilities.
"""

import time
import json
import logging
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager

from utils import rpc_call_with_retry, RPCError, NetworkError
from networks import get_fallback_urls


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up comprehensive logging for the Aave V3 data fetcher.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('aave_fetcher')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always debug level for file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create file handler for {log_file}: {e}")
    
    return logger


# Global logger instance
logger = setup_logging()


@dataclass
class RPCCallMetrics:
    """Metrics for individual RPC calls."""
    url: str
    method: str
    params: List[Any]
    start_time: float
    end_time: Optional[float]
    success: bool
    response_size: Optional[int]
    error: Optional[str]
    retry_count: int
    
    @property
    def duration(self) -> Optional[float]:
        """Get call duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class NetworkMetrics:
    """Performance metrics for a network."""
    network_key: str
    network_name: str
    start_time: float
    end_time: Optional[float]
    total_rpc_calls: int
    successful_rpc_calls: int
    failed_rpc_calls: int
    total_assets_processed: int
    total_response_size: int
    rpc_call_history: List[RPCCallMetrics]
    errors: List[str]
    warnings: List[str]
    
    @property
    def duration(self) -> Optional[float]:
        """Get network processing duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Get RPC call success rate."""
        if self.total_rpc_calls == 0:
            return 0.0
        return self.successful_rpc_calls / self.total_rpc_calls
    
    @property
    def average_rpc_time(self) -> float:
        """Get average RPC call time in seconds."""
        successful_calls = [call for call in self.rpc_call_history if call.success and call.duration]
        if not successful_calls:
            return 0.0
        return sum(call.duration for call in successful_calls) / len(successful_calls)


@dataclass
class DataFreshnessInfo:
    """Information about data freshness and validation."""
    timestamp: datetime
    networks_checked: int
    networks_with_fresh_data: int
    networks_with_stale_data: int
    oldest_data_age: Optional[timedelta]
    newest_data_age: Optional[timedelta]
    stale_networks: List[str]
    validation_errors: List[str]
    validation_warnings: List[str]
    
    @property
    def freshness_score(self) -> float:
        """Get data freshness score (0.0 to 1.0)."""
        if self.networks_checked == 0:
            return 0.0
        return self.networks_with_fresh_data / self.networks_checked


class PerformanceProfiler:
    """Profile performance of different operations."""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.current_operations: Dict[str, float] = {}
    
    @contextmanager
    def profile_operation(self, operation_name: str):
        """Context manager to profile an operation."""
        start_time = time.time()
        self.current_operations[operation_name] = start_time
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            
            self.operation_times[operation_name].append(duration)
            self.current_operations.pop(operation_name, None)
            
            logger.debug(f"Operation '{operation_name}' completed in {duration:.3f}s")
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        times = self.operation_times.get(operation_name, [])
        if not times:
            return {}
        
        return {
            'count': len(times),
            'total_time': sum(times),
            'average_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {op: self.get_operation_stats(op) for op in self.operation_times.keys()}


# Global profiler instance
profiler = PerformanceProfiler()


@dataclass
class EndpointHealth:
    """Health status of an RPC endpoint."""
    url: str
    is_healthy: bool
    last_check: datetime
    response_time: Optional[float]  # in seconds
    error_count: int
    success_count: int
    last_error: Optional[str]
    consecutive_failures: int


@dataclass
class NetworkHealth:
    """Health status of a network including all its endpoints."""
    network_key: str
    network_name: str
    primary_endpoint: EndpointHealth
    fallback_endpoints: List[EndpointHealth]
    overall_health: str  # "healthy", "degraded", "unhealthy"
    last_successful_call: Optional[datetime]
    total_requests: int
    failed_requests: int


class HealthMonitor:
    """Monitor and track health of RPC endpoints with comprehensive logging and debugging."""
    
    def __init__(self):
        self.endpoint_health: Dict[str, EndpointHealth] = {}
        self.network_health: Dict[str, NetworkHealth] = {}
        self.network_metrics: Dict[str, NetworkMetrics] = {}
        self.health_check_interval = 300  # 5 minutes
        self.max_consecutive_failures = 3
        self.response_time_threshold = 10.0  # seconds
        self.data_freshness_threshold = timedelta(hours=2)  # Data older than 2 hours is stale
        
        logger.info("HealthMonitor initialized with response time threshold: %.1fs", self.response_time_threshold)
    
    def start_network_monitoring(self, network_key: str, network_name: str) -> NetworkMetrics:
        """
        Start monitoring a network's performance.
        
        Args:
            network_key: Network identifier
            network_name: Human-readable network name
            
        Returns:
            NetworkMetrics object for tracking
        """
        metrics = NetworkMetrics(
            network_key=network_key,
            network_name=network_name,
            start_time=time.time(),
            end_time=None,
            total_rpc_calls=0,
            successful_rpc_calls=0,
            failed_rpc_calls=0,
            total_assets_processed=0,
            total_response_size=0,
            rpc_call_history=[],
            errors=[],
            warnings=[]
        )
        
        self.network_metrics[network_key] = metrics
        logger.info(f"Started monitoring network: {network_name} ({network_key})")
        
        return metrics
    
    def record_rpc_call(self, network_key: str, url: str, method: str, params: List[Any], 
                       start_time: float, end_time: float, success: bool, 
                       response_size: Optional[int] = None, error: Optional[str] = None, 
                       retry_count: int = 0):
        """
        Record details of an RPC call for monitoring and debugging.
        
        Args:
            network_key: Network identifier
            url: RPC endpoint URL
            method: RPC method name
            params: RPC parameters
            start_time: Call start time
            end_time: Call end time
            success: Whether the call was successful
            response_size: Size of response in bytes
            error: Error message if call failed
            retry_count: Number of retries attempted
        """
        call_metrics = RPCCallMetrics(
            url=url,
            method=method,
            params=params,
            start_time=start_time,
            end_time=end_time,
            success=success,
            response_size=response_size,
            error=error,
            retry_count=retry_count
        )
        
        if network_key in self.network_metrics:
            metrics = self.network_metrics[network_key]
            metrics.rpc_call_history.append(call_metrics)
            metrics.total_rpc_calls += 1
            
            if success:
                metrics.successful_rpc_calls += 1
                if response_size:
                    metrics.total_response_size += response_size
            else:
                metrics.failed_rpc_calls += 1
                if error:
                    metrics.errors.append(f"{method}: {error}")
        
        # Log the call
        duration = end_time - start_time
        if success:
            logger.debug(f"RPC call successful: {method} to {url} in {duration:.3f}s")
            if retry_count > 0:
                logger.info(f"RPC call succeeded after {retry_count} retries: {method}")
        else:
            logger.warning(f"RPC call failed: {method} to {url} after {duration:.3f}s - {error}")
            if retry_count > 0:
                logger.error(f"RPC call failed after {retry_count} retries: {method} - {error}")
    
    def finish_network_monitoring(self, network_key: str, assets_processed: int):
        """
        Finish monitoring a network and calculate final metrics.
        
        Args:
            network_key: Network identifier
            assets_processed: Number of assets successfully processed
        """
        if network_key in self.network_metrics:
            metrics = self.network_metrics[network_key]
            metrics.end_time = time.time()
            metrics.total_assets_processed = assets_processed
            
            duration = metrics.duration or 0
            success_rate = metrics.success_rate
            avg_rpc_time = metrics.average_rpc_time
            
            logger.info(
                f"Network monitoring completed: {metrics.network_name} - "
                f"{assets_processed} assets, {metrics.total_rpc_calls} RPC calls, "
                f"{success_rate:.1%} success rate, {duration:.1f}s total, "
                f"{avg_rpc_time:.3f}s avg RPC time"
            )
            
            if success_rate < 0.9:  # Less than 90% success rate
                logger.warning(f"Low RPC success rate for {metrics.network_name}: {success_rate:.1%}")
            
            if duration > 60:  # More than 1 minute
                logger.warning(f"Slow network processing for {metrics.network_name}: {duration:.1f}s")
    
    def validate_data_freshness(self, data: Dict[str, List[Dict]]) -> DataFreshnessInfo:
        """
        Validate the freshness of fetched data.
        
        Args:
            data: Network data dictionary
            
        Returns:
            DataFreshnessInfo with validation results
        """
        logger.info("Validating data freshness across all networks")
        
        current_time = datetime.now()
        networks_checked = len(data)
        networks_with_fresh_data = 0
        networks_with_stale_data = 0
        stale_networks = []
        validation_errors = []
        validation_warnings = []
        data_ages = []
        
        for network_key, assets in data.items():
            try:
                # Check if network has data
                if not assets:
                    validation_errors.append(f"No data for network: {network_key}")
                    continue
                
                # Check for timestamp fields in asset data
                has_fresh_data = False
                network_data_ages = []
                
                for asset in assets:
                    # Check last_update_timestamp if available
                    if 'last_update_timestamp' in asset and asset['last_update_timestamp']:
                        try:
                            last_update = datetime.fromtimestamp(asset['last_update_timestamp'])
                            data_age = current_time - last_update
                            network_data_ages.append(data_age)
                            
                            if data_age <= self.data_freshness_threshold:
                                has_fresh_data = True
                            
                        except (ValueError, TypeError) as e:
                            validation_warnings.append(
                                f"Invalid timestamp for {asset.get('symbol', 'unknown')} "
                                f"in {network_key}: {e}"
                            )
                
                # Evaluate network freshness
                if has_fresh_data:
                    networks_with_fresh_data += 1
                    logger.debug(f"Network {network_key} has fresh data")
                else:
                    networks_with_stale_data += 1
                    stale_networks.append(network_key)
                    logger.warning(f"Network {network_key} has stale or missing timestamp data")
                
                data_ages.extend(network_data_ages)
                
            except Exception as e:
                validation_errors.append(f"Error validating {network_key}: {str(e)}")
                logger.error(f"Error validating data freshness for {network_key}: {e}")
        
        # Calculate age statistics
        oldest_data_age = max(data_ages) if data_ages else None
        newest_data_age = min(data_ages) if data_ages else None
        
        freshness_info = DataFreshnessInfo(
            timestamp=current_time,
            networks_checked=networks_checked,
            networks_with_fresh_data=networks_with_fresh_data,
            networks_with_stale_data=networks_with_stale_data,
            oldest_data_age=oldest_data_age,
            newest_data_age=newest_data_age,
            stale_networks=stale_networks,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )
        
        # Log summary
        freshness_score = freshness_info.freshness_score
        logger.info(
            f"Data freshness validation completed: {freshness_score:.1%} fresh "
            f"({networks_with_fresh_data}/{networks_checked} networks)"
        )
        
        if validation_errors:
            logger.error(f"Data freshness validation errors: {len(validation_errors)}")
            for error in validation_errors[:3]:  # Log first 3 errors
                logger.error(f"  {error}")
        
        if validation_warnings:
            logger.warning(f"Data freshness validation warnings: {len(validation_warnings)}")
            for warning in validation_warnings[:3]:  # Log first 3 warnings
                logger.warning(f"  {warning}")
        
        return freshness_info
    
    def check_endpoint_health(self, url: str, timeout: int = 10) -> EndpointHealth:
        """
        Check health of a single RPC endpoint.
        
        Args:
            url: RPC endpoint URL
            timeout: Timeout for health check in seconds
            
        Returns:
            EndpointHealth object with current status
        """
        start_time = time.time()
        
        # Get existing health record or create new one
        if url in self.endpoint_health:
            health = self.endpoint_health[url]
        else:
            health = EndpointHealth(
                url=url,
                is_healthy=True,
                last_check=datetime.now(),
                response_time=None,
                error_count=0,
                success_count=0,
                last_error=None,
                consecutive_failures=0
            )
        
        try:
            logger.debug(f"Checking health of endpoint: {url}")
            
            # Simple health check with eth_chainId
            result = rpc_call_with_retry(
                url, 
                'eth_chainId', 
                [],
                max_retries=1  # Single attempt for health check
            )
            
            response_time = time.time() - start_time
            
            if 'result' in result:
                # Successful health check
                health.is_healthy = True
                health.response_time = response_time
                health.success_count += 1
                health.consecutive_failures = 0
                health.last_error = None
                
                logger.debug(f"Endpoint health check passed: {url} ({response_time:.3f}s)")
                
                # Mark as unhealthy if response time is too slow
                if response_time > self.response_time_threshold:
                    health.is_healthy = False
                    health.last_error = f"Slow response: {response_time:.2f}s"
                    logger.warning(f"Endpoint marked unhealthy due to slow response: {url} ({response_time:.2f}s)")
                    
            else:
                # No result in response
                health.is_healthy = False
                health.error_count += 1
                health.consecutive_failures += 1
                health.last_error = "No result in RPC response"
                logger.warning(f"Endpoint health check failed - no result: {url}")
                
        except (RPCError, NetworkError) as e:
            # RPC or network error
            health.is_healthy = False
            health.error_count += 1
            health.consecutive_failures += 1
            health.last_error = str(e)
            health.response_time = time.time() - start_time
            logger.warning(f"Endpoint health check failed - RPC/Network error: {url} - {e}")
            
        except Exception as e:
            # Unexpected error
            health.is_healthy = False
            health.error_count += 1
            health.consecutive_failures += 1
            health.last_error = f"Unexpected error: {str(e)}"
            health.response_time = time.time() - start_time
            logger.error(f"Endpoint health check failed - unexpected error: {url} - {e}")
        
        health.last_check = datetime.now()
        self.endpoint_health[url] = health
        
        return health
    
    def check_network_health(self, network_key: str, network_config: Dict) -> NetworkHealth:
        """
        Check health of all endpoints for a network.
        
        Args:
            network_key: Network identifier
            network_config: Network configuration dictionary
            
        Returns:
            NetworkHealth object with overall network status
        """
        primary_url = network_config['rpc']
        fallback_urls = get_fallback_urls(network_config) or []
        
        # Check primary endpoint
        primary_health = self.check_endpoint_health(primary_url)
        
        # Check fallback endpoints
        fallback_health = []
        for fallback_url in fallback_urls:
            fallback_health.append(self.check_endpoint_health(fallback_url))
        
        # Determine overall network health
        healthy_endpoints = []
        if primary_health.is_healthy:
            healthy_endpoints.append(primary_health)
        healthy_endpoints.extend([h for h in fallback_health if h.is_healthy])
        
        if primary_health.is_healthy:
            overall_health = "healthy"
        elif len(healthy_endpoints) > 0:
            overall_health = "degraded"
        else:
            overall_health = "unhealthy"
        
        # Get existing network health or create new
        if network_key in self.network_health:
            network_health = self.network_health[network_key]
            network_health.primary_endpoint = primary_health
            network_health.fallback_endpoints = fallback_health
            network_health.overall_health = overall_health
        else:
            network_health = NetworkHealth(
                network_key=network_key,
                network_name=network_config.get('name', network_key),
                primary_endpoint=primary_health,
                fallback_endpoints=fallback_health,
                overall_health=overall_health,
                last_successful_call=None,
                total_requests=0,
                failed_requests=0
            )
        
        self.network_health[network_key] = network_health
        return network_health
    
    def get_healthy_endpoints(self, network_key: str, network_config: Dict) -> List[str]:
        """
        Get list of healthy endpoints for a network, ordered by preference.
        
        Args:
            network_key: Network identifier
            network_config: Network configuration
            
        Returns:
            List of healthy endpoint URLs, primary first if healthy
        """
        network_health = self.check_network_health(network_key, network_config)
        
        healthy_urls = []
        
        # Add primary if healthy
        if network_health.primary_endpoint.is_healthy:
            healthy_urls.append(network_health.primary_endpoint.url)
        
        # Add healthy fallbacks, sorted by success rate
        healthy_fallbacks = [
            h for h in network_health.fallback_endpoints 
            if h.is_healthy
        ]
        
        # Sort by success rate (success_count / (success_count + error_count))
        healthy_fallbacks.sort(
            key=lambda h: h.success_count / max(h.success_count + h.error_count, 1),
            reverse=True
        )
        
        healthy_urls.extend([h.url for h in healthy_fallbacks])
        
        # If no healthy endpoints, return all endpoints as last resort
        if not healthy_urls:
            healthy_urls.append(network_config['rpc'])
            fallback_urls = get_fallback_urls(network_config) or []
            healthy_urls.extend(fallback_urls)
        
        return healthy_urls
    
    def record_request_result(self, network_key: str, success: bool, error: Optional[str] = None):
        """
        Record the result of a network request for monitoring.
        
        Args:
            network_key: Network identifier
            success: Whether the request was successful
            error: Error message if request failed
        """
        if network_key in self.network_health:
            network_health = self.network_health[network_key]
            network_health.total_requests += 1
            
            if success:
                network_health.last_successful_call = datetime.now()
            else:
                network_health.failed_requests += 1
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get summary of all network health statuses.
        
        Returns:
            Dictionary with health summary information
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "networks": {},
            "overall_stats": {
                "total_networks": len(self.network_health),
                "healthy_networks": 0,
                "degraded_networks": 0,
                "unhealthy_networks": 0
            }
        }
        
        for network_key, network_health in self.network_health.items():
            summary["networks"][network_key] = {
                "name": network_health.network_name,
                "status": network_health.overall_health,
                "primary_healthy": network_health.primary_endpoint.is_healthy,
                "healthy_fallbacks": len([h for h in network_health.fallback_endpoints if h.is_healthy]),
                "total_fallbacks": len(network_health.fallback_endpoints),
                "success_rate": (
                    (network_health.total_requests - network_health.failed_requests) / 
                    max(network_health.total_requests, 1)
                ),
                "last_successful_call": (
                    network_health.last_successful_call.isoformat() 
                    if network_health.last_successful_call else None
                )
            }
            
            # Update overall stats
            if network_health.overall_health == "healthy":
                summary["overall_stats"]["healthy_networks"] += 1
            elif network_health.overall_health == "degraded":
                summary["overall_stats"]["degraded_networks"] += 1
            else:
                summary["overall_stats"]["unhealthy_networks"] += 1
        
        return summary
    
    def should_skip_network(self, network_key: str) -> Tuple[bool, str]:
        """
        Determine if a network should be skipped due to health issues.
        
        Args:
            network_key: Network identifier
            
        Returns:
            Tuple of (should_skip, reason)
        """
        if network_key not in self.network_health:
            return False, ""
        
        network_health = self.network_health[network_key]
        
        # Skip if all endpoints are unhealthy for too long
        if network_health.overall_health == "unhealthy":
            # Check if we've had recent successful calls
            if network_health.last_successful_call:
                time_since_success = datetime.now() - network_health.last_successful_call
                if time_since_success > timedelta(hours=1):
                    return True, f"No successful calls for {time_since_success}"
            else:
                return True, "No successful calls recorded"
        
        # Skip if failure rate is too high
        if network_health.total_requests > 10:  # Only check if we have enough data
            failure_rate = network_health.failed_requests / network_health.total_requests
            if failure_rate > 0.8:  # 80% failure rate
                return True, f"High failure rate: {failure_rate:.1%}"
        
        return False, ""


# Global health monitor instance
health_monitor = HealthMonitor()


def get_healthy_rpc_urls(network_key: str, network_config: Dict) -> List[str]:
    """
    Get healthy RPC URLs for a network with automatic failover.
    
    Args:
        network_key: Network identifier
        network_config: Network configuration
        
    Returns:
        List of healthy RPC URLs ordered by preference
    """
    return health_monitor.get_healthy_endpoints(network_key, network_config)


def record_network_request(network_key: str, success: bool, error: Optional[str] = None):
    """
    Record the result of a network request for monitoring.
    
    Args:
        network_key: Network identifier
        success: Whether the request was successful
        error: Error message if request failed
    """
    health_monitor.record_request_result(network_key, success, error)


def should_skip_unhealthy_network(network_key: str) -> Tuple[bool, str]:
    """
    Check if a network should be skipped due to health issues.
    
    Args:
        network_key: Network identifier
        
    Returns:
        Tuple of (should_skip, reason)
    """
    return health_monitor.should_skip_network(network_key)


def get_network_health_summary() -> Dict[str, Any]:
    """
    Get summary of all network health statuses.
    
    Returns:
        Dictionary with health summary information
    """
    return health_monitor.get_health_summary()


def save_health_report(filepath: str):
    """
    Save health report to file.
    
    Args:
        filepath: Path to save the health report
    """
    health_summary = get_network_health_summary()
    
    with open(filepath, 'w') as f:
        json.dump(health_summary, f, indent=2)


def log_network_attempt(network_key: str, network_name: str):
    """
    Log an attempt to connect to a network.
    
    Args:
        network_key: Network identifier
        network_name: Human-readable network name
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempting to connect to {network_name} ({network_key})")


def log_network_success(network_key: str, network_name: str, asset_count: int, elapsed_time: float):
    """
    Log successful network data retrieval.
    
    Args:
        network_key: Network identifier
        network_name: Human-readable network name
        asset_count: Number of assets retrieved
        elapsed_time: Time taken in seconds
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {network_name}: Retrieved {asset_count} assets in {elapsed_time:.2f}s")
    record_network_request(network_key, True)


def log_network_failure(network_key: str, network_name: str, error_message: str):
    """
    Log network failure.
    
    Args:
        network_key: Network identifier
        network_name: Human-readable network name
        error_message: Description of the failure
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {network_name}: {error_message}")
    record_network_request(network_key, False, error_message)


def update_rpc_latency(url: str, latency: float):
    """
    Update RPC endpoint latency measurement.
    
    Args:
        url: RPC endpoint URL
        latency: Response time in seconds
    """
    if url in health_monitor.endpoint_health:
        health_monitor.endpoint_health[url].response_time = latency


def get_performance_report() -> Dict[str, Any]:
    """
    Get comprehensive performance report including profiler data.
    
    Returns:
        Dictionary with performance metrics and statistics
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "profiler_stats": profiler.get_all_stats(),
        "network_metrics": {},
        "overall_stats": {
            "total_networks": len(health_monitor.network_metrics),
            "total_rpc_calls": 0,
            "total_successful_calls": 0,
            "total_failed_calls": 0,
            "total_assets_processed": 0,
            "average_network_time": 0,
            "average_rpc_time": 0
        }
    }
    
    # Aggregate network metrics
    network_times = []
    rpc_times = []
    
    for network_key, metrics in health_monitor.network_metrics.items():
        network_report = {
            "network_name": metrics.network_name,
            "duration": metrics.duration,
            "assets_processed": metrics.total_assets_processed,
            "rpc_calls": metrics.total_rpc_calls,
            "successful_calls": metrics.successful_rpc_calls,
            "failed_calls": metrics.failed_rpc_calls,
            "success_rate": metrics.success_rate,
            "average_rpc_time": metrics.average_rpc_time,
            "total_response_size": metrics.total_response_size,
            "errors": metrics.errors,
            "warnings": metrics.warnings
        }
        
        report["network_metrics"][network_key] = network_report
        
        # Aggregate for overall stats
        report["overall_stats"]["total_rpc_calls"] += metrics.total_rpc_calls
        report["overall_stats"]["total_successful_calls"] += metrics.successful_rpc_calls
        report["overall_stats"]["total_failed_calls"] += metrics.failed_rpc_calls
        report["overall_stats"]["total_assets_processed"] += metrics.total_assets_processed
        
        if metrics.duration:
            network_times.append(metrics.duration)
        
        # Collect RPC times
        for call in metrics.rpc_call_history:
            if call.success and call.duration:
                rpc_times.append(call.duration)
    
    # Calculate averages
    if network_times:
        report["overall_stats"]["average_network_time"] = sum(network_times) / len(network_times)
    
    if rpc_times:
        report["overall_stats"]["average_rpc_time"] = sum(rpc_times) / len(rpc_times)
    
    return report


def save_performance_report(filepath: str):
    """
    Save comprehensive performance report to file.
    
    Args:
        filepath: Path to save the performance report
    """
    try:
        performance_report = get_performance_report()
        
        with open(filepath, 'w') as f:
            json.dump(performance_report, f, indent=2)
        
        logger.info(f"Performance report saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save performance report to {filepath}: {e}")


def save_debug_report(filepath: str, include_rpc_history: bool = False):
    """
    Save comprehensive debug report with detailed information.
    
    Args:
        filepath: Path to save the debug report
        include_rpc_history: Whether to include full RPC call history
    """
    try:
        debug_report = {
            "timestamp": datetime.now().isoformat(),
            "health_summary": get_network_health_summary(),
            "performance_report": get_performance_report(),
            "endpoint_health": {},
            "network_metrics": {}
        }
        
        # Add endpoint health details
        for url, health in health_monitor.endpoint_health.items():
            debug_report["endpoint_health"][url] = {
                "is_healthy": health.is_healthy,
                "last_check": health.last_check.isoformat(),
                "response_time": health.response_time,
                "error_count": health.error_count,
                "success_count": health.success_count,
                "last_error": health.last_error,
                "consecutive_failures": health.consecutive_failures
            }
        
        # Add detailed network metrics
        for network_key, metrics in health_monitor.network_metrics.items():
            network_debug = {
                "network_name": metrics.network_name,
                "start_time": datetime.fromtimestamp(metrics.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(metrics.end_time).isoformat() if metrics.end_time else None,
                "duration": metrics.duration,
                "total_rpc_calls": metrics.total_rpc_calls,
                "successful_rpc_calls": metrics.successful_rpc_calls,
                "failed_rpc_calls": metrics.failed_rpc_calls,
                "success_rate": metrics.success_rate,
                "average_rpc_time": metrics.average_rpc_time,
                "total_assets_processed": metrics.total_assets_processed,
                "total_response_size": metrics.total_response_size,
                "errors": metrics.errors,
                "warnings": metrics.warnings
            }
            
            if include_rpc_history:
                network_debug["rpc_call_history"] = [
                    {
                        "url": call.url,
                        "method": call.method,
                        "params": call.params,
                        "start_time": datetime.fromtimestamp(call.start_time).isoformat(),
                        "end_time": datetime.fromtimestamp(call.end_time).isoformat() if call.end_time else None,
                        "duration": call.duration,
                        "success": call.success,
                        "response_size": call.response_size,
                        "error": call.error,
                        "retry_count": call.retry_count
                    }
                    for call in metrics.rpc_call_history
                ]
            
            debug_report["network_metrics"][network_key] = network_debug
        
        with open(filepath, 'w') as f:
            json.dump(debug_report, f, indent=2)
        
        logger.info(f"Debug report saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save debug report to {filepath}: {e}")


def print_performance_summary():
    """Print a concise performance summary to console."""
    report = get_performance_report()
    overall = report["overall_stats"]
    
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"📊 Networks processed: {overall['total_networks']}")
    print(f"📊 Total assets: {overall['total_assets_processed']}")
    print(f"📊 Total RPC calls: {overall['total_rpc_calls']}")
    print(f"📊 RPC success rate: {(overall['total_successful_calls'] / max(overall['total_rpc_calls'], 1)):.1%}")
    print(f"⏱️  Average network time: {overall['average_network_time']:.2f}s")
    print(f"⏱️  Average RPC time: {overall['average_rpc_time']:.3f}s")
    
    # Show top 3 slowest networks
    network_times = [
        (key, metrics["duration"] or 0, metrics["network_name"])
        for key, metrics in report["network_metrics"].items()
    ]
    network_times.sort(key=lambda x: x[1], reverse=True)
    
    if network_times:
        print("\n🐌 Slowest networks:")
        for i, (key, duration, name) in enumerate(network_times[:3]):
            print(f"   {i+1}. {name}: {duration:.1f}s")
    
    print("="*70)


def create_github_actions_notification(health_summary: Dict[str, Any]) -> str:
    """
    Create GitHub Actions notification message for workflow failures.
    
    Args:
        health_summary: Health summary from get_network_health_summary()
        
    Returns:
        Formatted notification message
    """
    stats = health_summary["overall_stats"]
    
    if stats["unhealthy_networks"] == 0 and stats["degraded_networks"] == 0:
        return "✅ All networks are healthy"
    
    message_parts = []
    
    if stats["unhealthy_networks"] > 0:
        message_parts.append(f"🔴 {stats['unhealthy_networks']} networks unhealthy")
    
    if stats["degraded_networks"] > 0:
        message_parts.append(f"🟡 {stats['degraded_networks']} networks degraded")
    
    if stats["healthy_networks"] > 0:
        message_parts.append(f"✅ {stats['healthy_networks']} networks healthy")
    
    # Add details for unhealthy networks
    unhealthy_details = []
    for network_key, network_info in health_summary["networks"].items():
        if network_info["status"] == "unhealthy":
            unhealthy_details.append(f"- {network_info['name']}: No healthy endpoints")
        elif network_info["status"] == "degraded":
            unhealthy_details.append(
                f"- {network_info['name']}: Primary down, "
                f"{network_info['healthy_fallbacks']}/{network_info['total_fallbacks']} fallbacks healthy"
            )
    
    message = " | ".join(message_parts)
    
    if unhealthy_details:
        message += "\n\nDetails:\n" + "\n".join(unhealthy_details)
    
    return message


# Enhanced logging functions for better debugging
def log_rpc_call_start(network_key: str, method: str, url: str, params: List[Any]):
    """Log the start of an RPC call."""
    logger.debug(f"[{network_key}] Starting RPC call: {method} to {url}")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[{network_key}] RPC params: {params}")


def log_rpc_call_success(network_key: str, method: str, duration: float, response_size: Optional[int] = None):
    """Log successful RPC call."""
    size_info = f" ({response_size} bytes)" if response_size else ""
    logger.debug(f"[{network_key}] RPC call succeeded: {method} in {duration:.3f}s{size_info}")


def log_rpc_call_failure(network_key: str, method: str, duration: float, error: str, retry_count: int = 0):
    """Log failed RPC call."""
    retry_info = f" (retry {retry_count})" if retry_count > 0 else ""
    logger.warning(f"[{network_key}] RPC call failed: {method} in {duration:.3f}s{retry_info} - {error}")


def log_asset_processing(network_key: str, asset_symbol: str, asset_address: str, success: bool, error: Optional[str] = None):
    """Log asset processing result."""
    if success:
        logger.debug(f"[{network_key}] Asset processed successfully: {asset_symbol} ({asset_address})")
    else:
        logger.warning(f"[{network_key}] Asset processing failed: {asset_symbol} ({asset_address}) - {error}")


def log_network_summary(network_key: str, network_name: str, assets_processed: int, 
                       duration: float, rpc_calls: int, success_rate: float):
    """Log network processing summary."""
    logger.info(
        f"[{network_key}] Network completed: {network_name} - "
        f"{assets_processed} assets, {rpc_calls} RPC calls, "
        f"{success_rate:.1%} success rate in {duration:.1f}s"
    )


def configure_debug_logging(enable_debug: bool = False, log_file: Optional[str] = None):
    """
    Configure debug logging level and output.
    
    Args:
        enable_debug: Enable debug level logging
        log_file: Optional log file path
    """
    global logger
    
    log_level = "DEBUG" if enable_debug else "INFO"
    logger = setup_logging(log_level, log_file)
    
    logger.info(f"Debug logging configured: level={log_level}, file={log_file}")


# Initialize global health monitor
health_monitor = HealthMonitor()


def update_rpc_latency(url: str, latency_ms: float):
    """
    Update RPC latency metrics for monitoring.
    
    Args:
        url: RPC endpoint URL
        latency_ms: Latency in milliseconds
    """
    # Update endpoint health with latency information
    if url in health_monitor.endpoint_health:
        endpoint = health_monitor.endpoint_health[url]
        endpoint.response_time = latency_ms / 1000  # Convert to seconds
        endpoint.last_check = datetime.now()
        
        # Update success count for latency tracking
        endpoint.success_count += 1
        
        # Mark as unhealthy if latency is too high
        if latency_ms > health_monitor.response_time_threshold * 1000:
            endpoint.is_healthy = False
            endpoint.last_error = f"High latency: {latency_ms:.0f}ms"


def get_performance_optimized_networks(networks: Dict[str, Any], max_time_limit: float = 540) -> Dict[str, Any]:
    """
    Get networks optimized for performance within time constraints.
    
    Args:
        networks: Dictionary of network configurations
        max_time_limit: Maximum execution time in seconds
        
    Returns:
        Optimized network configuration
    """
    from network_prioritization import get_execution_strategy
    
    # Get execution strategy based on time constraints
    strategy = get_execution_strategy(0, max_time_limit, networks)
    
    # Return networks based on strategy
    if strategy['mode'] == 'critical_only':
        # Only critical networks
        critical_networks = {}
        for network_key, config, priority in strategy['networks']:
            critical_networks[network_key] = config
        return critical_networks
    else:
        # All networks but potentially reordered
        return networks


def create_performance_report() -> Dict[str, Any]:
    """Create comprehensive performance report."""
    from network_prioritization import network_prioritizer
    from performance_cache import get_cache_stats
    
    # Get profiler stats
    profiler_stats = profiler.get_all_stats()
    
    # Get network metrics
    network_metrics = {}
    for network_key, metrics in health_monitor.network_metrics.items():
        network_metrics[network_key] = {
            'network_name': metrics.network_name,
            'duration': metrics.duration,
            'total_rpc_calls': metrics.total_rpc_calls,
            'successful_rpc_calls': metrics.successful_rpc_calls,
            'success_rate': metrics.success_rate,
            'average_rpc_time': metrics.average_rpc_time,
            'total_assets_processed': metrics.total_assets_processed,
            'errors': len(metrics.errors),
            'warnings': len(metrics.warnings)
        }
    
    # Calculate overall stats
    total_networks = len(network_metrics)
    total_rpc_calls = sum(m['total_rpc_calls'] for m in network_metrics.values())
    total_successful_calls = sum(m['successful_rpc_calls'] for m in network_metrics.values())
    total_assets = sum(m['total_assets_processed'] for m in network_metrics.values())
    
    avg_network_time = (
        sum(m['duration'] for m in network_metrics.values() if m['duration']) / 
        max(total_networks, 1)
    )
    
    avg_rpc_time = (
        sum(m['average_rpc_time'] * m['total_rpc_calls'] for m in network_metrics.values()) /
        max(total_rpc_calls, 1)
    )
    
    return {
        'timestamp': datetime.now().isoformat(),
        'profiler_stats': profiler_stats,
        'network_metrics': network_metrics,
        'network_prioritization_stats': network_prioritizer.get_network_stats(),
        'cache_stats': get_cache_stats(),
        'overall_stats': {
            'total_networks': total_networks,
            'total_rpc_calls': total_rpc_calls,
            'total_successful_calls': total_successful_calls,
            'total_failed_calls': total_rpc_calls - total_successful_calls,
            'total_assets_processed': total_assets,
            'average_network_time': avg_network_time,
            'average_rpc_time': avg_rpc_time,
            'overall_success_rate': total_successful_calls / max(total_rpc_calls, 1)
        }
    }


def save_performance_report(filepath: str):
    """
    Save comprehensive performance report to file.
    
    Args:
        filepath: Path to save the performance report
    """
    try:
        report = create_performance_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save performance report: {e}")


def print_performance_summary():
    """Print performance summary to console."""
    report = create_performance_report()
    
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    overall = report['overall_stats']
    print(f"📊 Networks processed: {overall['total_networks']}")
    print(f"📊 Total assets: {overall['total_assets_processed']}")
    print(f"📊 Total RPC calls: {overall['total_rpc_calls']}")
    print(f"📊 RPC success rate: {overall['overall_success_rate']:.1%}")
    print(f"⏱️  Average network time: {overall['average_network_time']:.2f}s")
    print(f"⏱️  Average RPC time: {overall['average_rpc_time']:.3f}s")
    
    # Cache stats
    cache_stats = report.get('cache_stats', {})
    if cache_stats.get('total_entries', 0) > 0:
        print(f"💾 Cache entries: {cache_stats['active_entries']}/{cache_stats['total_entries']}")
        print(f"💾 Cache hit potential: {cache_stats['cache_hit_potential']}")
    
    # Top performing networks
    network_metrics = report['network_metrics']
    if network_metrics:
        print("\n🏆 Top Performing Networks:")
        sorted_networks = sorted(
            network_metrics.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )
        
        for i, (network_key, metrics) in enumerate(sorted_networks[:5]):
            duration = metrics['duration'] or 0
            print(f"  {i+1}. {metrics['network_name']:20} | "
                  f"{metrics['success_rate']:.1%} success | "
                  f"{duration:.1f}s | "
                  f"{metrics['total_assets_processed']} assets")
    
    print("="*70)


def save_debug_report(filepath: str, include_rpc_history: bool = False):
    """
    Save comprehensive debug report.
    
    Args:
        filepath: Path to save the debug report
        include_rpc_history: Include detailed RPC call history
    """
    try:
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'performance_report': create_performance_report(),
            'health_summary': get_network_health_summary(),
            'endpoint_health': {}
        }
        
        # Add endpoint health details
        for url, health in health_monitor.endpoint_health.items():
            debug_data['endpoint_health'][url] = {
                'is_healthy': health.is_healthy,
                'response_time': health.response_time,
                'error_count': health.error_count,
                'success_count': health.success_count,
                'consecutive_failures': health.consecutive_failures,
                'last_error': health.last_error,
                'last_check': health.last_check.isoformat() if health.last_check else None
            }
        
        # Add detailed RPC history if requested
        if include_rpc_history:
            debug_data['rpc_call_history'] = {}
            for network_key, metrics in health_monitor.network_metrics.items():
                debug_data['rpc_call_history'][network_key] = [
                    {
                        'url': call.url,
                        'method': call.method,
                        'duration': call.duration,
                        'success': call.success,
                        'error': call.error,
                        'retry_count': call.retry_count,
                        'response_size': call.response_size
                    }
                    for call in metrics.rpc_call_history
                ]
        
        with open(filepath, 'w') as f:
            json.dump(debug_data, f, indent=2)
        
        logger.info(f"Debug report saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to save debug report: {e}")