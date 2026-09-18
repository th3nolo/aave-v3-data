"""Read-only artifact and bounded RPC checks; no transaction methods or discovery."""

from __future__ import annotations

import json
import math
import re
import time
from datetime import datetime, timezone

import requests

ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
SAMPLE_NETWORKS = ("ethereum", "arbitrum", "base")
MAX_REQUESTS = 20
REQUEST_TIMEOUT = 5
NETWORK_TIMEOUT = 45
MAX_BODY = 4_000_000


class ProviderUnavailable(Exception):
    """Transport, RPC protocol, or budget prevented verification."""


def check_artifact(document: object, expected: set[str], now: datetime) -> dict:
    """Validate the published envelope, timestamps and internally stated coverage."""
    issues: list[dict[str, str]] = []

    def issue(kind: str, detail: str) -> None:
        issues.append({"kind": kind, "detail": detail})

    if not isinstance(document, dict):
        return {"status": "fail", "issues": [{"kind": "schema", "detail": "root must be an object"}]}
    metadata = document.get("metadata")
    networks = document.get("networks")
    if not isinstance(metadata, dict) or not isinstance(networks, dict):
        return {"status": "fail", "issues": [{"kind": "schema", "detail": "metadata/networks must be objects"}]}
    if metadata.get("schema_version") != "aave-v3-2025":
        issue("schema", "unsupported or absent schema_version")
    age = None
    try:
        generated = datetime.fromisoformat(metadata["generated_at"])
        if generated.tzinfo is None:
            raise ValueError("timezone required")
        age = (now - generated).total_seconds()
        if age > 36 * 3600:
            issue("stale", "generated_at is older than the 36-hour daily publication SLA")
        if age < -300:
            issue("schema", "generated_at is more than five minutes in the future")
        timestamp = metadata["generated_timestamp"]
        if type(timestamp) is not int or abs(timestamp - generated.timestamp()) > 1:
            issue("schema", "generated_timestamp disagrees with generated_at")
    except (KeyError, TypeError, ValueError, OverflowError):
        issue("schema", "invalid generated timestamp or timezone")
    missing = sorted(expected - networks.keys())
    extra = sorted(networks.keys() - expected)
    if missing:
        issue("partial", f"missing configured networks: {missing}")
    if extra:
        issue("schema", f"unexpected networks: {extra}")
    total_assets = 0
    for network, assets in networks.items():
        if not isinstance(assets, list) or not assets:
            issue("partial", f"{network}: absent or empty reserve list")
            continue
        total_assets += len(assets)
        seen: set[str] = set()
        for asset in assets:
            if not isinstance(asset, dict):
                issue("schema", f"{network}: reserve must be an object")
                continue
            for field in ("asset_address", "a_token_address", "variable_debt_token_address"):
                value = asset.get(field)
                if not isinstance(value, str) or not ADDRESS.fullmatch(value) or int(value[2:], 16) == 0:
                    issue("schema", f"{network}: invalid {field}")
            address = str(asset.get("asset_address", "")).lower()
            if address in seen:
                issue("partial", f"{network}: duplicate reserve {address}")
            seen.add(address)
            if not isinstance(asset.get("symbol"), str) or not asset["symbol"].strip():
                issue("schema", f"{network}: missing symbol")
            if type(asset.get("decimals")) is not int or not 0 <= asset["decimals"] <= 255:
                issue("schema", f"{network}: invalid decimals")
            for field in ("loan_to_value", "liquidation_threshold", "liquidation_bonus", "current_liquidity_rate", "current_variable_borrow_rate"):
                value = asset.get(field)
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    issue("schema", f"{network}: invalid {field}")
                elif field in ("loan_to_value", "liquidation_threshold") and value > 1:
                    issue("schema", f"{network}: {field} exceeds one")
            for field in ("active", "frozen", "borrowing_enabled", "stable_borrowing_enabled", "paused", "borrowable_in_isolation", "siloed_borrowing"):
                if type(asset.get(field)) is not bool:
                    issue("schema", f"{network}: invalid {field}")
            for field in ("supply_cap", "borrow_cap", "debt_ceiling", "emode_category", "last_update_timestamp"):
                if type(asset.get(field)) is not int or asset[field] < 0:
                    issue("schema", f"{network}: invalid {field}")
    summary = metadata.get("network_summary", {})
    successful = sum(isinstance(assets, list) and bool(assets) for assets in networks.values())
    counts = {"total_active_networks": len(expected), "successful_networks": successful,
              "failed_networks": len(expected) - successful, "total_assets": total_assets}
    if not isinstance(summary, dict) or any(type(summary.get(k)) is not int or summary[k] != v for k, v in counts.items()):
        issue("schema", "network_summary counts disagree with configured networks/payload")
    listed = metadata.get("networks")
    if not isinstance(listed, list) or sorted(str(n) for n in listed) != sorted(networks):
        issue("schema", "metadata network list disagrees with payload")
    return {"status": "pass" if not issues else "fail", "age_seconds": age,
            "networks": len(networks), "reserves": total_assets, "issues": issues}


def read_response(response: requests.Response) -> object:
    """Bound decoded response bytes, including compressed responses."""
    response.raise_for_status()
    content = bytearray()
    for chunk in response.iter_content(65536):
        content.extend(chunk)
        if len(content) > MAX_BODY:
            raise ValueError("response exceeds byte budget")
    return json.loads(content)


