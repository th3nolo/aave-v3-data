#!/usr/bin/env python3
"""
Intelligent caching system for network configurations and contract addresses.
Implements multi-level caching with TTL and performance-based prioritization.
"""

import json
import time
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib


@dataclass
class CacheEntry:
    """Represents a cached entry with metadata."""
    data: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    access_count: int = 0
    last_access: float = 0
    performance_score: float = 1.0  # Higher is better
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp
    
    def access(self):
        """Record access to this cache entry."""
        self.access_count += 1
        self.last_access = time.time()


class PerformanceCache:
    """
    Multi-level intelligent cache with performance-based prioritization.
    
    Features:
    - TTL-based expiration
    - Performance-based prioritization
    - Network configuration caching
    - Contract address caching
    - Symbol caching with long TTL
    - Automatic cleanup
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_entries = 1000
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache TTL settings (in seconds)
        self.ttl_settings = {
            'network_config': 3600,      # 1 hour - network configs change rarely
            'contract_address': 7200,    # 2 hours - contract addresses are immutable
            'symbol': 86400,             # 24 hours - symbols never change
            'reserve_list': 300,         # 5 minutes - reserve lists can change
            'rpc_health': 60,            # 1 minute - RPC health changes frequently
            'performance_metrics': 300,   # 5 minutes - performance metrics
        }
        
        # Load persistent cache
        self._load_persistent_cache()
    
    def _get_cache_key(self, category: str, identifier: str, extra: str = "") -> str:
        """Generate a cache key."""
        key_data = f"{category}:{identifier}:{extra}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _load_persistent_cache(self):
        """Load cache from disk."""
        cache_file = os.path.join(self.cache_dir, "performance_cache.json")
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Convert back to CacheEntry objects
                for key, entry_data in cache_data.items():
                    try:
                        entry = CacheEntry(
                            data=entry_data['data'],
                            timestamp=entry_data['timestamp'],
                            ttl=entry_data['ttl'],
                            access_count=entry_data.get('access_count', 0),
                            last_access=entry_data.get('last_access', 0),
                            performance_score=entry_data.get('performance_score', 1.0)
                        )
                        
                        # Only load non-expired entries
                        if not entry.is_expired:
                            self.memory_cache[key] = entry
                    
                    except Exception:
                        continue  # Skip corrupted entries
                        
        except Exception:
            pass  # Start with empty cache if loading fails
    
    def _save_persistent_cache(self):
        """Save cache to disk."""
        cache_file = os.path.join(self.cache_dir, "performance_cache.json")
        
        try:
            # Convert CacheEntry objects to serializable format
            cache_data = {}
            for key, entry in self.memory_cache.items():
                if not entry.is_expired:  # Only save non-expired entries
                    cache_data[key] = {
                        'data': entry.data,
                        'timestamp': entry.timestamp,
                        'ttl': entry.ttl,
                        'access_count': entry.access_count,
                        'last_access': entry.last_access,
                        'performance_score': entry.performance_score
                    }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception:
            pass  # Fail silently if save fails
    
    def get(self, category: str, identifier: str, extra: str = "") -> Optional[Any]:
        """Get item from cache."""
        key = self._get_cache_key(category, identifier, extra)
        
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            
            if entry.is_expired:
                del self.memory_cache[key]
                return None
            
            entry.access()
            return entry.data
        
        return None
    
    def set(self, category: str, identifier: str, data: Any, extra: str = "", 
            performance_score: float = 1.0, custom_ttl: Optional[float] = None):
        """Set item in cache."""
        key = self._get_cache_key(category, identifier, extra)
        ttl = custom_ttl or self.ttl_settings.get(category, 3600)
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl,
            performance_score=performance_score
        )
        
        self.memory_cache[key] = entry
        
        # Cleanup if cache is too large
        if len(self.memory_cache) > self.max_memory_entries:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired and least valuable entries."""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # If still too large, remove least valuable entries
        if len(self.memory_cache) > self.max_memory_entries:
            # Sort by value score (combination of performance and access frequency)
            entries_with_keys = [
                (key, entry, self._calculate_value_score(entry))
                for key, entry in self.memory_cache.items()
            ]
            
            entries_with_keys.sort(key=lambda x: x[2])  # Sort by value score
            
            # Remove bottom 20%
            remove_count = len(entries_with_keys) // 5
            for i in range(remove_count):
                key = entries_with_keys[i][0]
                del self.memory_cache[key]
    
    def _calculate_value_score(self, entry: CacheEntry) -> float:
        """Calculate value score for cache entry prioritization."""
        age_factor = max(0, 1 - (entry.age_seconds / entry.ttl))  # Newer is better
        access_factor = min(1, entry.access_count / 10)  # More accessed is better
        performance_factor = entry.performance_score  # Higher performance is better
        
        return age_factor * 0.3 + access_factor * 0.3 + performance_factor * 0.4
    
    def cache_network_config(self, network_key: str, config: Dict[str, Any], 
                           performance_score: float = 1.0):
        """Cache network configuration."""
        self.set('network_config', network_key, config, 
                performance_score=performance_score)
    
    def get_network_config(self, network_key: str) -> Optional[Dict[str, Any]]:
        """Get cached network configuration."""
        return self.get('network_config', network_key)
    
    def cache_contract_address(self, network_key: str, contract_type: str, 
                             address: str, performance_score: float = 1.0):
        """Cache contract address."""
        self.set('contract_address', network_key, address, 
                extra=contract_type, performance_score=performance_score)
    
    def get_contract_address(self, network_key: str, contract_type: str) -> Optional[str]:
        """Get cached contract address."""
        return self.get('contract_address', network_key, extra=contract_type)
    
    def cache_symbol(self, asset_address: str, symbol: str, network_key: str = ""):
        """Cache asset symbol (long TTL since symbols don't change)."""
        self.set('symbol', asset_address, symbol, extra=network_key, 
                performance_score=2.0)  # High performance score for symbols
    
    def get_symbol(self, asset_address: str, network_key: str = "") -> Optional[str]:
        """Get cached asset symbol."""
        return self.get('symbol', asset_address, extra=network_key)
    
    def cache_reserve_list(self, network_key: str, reserves: List[str], 
                          performance_score: float = 1.0):
        """Cache reserve list for a network."""
        self.set('reserve_list', network_key, reserves, 
                performance_score=performance_score)
    
    def get_reserve_list(self, network_key: str) -> Optional[List[str]]:
        """Get cached reserve list."""
        return self.get('reserve_list', network_key)
    
    def cache_rpc_health(self, rpc_url: str, health_data: Dict[str, Any]):
        """Cache RPC endpoint health data."""
        self.set('rpc_health', rpc_url, health_data)
    
    def get_rpc_health(self, rpc_url: str) -> Optional[Dict[str, Any]]:
        """Get cached RPC health data."""
        return self.get('rpc_health', rpc_url)
    
    def cache_performance_metrics(self, network_key: str, metrics: Dict[str, Any]):
        """Cache performance metrics for a network."""
        self.set('performance_metrics', network_key, metrics)
    
    def get_performance_metrics(self, network_key: str) -> Optional[Dict[str, Any]]:
        """Get cached performance metrics."""
        return self.get('performance_metrics', network_key)
    
    def invalidate_category(self, category: str):
        """Invalidate all entries in a category."""
        keys_to_remove = []
        
        for key, entry in self.memory_cache.items():
            # Check if key belongs to category (simplified check)
            if category in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.memory_cache)
        expired_entries = sum(1 for entry in self.memory_cache.values() if entry.is_expired)
        
        category_counts = {}
        for key in self.memory_cache.keys():
            # Extract category from key (simplified)
            for category in self.ttl_settings.keys():
                if category in key:
                    category_counts[category] = category_counts.get(category, 0) + 1
                    break
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'category_counts': category_counts,
            'cache_hit_potential': sum(entry.access_count for entry in self.memory_cache.values()),
            'average_performance_score': sum(entry.performance_score for entry in self.memory_cache.values()) / max(total_entries, 1)
        }
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        return len(expired_keys)
    
    def save(self):
        """Save cache to disk."""
        self._save_persistent_cache()
    
    def clear(self):
        """Clear all cache entries."""
        self.memory_cache.clear()
        
        # Also remove persistent cache file
        cache_file = os.path.join(self.cache_dir, "performance_cache.json")
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception:
            pass


