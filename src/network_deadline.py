"""Cooperative network budgets with a killable boundary for blocking RPC I/O.

Socket timeouts are inactivity limits, not wall-clock deadlines (DNS and a
trickling response can exceed them). A transport process per active network
keeps that I/O out of executor threads. Only JSON-RPC transport runs there;
decoding, retries, caches and monitoring remain in the parent.
"""

from contextvars import ContextVar
import math
import multiprocessing
import threading
import time


class NetworkDeadlineExceeded(TimeoutError):
    """The network budget expired or orchestration cancelled its work."""


_current = ContextVar("network_deadline", default=None)
POLL_INTERVAL = 0.05
SHUTDOWN_GRACE = 0.2


def current_deadline():
    return _current.get()


def check_deadline():
    deadline = current_deadline()
    if deadline is not None:
        deadline.remaining()


def retry_sleep(seconds):
    deadline = current_deadline()
    if deadline is None:
        time.sleep(seconds)
    else:
        wake_at = time.monotonic() + seconds
        while True:
            remaining = deadline.remaining()
            delay = wake_at - time.monotonic()
            if delay <= 0:
                return
            # Event.wait may return slightly early (notably on Windows).
            # Recheck both clocks instead of starting the next RPC early.
            deadline.cancel.wait(min(delay, remaining))


def _transport_worker(connection):
    """Spawn-safe worker; never inherits a thread's deadline context."""
    try:
        while True:
            request = connection.recv()
            if request is None:
                return
            function, args, kwargs = request
            try:
                connection.send((True, function(*args, **kwargs)))
            except Exception as exc:
                connection.send((False, exc))
    except (EOFError, BrokenPipeError):
        pass
    finally:
        connection.close()


class NetworkDeadline:
    """Budget starts on worker entry; queued time is excluded.

    Context exit reaps the transport, allowing at most two shutdown grace
    periods. Cancelling a Future alone cannot interrupt running I/O.
    """

    def __init__(self, seconds, cancel=None):
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("Network timeout must be finite and positive")
        self.expires = time.monotonic() + seconds
        self.cancel = cancel if cancel is not None else threading.Event()
        self.process = None
        self.connection = None

    def __enter__(self):
        self.token = _current.set(self)
        return self

    def remaining(self):
        remaining = self.expires - time.monotonic()
        if self.cancel.is_set() or remaining <= 0:
            raise NetworkDeadlineExceeded("Network deadline exceeded or cancelled")
        return remaining

    def call(self, function, *args, **kwargs):
        self.remaining()
        if self.process is None:
            context = multiprocessing.get_context("spawn")
            self.connection, child_connection = context.Pipe()
            self.process = context.Process(
                target=_transport_worker, args=(child_connection,), daemon=True
            )
            try:
                self.process.start()
            finally:
                child_connection.close()
        kwargs["timeout"] = min(kwargs.get("timeout", 30), self.remaining())
        self.connection.send((function, args, kwargs))
        while not self.connection.poll(min(POLL_INTERVAL, self.remaining())):
            if not self.process.is_alive():
                raise RuntimeError("RPC transport process exited without a response")
        succeeded, result = self.connection.recv()
        self.remaining()  # Never accept a late result, even from a slow fake RPC.
        if not succeeded:
            raise result
        return result

    def __exit__(self, exc_type, exc, traceback):
        _current.reset(self.token)
        if self.connection is not None:
            self.connection.close()
        if self.process is not None and self.process.pid is not None:
            # No unbounded join: stop even a resolver/read ignoring its timeout.
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(SHUTDOWN_GRACE)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(SHUTDOWN_GRACE)
            if self.process.is_alive():
                raise RuntimeError("RPC transport did not exit after termination")
            self.process.close()
