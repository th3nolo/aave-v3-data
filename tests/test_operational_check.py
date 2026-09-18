"""Deterministic negative paths for operational assurance; no external traffic."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import requests

import check_operational as cli
from src.operational_check import (
    BoundedRPC, MAX_REQUESTS, ProviderUnavailable, check_artifact, check_network,
    read_response, reserve_list,
)

NOW = datetime(2026, 9, 18, 12, tzinfo=timezone.utc)
POOL = "0x" + "11" * 20
TOKEN = "0x" + "22" * 20
ATOKEN = "0x" + "33" * 20
DEBT = "0x" + "44" * 20
TOKEN2 = "0x" + "55" * 20
CONFIG = {"chain_id": 1, "pool": POOL, "rpc": "https://synthetic.invalid", "rpc_fallback": ["https://fallback.invalid"]}


def encoded(values):
    return "0x" + "".join(format(value, "064x") for value in values)


def artifact():
    assets = [{"asset_address": token, "symbol": symbol, "decimals": 18,
               "a_token_address": ATOKEN, "variable_debt_token_address": DEBT,
               "loan_to_value": 0.7, "liquidation_threshold": 0.8,
               "liquidation_bonus": 0.05, "current_liquidity_rate": 0,
               "current_variable_borrow_rate": 0,
               **{field: False for field in ("active", "frozen", "borrowing_enabled", "stable_borrowing_enabled", "paused", "borrowable_in_isolation", "siloed_borrowing")},
               **{field: 0 for field in ("supply_cap", "borrow_cap", "debt_ceiling", "emode_category", "last_update_timestamp")}}
              for token, symbol in ((TOKEN, "WETH"), (TOKEN2, "USDC"))]
    return {"metadata": {"schema_version": "aave-v3-2025", "generated_at": NOW.isoformat(),
                         "generated_timestamp": int(NOW.timestamp()), "networks": ["ethereum"],
                         "network_summary": {"total_active_networks": 1, "successful_networks": 1,
                                             "failed_networks": 0, "total_assets": 2}},
            "networks": {"ethereum": assets}}


class FixtureRPC:
    def __init__(self):
        self.requests = 0
        self.failures = []
        self.calls = []
        self.header = {"number": "0x123", "hash": "0x" + "ab" * 32}
        self.decimals = 18
        self.reserves = [int(TOKEN, 16), int(TOKEN2, 16)]
        self.reorg = False

    def call(self, method, params):
        self.calls.append((method, params))
        self.requests += 1
        if method == "eth_chainId":
            return "0x1"
        if method == "eth_getBlockByNumber":
            if self.reorg and params[0] != "latest":
                return {**self.header, "hash": "0x" + "cd" * 32}
            return self.header
        if method == "eth_getCode":
            return "0x6000"
        data = params[0]["data"]
        if data == "0xd1946dbc":
            return encoded([32, len(self.reserves), *self.reserves])
        if data == "0x313ce567":
            return encoded([self.decimals])
        return encoded([0] * 8 + [int(ATOKEN, 16), 0, int(DEBT, 16), 0])


class ArtifactTests(unittest.TestCase):
    def validate(self, document, now=NOW):
        return check_artifact(document, {"ethereum"}, now)

    def test_fresh_valid_payload(self):
        self.assertEqual(self.validate(artifact())["status"], "pass")

    def test_stale_and_future(self):
        self.assertEqual(self.validate(artifact(), NOW + timedelta(hours=37))["issues"][0]["kind"], "stale")
        self.assertEqual(self.validate(artifact(), NOW - timedelta(minutes=6))["status"], "fail")

    def test_naive_invalid_or_inconsistent_timestamp(self):
        for value in (None, "bad", "2026-09-18T12:00:00", "2025-09-18T12:00:00+00:00"):
            with self.subTest(value=value):
                doc = artifact()
                doc["metadata"]["generated_at"] = value
                self.assertEqual(self.validate(doc)["status"], "fail")

    def test_malformed_roots_and_envelopes(self):
        for doc in (None, [], {}, {"metadata": [], "networks": {}}, {"metadata": {}, "networks": []}):
            self.assertEqual(self.validate(doc)["status"], "fail")

    def test_network_missing_empty_and_duplicate_reserve(self):
        for assets in (None, [], [artifact()["networks"]["ethereum"][0]] * 2):
            doc = artifact()
            doc["networks"]["ethereum"] = assets
            result = self.validate(doc)
            self.assertEqual(result["status"], "fail")
            self.assertIn("partial", [issue["kind"] for issue in result["issues"]])
        doc = artifact()
        del doc["networks"]["ethereum"]
        self.assertIn("partial", [issue["kind"] for issue in self.validate(doc)["issues"]])

    def test_schema_bad_address_boolean_decimal_nan_and_counts(self):
        for field, value in (("asset_address", "0x123"), ("a_token_address", "0x" + "0" * 40),
                             ("decimals", True), ("loan_to_value", float("nan")), ("symbol", ""),
                             ("active", "true"), ("supply_cap", -1), ("loan_to_value", 2)):
            doc = artifact()
            doc["networks"]["ethereum"][0][field] = value
            self.assertEqual(self.validate(doc)["status"], "fail")
        for field, value in (("network_summary", []), ("networks", []), ("schema_version", "future")):
            doc = artifact()
            doc["metadata"][field] = value
            self.assertEqual(self.validate(doc)["status"], "fail")


class LiveCheckerTests(unittest.TestCase):
    def test_identities_at_one_block_without_rate_comparison(self):
        rpc = FixtureRPC()
        assets = artifact()["networks"]["ethereum"]
        assets[0]["current_liquidity_rate"] = 999
        result = check_network(CONFIG, assets, rpc)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(len(result["sampled_reserves"]), 2)
        self.assertLessEqual(result["requests"], MAX_REQUESTS)
        self.assertTrue(all(params[-1] == {"blockHash": rpc.header["hash"], "requireCanonical": True} for method, params in rpc.calls if method in ("eth_call", "eth_getCode")))

    def test_missing_reserves_fail_even_when_network_is_nonempty(self):
        rpc = FixtureRPC()
        rpc.reserves.append(12345)
        result = check_network(CONFIG, artifact()["networks"]["ethereum"], rpc)
        self.assertEqual(result["issues"][0]["kind"], "coverage_mismatch")

    def test_identity_mismatch(self):
        rpc = FixtureRPC()
        rpc.decimals = 6
        result = check_network(CONFIG, artifact()["networks"]["ethereum"], rpc)
        self.assertEqual(result["issues"][0]["kind"], "invariant_mismatch")

    def test_wrong_chain_is_configuration_failure(self):
        result = check_network({**CONFIG, "chain_id": 2}, artifact()["networks"]["ethereum"], FixtureRPC())
        self.assertEqual(result["issues"][0]["kind"], "configuration_mismatch")

    def test_reorg_and_provider_failure_never_pass(self):
        rpc = FixtureRPC()
        rpc.reorg = True
        result = check_network(CONFIG, artifact()["networks"]["ethereum"], rpc)
        self.assertEqual(result["issues"][-1]["kind"], "provider_unavailable")
        rpc.call = Mock(side_effect=ProviderUnavailable("offline"))
        self.assertEqual(check_network(CONFIG, [], rpc)["status"], "fail")

    def test_malformed_array_rejected(self):
        for value in ("0x", "0xzz", encoded([32, 0]), encoded([0, 1, 1]), encoded([32, 2, 1]), encoded([32, 2, 1, 1])):
            with self.subTest(value=value), self.assertRaises(ProviderUnavailable):
                reserve_list(value)

    @patch("src.operational_check.time.sleep")
    @patch("src.operational_check.requests.post", side_effect=requests.Timeout)
    def test_timeout_retries_and_total_budget(self, post, sleep):
        rpc = BoundedRPC(CONFIG)
        for _ in range(12):
            with self.assertRaises(ProviderUnavailable):
                rpc.call("eth_chainId", [])
        self.assertEqual(post.call_count, MAX_REQUESTS)
        self.assertEqual(len(rpc.failures), MAX_REQUESTS)
        self.assertEqual(post.call_args.kwargs["timeout"], 5)
        with self.assertRaises(ValueError):
            rpc.call("eth_sendRawTransaction", [])
        self.assertEqual(post.call_count, MAX_REQUESTS)

    @patch("src.operational_check.time.sleep")
    @patch("src.operational_check.requests.post")
    def test_rpc_error_and_wrong_response_id_are_unavailable(self, post, sleep):
        response = post.return_value.__enter__.return_value
        for body in ({"jsonrpc": "2.0", "id": 1, "error": {}}, {"jsonrpc": "2.0", "id": 999, "result": "0x1"}):
            response.iter_content.return_value = [json.dumps(body).encode()]
            with self.assertRaises(ProviderUnavailable):
                BoundedRPC(CONFIG).call("eth_chainId", [])

    def test_response_byte_budget(self):
        response = Mock()
        response.iter_content.return_value = [b"x" * 4_000_001]
        with self.assertRaises(ValueError):
            read_response(response)


class CLITests(unittest.TestCase):
    def test_real_stalled_child_is_killed_and_reaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            sleeper = Path(tmp) / "sleeper.py"
            sleeper.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
            started = time.monotonic()
            with patch.object(cli, "__file__", str(sleeper)):
                result = cli.bounded_worker("download", {}, 0.2)
            self.assertLess(time.monotonic() - started, 5)
            self.assertEqual(result["issues"][0]["kind"], "provider_unavailable")

    @patch("check_operational.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 1))
    def test_hard_timeout_reports_unavailable(self, run):
        self.assertEqual(cli.bounded_worker("network", {}, 1)["issues"][0]["kind"], "provider_unavailable")

    @patch("check_operational.subprocess.run")
    def test_crashed_worker_is_code_error(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, stdout="", stderr="traceback")
        self.assertEqual(cli.bounded_worker("network", {}, 1)["issues"][0]["kind"], "checker_error")

    def test_cli_missing_networks_cannot_silently_skip_live_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            output = Path(tmp) / "report.json"
            source.write_text(json.dumps({"metadata": {}, "networks": {}}))
            with patch("sys.argv", ["check_operational.py", "--artifact", str(source), "--live", "--output", str(output)]), patch("builtins.print"):
                self.assertEqual(cli.main(), 1)
            report = json.loads(output.read_text())
            self.assertEqual(set(report["live"]), set(cli.SAMPLE_NETWORKS))
            self.assertTrue(all(result["status"] == "fail" for result in report["live"].values()))


if __name__ == "__main__":
    unittest.main()