# Global cache instance
performance_cache = PerformanceCache()


def get_cached_network_config(network_key: str) -> Optional[Dict[str, Any]]:
    """Get cached network configuration."""
    return performance_cache.get_network_config(network_key)


def cache_network_config(network_key: str, config: Dict[str, Any], performance_score: float = 1.0):
    """Cache network configuration."""
    performance_cache.cache_network_config(network_key, config, performance_score)


def get_cached_symbol(asset_address: str, network_key: str = "") -> Optional[str]:
    """Get cached asset symbol."""
    return performance_cache.get_symbol(asset_address, network_key)


def cache_symbol(asset_address: str, symbol: str, network_key: str = ""):
    """Cache asset symbol."""
    performance_cache.cache_symbol(asset_address, symbol, network_key)


def get_cached_reserve_list(network_key: str) -> Optional[List[str]]:
    """Get cached reserve list."""
    return performance_cache.get_reserve_list(network_key)


def cache_reserve_list(network_key: str, reserves: List[str], performance_score: float = 1.0):
    """Cache reserve list."""
    performance_cache.cache_reserve_list(network_key, reserves, performance_score)


def save_cache():
    """Save cache to disk."""
    performance_cache.save()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return performance_cache.get_cache_stats()


if __name__ == "__main__":
    # Test the cache system
    cache = PerformanceCache()
    
    # Test network config caching
    test_config = {
        'name': 'Test Network',
        'rpc': 'https://test.rpc.com',
        'pool': '0x1234567890123456789012345678901234567890'
    }
    
    cache.cache_network_config('test', test_config, performance_score=1.5)
    retrieved = cache.get_network_config('test')
    
    print("Cache Test Results:")
    print(f"  Stored config: {test_config}")
    print(f"  Retrieved config: {retrieved}")
    print(f"  Match: {test_config == retrieved}")
    
    # Test symbol caching
    cache.cache_symbol('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'USDC', 'ethereum')
    symbol = cache.get_symbol('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'ethereum')
    print(f"  Cached symbol: {symbol}")
    
    # Print cache stats
    stats = cache.get_cache_stats()
    print(f"  Cache stats: {stats}")
    
    # Save cache
    cache.save()
    print("  Cache saved to disk")