from math import isfinite
from time import perf_counter
import tracemalloc

from src.solvers.common.result import SolverMetrics


def validate_timeout(timeout_s) -> float:
    try:
        if type(timeout_s) not in (int, float):
            raise ValueError
        value = float(timeout_s)
        if not isfinite(value) or value <= 0:
            raise ValueError
    except (ValueError, OverflowError):
        raise ValueError("timeout_s must be a finite number > 0") from None
    return value


class SearchStopped(Exception):
    def __init__(self, status):
        super().__init__(status)
        self.status = status


class SearchRuntime:
    """Control one sequential search; only stop tracing started by this instance."""

    def __init__(self, timeout_s=60.0, cancel_event=None, metrics=None):
        self.timeout_s = validate_timeout(timeout_s)
        if cancel_event is not None and not callable(getattr(cancel_event, "is_set", None)):
            raise ValueError("cancel_event must provide callable is_set()")
        self.cancel_event = cancel_event
        self.metrics = metrics if metrics is not None else SolverMetrics()
        self._started_at = None
        self._search_stopped = False
        self._owns_tracing = False
        self._finished = False

    def start(self):
        if self._started_at is not None or self._finished:
            raise RuntimeError("SearchRuntime can only be started once")
        # shortcut: sequential solves only; isolate workers before concurrent solving.
        if tracemalloc.is_tracing():
            raise RuntimeError("tracemalloc is already active; use an isolated solve process")
        tracemalloc.start()
        self._owns_tracing = True
        self._started_at = perf_counter()

    def check_stop(self):
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise SearchStopped("CANCELLED")
        if self._started_at is not None and perf_counter() - self._started_at >= self.timeout_s:
            raise SearchStopped("TIMEOUT")

    def mark_search_stopped(self):
        if self._started_at is not None and not self._search_stopped:
            self.metrics.search_time_s = perf_counter() - self._started_at
            self._search_stopped = True

    def finish(self):
        if self._finished:
            return
        self._finished = True
        try:
            self.mark_search_stopped()
        finally:
            if self._owns_tracing:
                try:
                    self.metrics.peak_memory_bytes = tracemalloc.get_traced_memory()[1]
                finally:
                    self._owns_tracing = False
                    tracemalloc.stop()