class BoundedRPC:
    """Two configured endpoints, one attempt each, twenty total HTTP requests."""

    def __init__(self, config: dict) -> None:
        self.urls = [config["rpc"], *config.get("rpc_fallback", [])][:2]
        self.requests = 0
        self.failures: list[dict[str, str]] = []

    def call(self, method: str, params: list) -> object:
        if method not in {"eth_chainId", "eth_getBlockByNumber", "eth_getCode", "eth_call"}:
            raise ValueError("read-only method allowlist")
        for index, url in enumerate(self.urls):
            if self.requests >= MAX_REQUESTS:
                raise ProviderUnavailable("request budget exhausted")
            self.requests += 1
            try:
                with requests.post(url, json={"jsonrpc": "2.0", "id": self.requests,
                                             "method": method, "params": params},
                                   timeout=REQUEST_TIMEOUT, stream=True, allow_redirects=False) as response:
                    body = read_response(response)
                if not isinstance(body, dict) or body.get("id") != self.requests or body.get("jsonrpc") != "2.0" or "error" in body or "result" not in body:
                    raise ValueError("invalid/error JSON-RPC response")
                return body["result"]
            except (requests.RequestException, ValueError) as exc:
                # Do not expose exception URLs, credentials or provider response bodies.
                self.failures.append({"endpoint": str(index), "method": method, "reason": type(exc).__name__})
                if index + 1 < len(self.urls):
                    time.sleep(0.1)
        raise ProviderUnavailable(f"providers unavailable for {method}")


def words(value: object) -> list[str]:
    if not isinstance(value, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{64})+", value):
        raise ProviderUnavailable("malformed ABI response")
    return [value[i:i + 64].lower() for i in range(2, len(value), 64)]


def reserve_list(value: object) -> set[str]:
    decoded = words(value)
    if len(decoded) < 2 or int(decoded[0], 16) != 32:
        raise ProviderUnavailable("malformed reserve array offset")
    count = int(decoded[1], 16)
    if not 0 < count <= 1024 or len(decoded) != count + 2:
        raise ProviderUnavailable("malformed/empty reserve array")
    if any(int(word[:24], 16) or int(word, 16) == 0 for word in decoded[2:]):
        raise ProviderUnavailable("malformed reserve address")
    addresses = {"0x" + word[-40:] for word in decoded[2:]}
    if len(addresses) != count:
        raise ProviderUnavailable("duplicate on-chain reserves")
    return addresses


def check_network(config: dict, assets: list[dict], rpc: BoundedRPC) -> dict:
    """Compare complete reserve sets plus two identities at a single sampled block."""
    issues: list[dict[str, str]] = []
    evidence: dict = {"status": "fail", "issues": issues, "sampled_reserves": []}
    try:
        if rpc.call("eth_chainId", []) != hex(config["chain_id"]):
            issues.append({"kind": "configuration_mismatch", "detail": "RPC chain ID differs from configuration"})
            return evidence
        header = rpc.call("eth_getBlockByNumber", ["latest", False])
        if not isinstance(header, dict) or not re.fullmatch(r"0x[0-9a-fA-F]+", str(header.get("number"))) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", str(header.get("hash"))):
            raise ProviderUnavailable("invalid block header")
        block = header["number"]
        evidence.update(block=block, block_hash=header["hash"])
        # Hash pinning also prevents fallback providers from serving another fork
        # at the same height (EIP-1898). Unsupported providers fail explicitly.
        block_ref = {"blockHash": header["hash"], "requireCanonical": True}
        code = rpc.call("eth_getCode", [config["pool"], block_ref])
        if not isinstance(code, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", code):
            issues.append({"kind": "configuration_mismatch", "detail": "configured pool has no valid contract code"})
            return evidence
        def call(to: str, data: str) -> object:
            return rpc.call("eth_call", [{"to": to, "data": data}, block_ref])
        reserves = reserve_list(call(config["pool"], "0xd1946dbc"))
        published = {asset["asset_address"].lower() for asset in assets}
        evidence.update(onchain_reserves=len(reserves), published_reserves=len(published))
        if reserves != published:
            issues.append({"kind": "coverage_mismatch", "detail": f"missing={sorted(reserves - published)}, removed={sorted(published - reserves)}; inspect listing changes since publication"})
        samples = sorted(assets, key=lambda a: (a["symbol"] not in ("USDC", "WETH"), a["asset_address"]))[:2]
        if len(samples) < 2:
            issues.append({"kind": "partial", "detail": "two representative reserves required"})
        for asset in samples:
            address = asset["asset_address"].lower()
            if address not in reserves:
                continue
            decimals = words(call(address, "0x313ce567"))
            data = words(call(config["pool"], "0x35ea6a75" + address[2:].zfill(64)))
            if len(decimals) != 1 or len(data) < 12:
                raise ProviderUnavailable("truncated reserve ABI")
            mismatches = []
            if int(decimals[0], 16) != asset["decimals"]:
                mismatches.append("decimals")
            for field, index in (("a_token_address", 8), ("variable_debt_token_address", 10)):
                if "0x" + data[index][-40:] != asset[field].lower():
                    mismatches.append(field)
            evidence["sampled_reserves"].append(address)
            if mismatches:
                issues.append({"kind": "invariant_mismatch", "detail": f"{address}: {mismatches}; investigate decoder/configuration or contract upgrade"})
        final_header = rpc.call("eth_getBlockByNumber", [block, False])
        if not isinstance(final_header, dict) or final_header.get("hash") != header["hash"]:
            raise ProviderUnavailable("block changed during verification")
    except ProviderUnavailable as exc:
        issues.append({"kind": "provider_unavailable", "detail": str(exc)})
    finally:
        evidence.update(requests=rpc.requests, provider_failures=rpc.failures)
    evidence["status"] = "pass" if not issues else "fail"
    return evidence
