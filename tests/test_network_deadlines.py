"""Offline deadline regressions: no public RPC or external HTTP requests."""

from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import multiprocessing
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import aave_fetcher
import graceful_fetcher
import utils
from network_deadline import (
    NetworkDeadline, NetworkDeadlineExceeded, current_deadline, retry_sleep,
)


def fake_rpc(value=None, delay=0, marker=None, *, timeout=30):
    """Deliberately ignores transport timeout, like stuck DNS or trickling I/O."""
    if marker:
        Path(marker).write_text("entered", encoding="utf-8")
    time.sleep(delay)
    return value


def report_socket_timeout(*, timeout=30):
    return timeout


class FakeRPCHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.server.calls += 1
        self.server.entered.set()
        if self.path == "/retry" and self.server.calls == 1:
            self.send_error(503)
            return
        payload = json.dumps({"jsonrpc": "2.0", "id": 1, "result": "0x1"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            if self.path == "/trickle":
                for byte in payload:
                    self.wfile.write(bytes([byte]))
                    self.wfile.flush()
                    time.sleep(0.2)
            else:
                self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeRPCHandler)
        self.server.calls = 0
        self.server.entered = threading.Event()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(1)

    def test_real_rpc_transport_success(self):
        with NetworkDeadline(4):
            self.assertEqual(utils.rpc_call_with_retry(self.url, "eth_chainId", [])["result"], "0x1")
        self.assertEqual(self.server.calls, 1)

    def test_real_rpc_transport_retry_preserves_exception_classification(self):
        with NetworkDeadline(4), patch.object(utils.random, "uniform", return_value=0):
            self.assertEqual(utils.rpc_call_with_retry(self.url + "/retry", "eth_chainId", [])["result"], "0x1")
        self.assertEqual(self.server.calls, 2)

    def test_trickling_response_is_stopped_by_wall_clock_deadline(self):
        started = time.monotonic()
        with self.assertRaises(NetworkDeadlineExceeded):
            with NetworkDeadline(1.5):
                utils.rpc_call_with_retry(self.url + "/trickle", "eth_chainId", [])
        elapsed = time.monotonic() - started
        self.assertTrue(self.server.entered.is_set())
        self.assertEqual(self.server.calls, 1)
        self.assertGreaterEqual(elapsed, 1.4)
        self.assertLess(elapsed, 2.5)
        self.assertFalse(multiprocessing.active_children())


class DeadlineTests(unittest.TestCase):
    def test_stuck_transport_deadline_includes_shutdown(self):
        before = {p.pid for p in multiprocessing.active_children()}
        with tempfile.TemporaryDirectory() as directory:
            marker = str(Path(directory) / "entered")
            started = time.monotonic()
            with self.assertRaises(NetworkDeadlineExceeded):
                with NetworkDeadline(1.5) as deadline:
                    deadline.call(fake_rpc, "late", delay=30, marker=marker)
            elapsed = time.monotonic() - started
            self.assertTrue(Path(marker).exists(), "fake RPC must start before timeout")
        self.assertGreaterEqual(elapsed, 1.4)
        self.assertLess(elapsed, 2.5, "must include bounded shutdown, not the 30s RPC")
        self.assertEqual(before, {p.pid for p in multiprocessing.active_children()})
        self.assertIsNone(current_deadline())

    def test_success_reuses_transport_and_caps_socket_timeout(self):
        with NetworkDeadline(5) as deadline:
            self.assertEqual(deadline.call(fake_rpc, "one"), "one")
            process = deadline.process
            self.assertEqual(deadline.call(fake_rpc, "two"), "two")
            self.assertIs(deadline.process, process)
            self.assertGreater(deadline.call(report_socket_timeout), 0)
            self.assertLess(deadline.call(report_socket_timeout), 5)
            with patch.object(deadline, "call", return_value={"result": "ok"}) as call:
                self.assertEqual(utils._make_single_rpc_call("https://fake", "eth_call", []), {"result": "ok"})
                self.assertEqual(call.call_args.kwargs["timeout"], 30)

    def test_backoff_stops_at_deadline_without_fallback(self):
        started = time.monotonic()
        with patch.object(utils, "_make_single_rpc_call", side_effect=utils.RPCError(
            "rate limited", error_type="rate_limit", retry_after=60
        )) as call:
            with self.assertRaises(NetworkDeadlineExceeded):
                with NetworkDeadline(0.15):
                    utils.rpc_call_with_retry("primary", "eth_call", [], fallback_urls=["backup"])
        self.assertEqual(call.call_count, 1)
        self.assertLess(time.monotonic() - started, 0.6)

    def test_retry_then_success_and_fallback_preserve_budget(self):
        with NetworkDeadline(3):
            with patch.object(utils, "_make_single_rpc_call", side_effect=[
                utils.NetworkError("offline"), {"result": "ok"}
            ]) as call, patch.object(utils.random, "uniform", return_value=0):
                self.assertEqual(utils.rpc_call_with_retry("primary", "eth_call", []), {"result": "ok"})
                self.assertEqual(call.call_count, 2)
            with patch.object(utils, "_make_single_rpc_call", side_effect=[
                utils.RPCError("bad", error_type="invalid_request"), {"result": "backup"}
            ]) as call:
                result = utils.rpc_call_with_retry("primary", "eth_call", [], fallback_urls=["backup"])
                self.assertEqual(result, {"result": "backup"})
                self.assertEqual(call.call_args.args[0], "backup")

    def test_cancellation_interrupts_backoff(self):
        cancel = threading.Event()
        timer = threading.Timer(0.1, cancel.set)
        timer.start()
        started = time.monotonic()
        try:
            with self.assertRaises(NetworkDeadlineExceeded):
                with NetworkDeadline(20, cancel):
                    retry_sleep(60)
        finally:
            timer.join()
        self.assertLess(time.monotonic() - started, 0.6)

    def test_invalid_budgets(self):
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                NetworkDeadline(timeout)


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.priority = SimpleNamespace(timeout_multiplier=1, weight=1,
                                        tier=SimpleNamespace(value=1, name="HIGH"))
        self.networks = {key: {"name": key, "rpc": "https://fake/" + key,
                               "pool": "0xpool"} for key in ("fast", "slow")}
        self.stack.enter_context(patch.object(aave_fetcher, "get_active_networks", return_value=self.networks))
        self.stack.enter_context(patch("network_prioritization.get_prioritized_networks",
            side_effect=lambda networks: [(k, v, self.priority) for k, v in networks.items()]))
        self.stack.enter_context(patch("network_prioritization.get_execution_strategy", return_value={
            "mode": "normal", "max_workers": 2, "timeout_multiplier": 1}))
        self.record = self.stack.enter_context(patch("network_prioritization.record_network_performance"))
        self.stack.enter_context(patch("performance_cache.performance_cache.save"))
        self.stack.enter_context(patch("performance_cache.get_cached_reserve_list", return_value=["asset"]))
        self.stack.enter_context(patch("performance_cache.cache_symbol"))
        self.stack.enter_context(patch.object(aave_fetcher.PerformanceMonitor, "print_performance_report"))
        self.stack.enter_context(patch.object(aave_fetcher, "log_network_summary"))

    def test_slow_rpc_does_not_delay_success_or_shutdown(self):
        def fetch(fetcher, key, config, **kwargs):
            return current_deadline().call(fake_rpc,
                [{"symbol": "OK", "asset_address": "asset"}], delay=30 if key == "slow" else 0)
        with patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch):
            started = time.monotonic()
            data, report = aave_fetcher.fetch_data_with_parallel_processing(2, 1.5)
        self.assertEqual(set(data), {"fast"})
        self.assertEqual(report["total_assets"], 1)
        self.assertEqual(report["successful_networks"], 1)
        self.assertLess(time.monotonic() - started, 2.5)
        self.assertEqual(self.record.call_count, 2)

    def test_queue_time_excluded_and_worker_limit_honored(self):
        active = 0
        peak = 0
        def fetch(fetcher, key, config, **kwargs):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            retry_sleep(0.12)
            active -= 1
            return [{"symbol": key}]
        with patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch):
            data, _ = aave_fetcher.fetch_data_with_parallel_processing(1, 0.2)
        self.assertEqual(set(data), {"fast", "slow"})
        self.assertEqual(peak, 1)

    def test_strategy_and_priority_adjust_the_active_budget(self):
        self.priority.timeout_multiplier = 2
        def fetch(fetcher, key, config, **kwargs):
            retry_sleep(0.12)
            return [{"symbol": key}]
        with patch("network_prioritization.get_execution_strategy", return_value={
            "mode": "normal", "max_workers": 2, "timeout_multiplier": 2
        }), patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch):
            data, _ = aave_fetcher.fetch_data_with_parallel_processing(2, 0.05)
        self.assertEqual(set(data), {"fast", "slow"})

    def test_global_cancellation_keeps_previously_completed_networks(self):
        started = time.monotonic()
        def fetch(fetcher, key, config, **kwargs):
            if key == "slow":
                retry_sleep(20)
            return [{"symbol": key}]
        with patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch), \
             patch.object(aave_fetcher.PerformanceMonitor, "is_approaching_limit",
                          side_effect=lambda: time.monotonic() - started > 0.2):
            data, report = aave_fetcher.fetch_data_with_parallel_processing(2, 20)
        self.assertEqual(set(data), {"fast"})
        self.assertEqual(report["total_assets"], 1)
        self.assertEqual(report["cancelled_networks"], ["slow"])
        self.assertLess(time.monotonic() - started, 0.7)

    def test_global_limit_cancels_running_transport_and_queued_work(self):
        started = time.monotonic()
        def fetch(fetcher, key, config, **kwargs):
            return current_deadline().call(fake_rpc, [], delay=30)
        with patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch), \
             patch.object(aave_fetcher.PerformanceMonitor, "is_approaching_limit",
                          side_effect=lambda: time.monotonic() - started > 1):
            data, report = aave_fetcher.fetch_data_with_parallel_processing(1, 20)
        self.assertEqual(data, {})
        self.assertEqual(report["cancelled_networks"], ["fast", "slow"])
        self.assertLess(time.monotonic() - started, 2)
        self.assertFalse(multiprocessing.active_children())

    def test_partial_asset_failure_keeps_successful_assets(self):
        self.networks.pop("slow")
        with patch("performance_cache.get_cached_reserve_list", return_value=["good", "bad"]), \
             patch.object(graceful_fetcher, "get_reserves", return_value=["good", "bad"]), \
             patch.object(graceful_fetcher, "get_asset_symbol", return_value="OK"), \
             patch.object(graceful_fetcher, "get_reserve_data", side_effect=[{"ltv": 50}, RuntimeError("bad asset")]):
            data, report = aave_fetcher.fetch_data_with_parallel_processing(1, 2)
        self.assertEqual(len(data["fast"]), 1)
        self.assertEqual(data["fast"][0]["asset_address"], "good")
        self.assertEqual(report["total_assets"], 1)

    def test_uncached_reserve_lookup_uses_same_deadline(self):
        self.networks.pop("slow")
        def reserves(*args):
            retry_sleep(0.1)
            return ["asset"]
        def fetch(fetcher, key, config, **kwargs):
            retry_sleep(0.15)
            return [{"symbol": "too late"}]
        with patch("performance_cache.get_cached_reserve_list", return_value=None), \
             patch("performance_cache.cache_reserve_list"), \
             patch.object(aave_fetcher, "get_reserves", side_effect=reserves), \
             patch.object(graceful_fetcher.GracefulDataFetcher, "fetch_network_data", fetch):
            started = time.monotonic()
            data, _ = aave_fetcher.fetch_data_with_parallel_processing(1, 0.2)
        self.assertEqual(data, {})
        self.assertLess(time.monotonic() - started, 0.6)


if __name__ == "__main__":
    unittest.main()
