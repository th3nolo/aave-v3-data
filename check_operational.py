#!/usr/bin/env python3
"""Validate public daily artifacts and optionally smoke-test three configured chains."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

import requests

from src.networks import get_active_networks
from src.operational_check import (
    BoundedRPC, NETWORK_TIMEOUT, SAMPLE_NETWORKS, check_artifact, check_network,
    read_response,
)

PUBLIC_ARTIFACTS = {
    "raw": "https://raw.githubusercontent.com/th3nolo/aave-v3-data/main/aave_v3_data.json",
    "pages": "https://th3nolo.github.io/aave-v3-data/aave_v3_data.json",
}


def worker(kind: str) -> int:
    payload = json.load(sys.stdin)
    if kind == "download":
        for attempt in range(2):
            try:
                with requests.get(PUBLIC_ARTIFACTS[payload["source"]], timeout=5,
                                  stream=True, allow_redirects=False) as response:
                    document = read_response(response)
                print(json.dumps({"document": document}))
                return 0
            except (requests.RequestException, ValueError):
                if attempt == 1:
                    print(json.dumps({"error": "public artifact unavailable or invalid JSON"}))
        return 1
    config = get_active_networks()[payload["network"]]
    result = check_network(config, payload["assets"], BoundedRPC(config))
    print(json.dumps(result))
    return 0


def bounded_worker(kind: str, payload: dict, timeout: float) -> dict:
    """Kill and reap the child on timeout, including DNS/slow-drip HTTP stalls."""
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", kind],
            input=json.dumps(payload), text=True, encoding="utf-8", capture_output=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "fail", "issues": [{"kind": "provider_unavailable", "detail": "hard wall-clock deadline exceeded; worker killed and reaped"}]}
    try:
        body = json.loads(result.stdout)
    except ValueError:
        body = None
    if not isinstance(body, dict) or (result.returncode and "error" not in body):
        return {"status": "fail", "issues": [{"kind": "checker_error", "detail": f"worker failed (exit {result.returncode}); inspect code/runtime"}]}
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=PUBLIC_ARTIFACTS, default="raw")
    parser.add_argument("--artifact", type=Path, help="Check a local JSON instead of downloading")
    parser.add_argument("--live", action="store_true", help="Read-only Ethereum, Arbitrum and Base RPC smoke")
    parser.add_argument("--output", type=Path, default=Path("operational_local_report.json"))
    parser.add_argument("--worker", choices=("download", "network"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    now = datetime.now(timezone.utc)
    report: dict = {"checked_at": now.isoformat(), "source": str(args.artifact) if args.artifact else PUBLIC_ARTIFACTS[args.source],
                    "live_requested": args.live, "live": {}, "sample_networks": list(SAMPLE_NETWORKS)}
    document = None
    try:
        if args.artifact:
            document = json.loads(args.artifact.read_text(encoding="utf-8"))
        else:
            downloaded = bounded_worker("download", {"source": args.source}, 15)
            if "document" not in downloaded:
                report["artifact"] = {"status": "fail", "issues": downloaded.get("issues", [{"kind": "artifact_unavailable", "detail": downloaded.get("error", "missing artifact")}])}
            else:
                document = downloaded["document"]
        if "artifact" not in report:
            report["artifact"] = check_artifact(document, set(get_active_networks()), now)
    except (OSError, ValueError):
        report["artifact"] = {"status": "fail", "issues": [{"kind": "schema", "detail": "cannot read local JSON artifact"}]}
    if args.live:
        malformed = any(issue["kind"] == "schema" for issue in report["artifact"]["issues"])
        for network in SAMPLE_NETWORKS:
            assets = document.get("networks", {}).get(network) if isinstance(document, dict) and isinstance(document.get("networks"), dict) else None
            if malformed or not isinstance(assets, list) or not assets:
                report["live"][network] = {"status": "fail", "issues": [{"kind": "missing_coverage", "detail": "cannot safely check missing/malformed artifact reserves"}]}
            else:
                report["live"][network] = bounded_worker("network", {"network": network, "assets": assets}, NETWORK_TIMEOUT)
    passed = report["artifact"]["status"] == "pass" and all(result["status"] == "pass" for result in report["live"].values())
    report["status"] = "pass" if passed else "fail"
    report["live_coverage"] = {
        "required_networks": len(SAMPLE_NETWORKS) if args.live else 0,
        "passed_networks": sum(result["status"] == "pass" for result in report["live"].values()),
        "checked_reserves": sum(len(result.get("sampled_reserves", [])) for result in report["live"].values()),
        "scope": "full reserve sets and two token identities per sampled network; other networks receive artifact checks only",
    }
    rendered = json.dumps(report, indent=2)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
