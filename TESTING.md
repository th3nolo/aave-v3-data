# Offline regression gate

Use Python 3.12 or 3.13 and uv:

```sh
uv venv --python 3.12
uv pip sync --require-hashes --only-binary :all: requirements.lock
uv pip check
uv run --no-project --no-sync python run_offline_tests.py
```

The runner discovers **every `tests/test_*.py` unittest**, including the real
loopback HTTP and subprocess deadline tests. There is no passing-test allowlist.
External DNS/connections are rejected before network access, including in Python
workers. Attempted access makes the command fail even if application code catches
the exception. Skips, expected failures, empty discovery and assertion failures
also fail the gate. Synthetic subprocess tests verify these properties.

Root-level `test_*.py`, `test_runner.py`, and `run_all_tests.py` are older manual
diagnostics: some fetch live RPC data or inspect generated production snapshots.
They are not covered by the offline gate and their success is not claimed here.
Live integration checks must be explicitly invoked with appropriate endpoints;
never add credentials or public RPC dependencies to the offline suite.

The PR workflow runs this same command on Linux and Windows with Python 3.12/3.13.
Its Actions are pinned to verified upstream commits, and uv to 0.8.22. The daily
data workflow installs the same runtime lock; its live fetch is not a unit test.

## Why the legacy tests changed

- RPC tests now patch the function/module used by callers (`utils.rpc_call_with_retry`),
  supply real response status/context-manager semantics, and distinguish transport
  `NetworkError` from protocol `RPCError`. Assertions still check errors, retry counts,
  classification, fallback propagation and decoded values.
- Fixtures use the actual method selectors and encode a 5% liquidation bonus as
  10500 basis points (the total multiplier). Aave's LiquidationLogic applies this
  using `percentMul(liquidationBonus)`, not a bare 500-basis-point multiplier:
  https://github.com/aave/aave-v3-core/blob/master/contracts/protocol/libraries/logic/LiquidationLogic.sol
- Output assertions use the documented `networks` envelope and displayed percentages.
  Text is read as UTF-8. Permission-error tests inject the OS error deterministically,
  rather than relying on host privilege or chmod behavior.
- Discovery tests use synthetic address-book content and assert the discovered
  network instead of merely asserting that no exception occurred.

The tests exposed production bugs, which are repaired instead of accepted:
classified RPC errors were rewrapped as unknown, malformed validator structures
were dereferenced after being rejected, and damaged `USD` symbols were relabeled
as `USDT`. Bonus conversion now subtracts integer basis points before division,
avoiding floating-point cancellation.

Cross-platform CI also exposed an early-returning timed wait on Windows. Backoff
now rechecks the monotonic wake time instead of starting another RPC early; a
deterministic fake-clock regression preserves the one-call deadline assertion.
The monitoring test scopes its clock mock to its module so Python 3.12 logging
does not consume the fake response-time values.

## Dependencies

`requirements.txt` records the direct Requests requirement. `requirements.lock`
pins the complete five-package runtime closure with PyPI SHA-256 hashes. Existing
lockfiles were not replaced. Before installation, package names, upstream links,
versions, upload dates, yanked status and PyPI-reported advisories were checked on
2026-09-18. Every selected release was older than 72 hours; none had advisories
listed in that metadata. This is not a guarantee of absence of vulnerabilities.

Requests 2.33.0 fixes the .netrc issue (GHSA-9hjg-9r4m-mvj7) and the subsequently
reported zipped-path issue. urllib3 2.7.0 and idna 3.15 avoid advisories listed for
the older candidate transitives. A synthetic .netrc test proves crafted URL
userinfo cannot select a different host's credentials; it makes no HTTP request.
Environment proxies and normal matching-host authentication remain supported.

The separate traffic-analytics workflow's pandas/tooling dependencies are outside
this fetcher lock and have not been audited by this change.

## Operational assurance for the daily turbo publication

The daily `update-aave-data.yml` runs `aave_fetcher.py --turbo` and publishes the
JSON only after `check_operational.py --artifact aave_v3_data.json` passes.
This gate checks the supported schema, addresses/types, timezone-aware timestamp
(36-hour maximum age, five-minute future tolerance), configured network coverage,
nonempty/unique reserves and metadata counts. A fresh timestamp alone does not
establish reserve completeness: turbo can return a nonempty partial reserve list.

Run the independent public check with the existing locked environment:

```sh
uv run --no-project --no-sync python check_operational.py --live
uv run --no-project --no-sync python check_operational.py --source pages
```

`operational-check.yml` runs the first command daily at 06:30 UTC, manually, and
on checker PRs. It has read-only repository permissions and never invokes the
publisher. The JSON report is printed in logs and copied into the job summary,
including on failure. Every missing required sample or provider outage exits 1;
the job must not be interpreted as passing when no report exists. Local output
defaults to ignored `operational_local_report.json`; `--output` selects another
path. Without `--live`, success is artifact validation only.

The live scope is exactly Ethereum, Arbitrum and Base, using their configured
primary and first fallback public RPCs. For each chain, compare the complete
on-chain reserve address set with the publication and sample two reserves
(prefer USDC/WETH) for decimals and aToken/variable-debt-token identity. Calls
use a single block hash with EIP-1898 canonical enforcement, and recheck the
block hash at the end. Rates and mutable risk parameters from different blocks
are deliberately not compared. No historical scan or transaction is performed.
The other configured networks receive artifact validation, not live attestation.

Budgets: two artifact HTTP attempts in a 15-second subprocess; at most 20 RPC
HTTP attempts per network, five-second socket timeouts, one fallback attempt per
call, four MB decoded response size, and a hard 45-second subprocess deadline
per chain. Timed-out workers are killed and reaped, bounding DNS and slow-drip
responses too. The complete check normally uses 27 RPC requests and is bounded
by 150 seconds of child execution plus process/report overhead. CI has a separate
five-minute job cap including environment setup.

Interpret report issues before deciding on a repair:

- `stale`: inspect the latest daily fetch/push workflow and artifact timestamp;
  restore daily publication, then rerun the check.
- `partial` / `missing_coverage`: inspect the named missing network/reserve data;
  do not accept an empty or skipped sample as success.
- `coverage_mismatch`: compare the listed missing/removed reserve addresses with
  protocol listing changes since the artifact timestamp; rerun the fetch.
- `provider_unavailable` / `artifact_unavailable`: inspect provider attempt details
  and rerun when service returns. This is incomplete assurance, not proof of a
  fetcher defect. EIP-1898 support is required; no silent weaker fallback is used.
- `schema`, `configuration_mismatch`, `invariant_mismatch`: inspect the named
  field, configuration, decoder or contract upgrade before changing code. An
  observation mismatch is evidence to investigate, not an automatic bug diagnosis.
- `checker_error`: the worker crashed or returned an invalid result; fix the
  checker/runtime and repeat the required coverage.

`tests/test_operational_check.py` exercises synthetic fresh/stale/future and
malformed artifacts, missing/duplicate coverage, wrong chains, reserve-list and
identity mismatches, block changes, provider timeouts/errors, retry/request/byte
budgets, worker failures and missing CLI coverage. These deterministic tests run
in the offline gate; only explicitly invoked RPC checks provide live evidence.
