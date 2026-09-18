"""Offline regression tests for reserve discovery ownership."""

import os
from pathlib import Path
import sys
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import aave_fetcher
from graceful_fetcher import GracefulDataFetcher


class PrefetchedReservesTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {'ENABLE_RPC_MONITORING': 'false'}))
        self.config = {
            'name': 'Test network', 'pool': '0xpool',
            'rpc': 'https://primary.invalid',
            'rpc_fallback': ['https://fallback.invalid'],
        }
        self.reserves = ['0xasset1', '0xasset2']
        self.assets = [{'asset_address': address, 'symbol': 'TEST'} for address in self.reserves]
        self.discovery = self.stack.enter_context(
            patch('graceful_fetcher.get_reserves', return_value=self.reserves)
        )
        self.fetch_asset = self.stack.enter_context(
            patch.object(GracefulDataFetcher, 'fetch_asset_data', side_effect=self.assets)
        )

    def run_wrapper(self, cached, fetched):
        self.stack.enter_context(patch('performance_cache.get_cached_reserve_list', return_value=cached))
        self.cache_write = self.stack.enter_context(patch('performance_cache.cache_reserve_list'))
        self.stack.enter_context(patch('performance_cache.cache_symbol'))
        self.stack.enter_context(patch('aave_fetcher.health_monitor'))
        self.stack.enter_context(patch('aave_fetcher.log_network_summary'))
        self.wrapper_discovery = self.stack.enter_context(
            patch('aave_fetcher.get_reserves', return_value=fetched)
        )
        return aave_fetcher.fetch_network_data_parallel_optimized(
            'test', self.config, aave_fetcher.PerformanceMonitor(), 120,
            SimpleNamespace(tier=SimpleNamespace(name='TEST'), weight=1.0),
        )

    def assert_assets_fetched(self):
        self.assertEqual(self.fetch_asset.call_args_list, [
            call(address, self.config, self.config['rpc'], self.config['rpc_fallback'], 'test')
            for address in self.reserves
        ])

    def test_cache_miss_discovers_once_and_caches_list(self):
        key, data, _ = self.run_wrapper(None, self.reserves)
        self.assertEqual((key, data), ('test', self.assets))
        self.wrapper_discovery.assert_called_once_with(
            self.config['pool'], self.config['rpc'], self.config['rpc_fallback'], 'test'
        )
        self.discovery.assert_not_called()
        self.cache_write.assert_called_once_with('test', self.reserves, 1.0)
        self.assert_assets_fetched()

    def test_cache_hit_uses_cached_assets_without_discovery(self):
        # A second lookup would return a different list, so check asset identity too.
        self.discovery.return_value = ['0xwrong']
        _, data, _ = self.run_wrapper(self.reserves, ['0xwrong'])
        self.assertEqual(data, self.assets)
        self.wrapper_discovery.assert_not_called()
        self.discovery.assert_not_called()
        self.cache_write.assert_not_called()
        self.assert_assets_fetched()

    def test_empty_discovery_stops_without_second_lookup(self):
        _, data, _ = self.run_wrapper(None, [])
        self.assertIsNone(data)
        self.wrapper_discovery.assert_called_once()
        self.discovery.assert_not_called()
        self.fetch_asset.assert_not_called()
        self.cache_write.assert_not_called()

    def test_empty_cache_retains_existing_refresh_behavior(self):
        _, data, _ = self.run_wrapper([], self.reserves)
        self.assertEqual(data, self.assets)
        self.wrapper_discovery.assert_called_once()
        self.discovery.assert_not_called()
        self.assert_assets_fetched()

    def test_explicit_empty_prefetch_does_not_discover(self):
        data = GracefulDataFetcher().fetch_network_data('test', self.config, prefetched_reserves=[])
        self.assertIsNone(data)
        self.discovery.assert_not_called()
        self.fetch_asset.assert_not_called()

    def test_standalone_discovers_once(self):
        data = GracefulDataFetcher().fetch_network_data('test', self.config)
        self.assertEqual(data, self.assets)
        self.discovery.assert_called_once_with(
            self.config['pool'], self.config['rpc'], self.config['rpc_fallback'], 'test'
        )
        self.assert_assets_fetched()

    def test_standalone_empty_discovery(self):
        self.discovery.return_value = []
        self.assertIsNone(GracefulDataFetcher().fetch_network_data('test', self.config))
        self.discovery.assert_called_once()
        self.fetch_asset.assert_not_called()

    def test_sequential_caller_still_discovers_once(self):
        with patch('graceful_fetcher.get_active_networks', return_value={'test': self.config}):
            data = GracefulDataFetcher().fetch_all_networks_data()
        self.assertEqual(data, {'test': self.assets})
        self.discovery.assert_called_once()
        self.assert_assets_fetched()


if __name__ == '__main__':
    unittest.main()
