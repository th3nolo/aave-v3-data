#!/usr/bin/env python3
"""
Network prioritization system for critical chains.
Implements intelligent ordering and resource allocation based on network importance.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time


class NetworkTier(Enum):
    """Network importance tiers."""
    CRITICAL = 1    # Must succeed - Ethereum, Polygon, Arbitrum
    HIGH = 2        # High priority - Optimism, Avalanche, Base
    MEDIUM = 3      # Medium priority - BNB, Gnosis, Scroll
    LOW = 4         # Lower priority - Metis, Celo, Linea, zkSync


@dataclass
class NetworkPriority:
    """Network priority configuration."""
    network_key: str
    tier: NetworkTier
    weight: float  # Higher weight = more resources
    timeout_multiplier: float  # Timeout adjustment
    retry_multiplier: int  # Retry count adjustment
    parallel_workers: int  # Dedicated workers for this network
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score (lower is higher priority)."""
        return self.tier.value + (1.0 / max(self.weight, 0.1))


class NetworkPrioritizer:
    """
    Manages network prioritization and resource allocation.
    
    Features:
    - Tier-based prioritization
    - Dynamic resource allocation
    - Performance-based adjustments
    - Critical network protection
    """
    
    def __init__(self):
        # Network priority configuration
        self.network_priorities = {
            # CRITICAL TIER - Must succeed
            'ethereum': NetworkPriority(
                network_key='ethereum',
                tier=NetworkTier.CRITICAL,
                weight=3.0,
                timeout_multiplier=2.0,
                retry_multiplier=3,
                parallel_workers=3
            ),
            'polygon': NetworkPriority(
                network_key='polygon',
                tier=NetworkTier.CRITICAL,
                weight=2.5,
                timeout_multiplier=1.8,
                retry_multiplier=3,
                parallel_workers=2
            ),
            'arbitrum': NetworkPriority(
                network_key='arbitrum',
                tier=NetworkTier.CRITICAL,
                weight=2.5,
                timeout_multiplier=1.8,
                retry_multiplier=3,
                parallel_workers=2
            ),
            
            # HIGH TIER - High priority
            'optimism': NetworkPriority(
                network_key='optimism',
                tier=NetworkTier.HIGH,
                weight=2.0,
                timeout_multiplier=1.5,
                retry_multiplier=2,
                parallel_workers=2
            ),
            'avalanche': NetworkPriority(
                network_key='avalanche',
                tier=NetworkTier.HIGH,
                weight=2.0,
                timeout_multiplier=1.5,
                retry_multiplier=2,
                parallel_workers=2
            ),
            'base': NetworkPriority(
                network_key='base',
                tier=NetworkTier.HIGH,
                weight=1.8,
                timeout_multiplier=1.4,
                retry_multiplier=2,
                parallel_workers=1
            ),
            
            # MEDIUM TIER - Medium priority
            'bnb': NetworkPriority(
                network_key='bnb',
                tier=NetworkTier.MEDIUM,
                weight=1.5,
                timeout_multiplier=1.2,
                retry_multiplier=2,
                parallel_workers=1
            ),
            'gnosis': NetworkPriority(
                network_key='gnosis',
                tier=NetworkTier.MEDIUM,
                weight=1.3,
                timeout_multiplier=1.2,
                retry_multiplier=2,
                parallel_workers=1
            ),
            'scroll': NetworkPriority(
                network_key='scroll',
                tier=NetworkTier.MEDIUM,
                weight=1.2,
                timeout_multiplier=1.1,
                retry_multiplier=1,
                parallel_workers=1
            ),
            
            # LOW TIER - Lower priority
            'metis': NetworkPriority(
                network_key='metis',
                tier=NetworkTier.LOW,
                weight=1.0,
                timeout_multiplier=1.0,
                retry_multiplier=1,
                parallel_workers=1
            ),
            'celo': NetworkPriority(
                network_key='celo',
                tier=NetworkTier.LOW,
                weight=1.0,
                timeout_multiplier=1.0,
                retry_multiplier=1,
                parallel_workers=1
            ),
            'linea': NetworkPriority(
                network_key='linea',
                tier=NetworkTier.LOW,
                weight=0.8,
                timeout_multiplier=0.9,
                retry_multiplier=1,
                parallel_workers=1
            ),
            'zksync': NetworkPriority(
                network_key='zksync',
                tier=NetworkTier.LOW,
                weight=0.8,
                timeout_multiplier=0.9,
                retry_multiplier=1,
                parallel_workers=1
            ),
        }
        
        # Performance tracking for dynamic adjustments
        self.performance_history: Dict[str, List[float]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
    
    def get_network_priority(self, network_key: str) -> NetworkPriority:
        """Get priority configuration for a network."""
        return self.network_priorities.get(
            network_key,
            NetworkPriority(
                network_key=network_key,
                tier=NetworkTier.LOW,
                weight=0.5,
                timeout_multiplier=0.8,
                retry_multiplier=1,
                parallel_workers=1
            )
        )
    
    def get_prioritized_networks(self, networks: Dict[str, Any]) -> List[Tuple[str, Any, NetworkPriority]]:
        """
        Get networks sorted by priority (highest priority first).
        
        Args:
            networks: Dictionary of network configurations
            
        Returns:
            List of (network_key, network_config, priority) tuples sorted by priority
        """
        network_list = []
        
        for network_key, network_config in networks.items():
            priority = self.get_network_priority(network_key)
            network_list.append((network_key, network_config, priority))
        
        # Sort by priority score (lower score = higher priority)
        network_list.sort(key=lambda x: x[2].priority_score)
        
        return network_list
    
    def get_critical_networks(self, networks: Dict[str, Any]) -> List[Tuple[str, Any, NetworkPriority]]:
        """Get only critical tier networks."""
        prioritized = self.get_prioritized_networks(networks)
        return [
            (key, config, priority) for key, config, priority in prioritized
            if priority.tier == NetworkTier.CRITICAL
        ]
    
    def calculate_timeout(self, network_key: str, base_timeout: float) -> float:
        """Calculate adjusted timeout for a network."""
        priority = self.get_network_priority(network_key)
        adjusted_timeout = base_timeout * priority.timeout_multiplier
        
        # Apply performance-based adjustments
        if network_key in self.performance_history:
            recent_times = self.performance_history[network_key][-5:]  # Last 5 attempts
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                # If network is consistently slow, increase timeout
                if avg_time > base_timeout * 0.8:
                    adjusted_timeout *= 1.5
        
        return min(adjusted_timeout, 300)  # Cap at 5 minutes
    
    def calculate_retry_count(self, network_key: str, base_retries: int) -> int:
        """Calculate adjusted retry count for a network."""
        priority = self.get_network_priority(network_key)
        adjusted_retries = base_retries * priority.retry_multiplier
        
        # Apply failure-based adjustments
        failure_rate = self.get_failure_rate(network_key)
        if failure_rate > 0.5:  # High failure rate
            adjusted_retries = max(1, adjusted_retries - 1)  # Reduce retries
        elif failure_rate < 0.1:  # Low failure rate
            adjusted_retries = min(5, adjusted_retries + 1)  # Increase retries
        
        return max(1, adjusted_retries)
    
    def get_worker_allocation(self, total_workers: int, networks: Dict[str, Any]) -> Dict[str, int]:
        """
        Allocate workers to networks based on priority.
        
        Args:
            total_workers: Total number of workers available
            networks: Dictionary of network configurations
            
        Returns:
            Dictionary mapping network_key to worker count
        """
        prioritized_networks = self.get_prioritized_networks(networks)
        
        # Calculate total weight
        total_weight = sum(priority.weight for _, _, priority in prioritized_networks)
        
        # Allocate workers proportionally
        allocation = {}
        allocated_workers = 0
        
        for network_key, _, priority in prioritized_networks:
            # Calculate proportional allocation
            proportion = priority.weight / total_weight
            workers = max(1, int(total_workers * proportion))
            
            # Ensure critical networks get minimum workers
            if priority.tier == NetworkTier.CRITICAL:
                workers = max(workers, priority.parallel_workers)
            
            # Don't exceed total workers
            if allocated_workers + workers > total_workers:
                workers = max(1, total_workers - allocated_workers)
            
            allocation[network_key] = workers
            allocated_workers += workers
            
            if allocated_workers >= total_workers:
                break
        
        return allocation
    
    def record_performance(self, network_key: str, execution_time: float, success: bool):
        """Record performance metrics for a network."""
        # Track execution time
        if network_key not in self.performance_history:
            self.performance_history[network_key] = []
        
        self.performance_history[network_key].append(execution_time)
        
        # Keep only recent history (last 20 attempts)
        if len(self.performance_history[network_key]) > 20:
            self.performance_history[network_key] = self.performance_history[network_key][-20:]
        
        # Track success/failure
        if success:
            self.success_counts[network_key] = self.success_counts.get(network_key, 0) + 1
        else:
            self.failure_counts[network_key] = self.failure_counts.get(network_key, 0) + 1
    
    def get_failure_rate(self, network_key: str) -> float:
        """Get failure rate for a network."""
        successes = self.success_counts.get(network_key, 0)
        failures = self.failure_counts.get(network_key, 0)
        total = successes + failures
        
        if total == 0:
            return 0.0
        
        return failures / total
    
    def get_average_performance(self, network_key: str) -> Optional[float]:
        """Get average execution time for a network."""
        if network_key not in self.performance_history:
            return None
        
        times = self.performance_history[network_key]
        if not times:
            return None
        
        return sum(times) / len(times)
    
    def should_prioritize_critical(self, elapsed_time: float, total_time_limit: float) -> bool:
        """
        Determine if we should focus only on critical networks.
        
        Args:
            elapsed_time: Time already elapsed
            total_time_limit: Total time limit (e.g., GitHub Actions limit)
            
        Returns:
            True if we should focus only on critical networks
        """
        time_remaining = total_time_limit - elapsed_time
        
        # If less than 30% time remaining, focus on critical networks only
        return time_remaining < (total_time_limit * 0.3)
    
    def get_execution_strategy(self, elapsed_time: float, total_time_limit: float, 
                             networks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get execution strategy based on time constraints and network priorities.
        
        Returns:
            Dictionary with execution strategy parameters
        """
        time_remaining = total_time_limit - elapsed_time
        time_pressure = elapsed_time / total_time_limit
        
        if time_pressure < 0.3:  # Plenty of time
            return {
                'mode': 'comprehensive',
                'networks': self.get_prioritized_networks(networks),
                'max_workers': 12,
                'timeout_multiplier': 1.0,
                'retry_multiplier': 1.0
            }
        elif time_pressure < 0.7:  # Moderate time pressure
            return {
                'mode': 'prioritized',
                'networks': self.get_prioritized_networks(networks),
                'max_workers': 8,
                'timeout_multiplier': 0.8,
                'retry_multiplier': 0.8
            }
        else:  # High time pressure
            critical_networks = self.get_critical_networks(networks)
            return {
                'mode': 'critical_only',
                'networks': critical_networks,
                'max_workers': 6,
                'timeout_multiplier': 0.6,
                'retry_multiplier': 0.5
            }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network performance statistics."""
        stats = {}
        
        for network_key in self.network_priorities.keys():
            priority = self.get_network_priority(network_key)
            avg_time = self.get_average_performance(network_key)
            failure_rate = self.get_failure_rate(network_key)
            
            stats[network_key] = {
                'tier': priority.tier.name,
                'weight': priority.weight,
                'average_time': avg_time,
                'failure_rate': failure_rate,
                'total_attempts': (
                    self.success_counts.get(network_key, 0) + 
                    self.failure_counts.get(network_key, 0)
                )
            }
        
        return stats
    
    def print_priority_summary(self, networks: Dict[str, Any]):
        """Print network priority summary."""
        print("\n🎯 NETWORK PRIORITIZATION SUMMARY")
        print("=" * 50)
        
        prioritized = self.get_prioritized_networks(networks)
        
        for tier in NetworkTier:
            tier_networks = [
                (key, config, priority) for key, config, priority in prioritized
                if priority.tier == tier
            ]
            
            if tier_networks:
                print(f"\n{tier.name} TIER:")
                for network_key, network_config, priority in tier_networks:
                    avg_time = self.get_average_performance(network_key)
                    failure_rate = self.get_failure_rate(network_key)
                    
                    time_str = f"{avg_time:.2f}s" if avg_time else "N/A"
                    failure_str = f"{failure_rate:.1%}" if failure_rate > 0 else "0%"
                    
                    print(f"  {network_config['name']:20} | "
                          f"Weight: {priority.weight:4.1f} | "
                          f"Workers: {priority.parallel_workers} | "
                          f"Avg: {time_str:6} | "
                          f"Failures: {failure_str}")
        
        print("=" * 50)


# Global prioritizer instance
network_prioritizer = NetworkPrioritizer()


def get_prioritized_networks(networks: Dict[str, Any]) -> List[Tuple[str, Any, NetworkPriority]]:
    """Get networks sorted by priority."""
    return network_prioritizer.get_prioritized_networks(networks)


def get_critical_networks(networks: Dict[str, Any]) -> List[Tuple[str, Any, NetworkPriority]]:
    """Get only critical networks."""
    return network_prioritizer.get_critical_networks(networks)


def calculate_network_timeout(network_key: str, base_timeout: float) -> float:
    """Calculate adjusted timeout for a network."""
    return network_prioritizer.calculate_timeout(network_key, base_timeout)


def get_worker_allocation(total_workers: int, networks: Dict[str, Any]) -> Dict[str, int]:
    """Allocate workers to networks based on priority."""
    return network_prioritizer.get_worker_allocation(total_workers, networks)


def record_network_performance(network_key: str, execution_time: float, success: bool):
    """Record performance metrics for a network."""
    network_prioritizer.record_performance(network_key, execution_time, success)


def get_execution_strategy(elapsed_time: float, total_time_limit: float, 
                         networks: Dict[str, Any]) -> Dict[str, Any]:
    """Get execution strategy based on time constraints."""
    return network_prioritizer.get_execution_strategy(elapsed_time, total_time_limit, networks)


if __name__ == "__main__":
    # Test the prioritization system
    from networks import get_active_networks
    
    networks = get_active_networks()
    prioritizer = NetworkPrioritizer()
    
    print("Network Prioritization Test:")
    prioritizer.print_priority_summary(networks)
    
    # Test worker allocation
    allocation = prioritizer.get_worker_allocation(12, networks)
    print(f"\nWorker Allocation (12 total workers):")
    for network_key, workers in allocation.items():
        print(f"  {network_key}: {workers} workers")
    
    # Test execution strategy
    strategy = prioritizer.get_execution_strategy(0, 600, networks)  # 10 minute limit
    print(f"\nExecution Strategy: {strategy['mode']}")
    print(f"  Max workers: {strategy['max_workers']}")
    print(f"  Networks: {len(strategy['networks'])}")