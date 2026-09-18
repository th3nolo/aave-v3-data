# Default/parallel network deadlines

`python aave_fetcher.py --parallel --timeout 120 --max-workers 4` uses a
120-second **base** budget. Each network receives the base multiplied by the
execution strategy's timeout multiplier and the network priority multiplier.
The budget starts when a worker begins that network, excluding queue time.
`--max-workers` caps simultaneous network workers, even if the strategy allows
more. The global collection limit is checked while waiting, including when
no network has completed yet.

One monotonic deadline covers reserve discovery, asset RPC operations,
fallback endpoints, retry backoff, and transport startup. A timed-out network
is omitted from output rather than published as a successful snapshot.
Ordinary asset failures still preserve successfully fetched assets when the
network finishes within its budget. Completed networks survive another
network's timeout. Monitoring records deadline failures.

Socket timeouts alone do not bound a whole HTTP operation: DNS resolution or
a response that keeps trickling bytes can outlast them. In deadline mode,
each active network lazily creates one reusable transport process using
Python's standard-library `multiprocessing` spawn context. Only blocking
JSON-RPC transport runs there; retries, decoding, cache updates, and monitoring
remain in the network thread. Socket timeout values are capped to the remaining
budget. When the budget expires or collection is cancelled, the parent stops
the transport process. `Future.cancel()` is used only for queued work.

Transport shutdown uses a 0.2-second terminate/join grace, then a 0.2-second
kill/join grace if necessary. Cancellation is polled every 0.05 seconds.
These bounds include shutdown waiting, with normal scheduling and process
startup/termination overhead; they are not a hard real-time guarantee from the
operating system. A process that cannot be killed is reported as an error.
No running I/O is claimed to be interrupted by cancelling its thread future.

The deadline does not bound disk stalls, arbitrary custom Python code that
blocks outside the RPC transport, or later validation/output/governance work.
`--timeout` does not apply to `--sequential`, `--ultra-fast`, or `--turbo`.
The scheduled data workflow currently selects `--turbo`, so it does not use
this deadline implementation. Embedders must use the usual
`if __name__ == '__main__':` guard when starting multiprocessing workloads.

## Offline regression checks

With repository dependencies already installed in a Python environment:

```sh
uv run --no-project --python /path/to/python -m unittest tests.test_network_deadlines -v
```

The tests use deliberately slow fake functions and a loopback HTTP server,
including a trickling response, and assert elapsed time through shutdown and
absence of leftover transport processes. They cover success, partial asset
failure, retries, fallback, shared discovery/asset budgets, queue timing,
worker limits, and cancellation. They do not require a public RPC endpoint.

This change adds no third-party dependencies and does not alter
`requirements.txt` or dependency versions.
