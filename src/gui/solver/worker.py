"""One background solver at a time, with nonblocking replacement/cancellation."""

import copy
import queue
import threading

from .result import make_result, validate_result


class SolverWorker:
    """Call start/cancel/discard/poll from the GUI thread.

    Keep only the newest pending request; poll launches it after the old thread
    exits. Never join a running thread on the GUI. Solvers must cooperate with
    cancel_event to release the execution slot.
    """

    def __init__(self, solve_fn):
        self._solve_fn = solve_fn
        self._results = queue.Queue()
        self._thread = None
        self._active_cancel = None
        self._pending = None
        self._current = None
        self._cancelled_run = None
        self.run_id = 0

    def start(self, game_map, state, algorithm, timeout_s=60.0):
        self.discard()
        request = (self.run_id, copy.deepcopy(game_map), copy.deepcopy(state),
                   algorithm, timeout_s, threading.Event())
        self._current = self._pending = request
        self._launch_pending()
        return self.run_id

    def _launch_pending(self):
        if self._thread is not None and self._thread.is_alive():
            return
        if self._pending is None:
            return
        request, self._pending = self._pending, None
        run_id, game_map, snapshot, algorithm, timeout_s, cancel_event = request
        self._active_cancel = cancel_event

        def target():
            try:
                result = self._solve_fn(copy.deepcopy(game_map), copy.deepcopy(snapshot), algorithm,
                                        timeout_s=timeout_s,
                                        cancel_event=cancel_event)
                if result is None:
                    raise ValueError("solver returned no result")
            except Exception as error:
                result = make_result(game_map, snapshot, algorithm, timeout_s,
                                     "ERROR", str(error) or type(error).__name__)
            self._results.put((run_id, result))

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def cancel(self):
        """Cancel cooperatively, including success queued before this request.

        Keep the GUI in CANCELLING until active work returns, so its measured
        search statistics can be retained. A pending job can be cancelled now.
        """
        request = self._current
        if request is None or self._cancelled_run == self.run_id:
            return
        self._cancelled_run = self.run_id
        request[-1].set()
        if self._pending is not None:
            self._pending = None
            _, game_map, snapshot, algorithm, timeout_s, _ = request
            result = make_result(game_map, snapshot, algorithm, timeout_s, "CANCELLED")
            self._results.put((self.run_id, result))

    def discard(self):
        """Cancel active/pending work and silently drop eventual results."""
        if self._active_cancel is not None:
            self._active_cancel.set()
        if self._current is not None:
            self._current[-1].set()
        self._pending = self._current = None
        self._cancelled_run = None
        self.run_id += 1

    def poll(self):
        """Pump pending work and return only the current run's result."""
        self._launch_pending()
        latest = None
        while True:
            try:
                run_id, result = self._results.get_nowait()
            except queue.Empty:
                return latest
            if run_id == self.run_id:
                if self._cancelled_run == run_id:
                    _, game_map, snapshot, algorithm, timeout_s, _ = self._current
                    cancelled = make_result(game_map, snapshot, algorithm, timeout_s, "CANCELLED")
                    try:
                        measured = validate_result(result, game_map, snapshot, algorithm, timeout_s)
                    except (ValueError, TypeError, OverflowError, RecursionError):
                        pass
                    else:
                        for name in ("search_time_s", "peak_memory_bytes", "expanded_nodes"):
                            cancelled["metrics"][name] = measured["metrics"][name]
                    result = cancelled
                    self._cancelled_run = None
                latest = result
                self._current = None
