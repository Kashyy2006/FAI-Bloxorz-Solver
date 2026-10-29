"""Sequential, spawn-isolated benchmark runs; solvers own search measurements."""

import argparse
import csv
from dataclasses import fields
from datetime import datetime, timezone
import hashlib
import importlib
import json
import multiprocessing
from multiprocessing.reduction import ForkingPickler
import os
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from src.engine.models import State
from src.solvers.common.result import SolverMetrics, SolverResult, snapshot_to_dict
from src.solvers.common.runtime import validate_timeout

from src.contracts import ALGORITHMS, STATUSES, COST_MODEL
from src.solvers.common.schema import validate_payload
METRICS = tuple(field.name for field in fields(SolverMetrics))


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _snapshot(raw, bridge_ids):
    if not isinstance(raw, dict) or set(raw) != {"mode", "cells", "active", "bridges"}:
        raise ValueError("snapshot requires mode, cells, active, bridges")
    bridges = raw["bridges"]
    if not isinstance(bridges, dict) or set(bridges) != set(bridge_ids):
        raise ValueError("snapshot bridge IDs must match the map")
    state = State(raw["mode"], raw["cells"], raw["active"],
                  tuple(bridges[bid] for bid in bridge_ids))
    canonical = snapshot_to_dict(state, bridge_ids)
    if raw != canonical:
        raise ValueError("snapshot cells must be canonical JSON coordinates")
    return canonical


def _validate_result(raw, case, algorithm, timeout_s):
    if not isinstance(raw, dict) or set(raw) != {f.name for f in fields(SolverResult)}:
        raise ValueError("SolverResult must have exactly 11 contract fields")
    validate_payload(raw)
    if raw["algorithm"] != algorithm:
        raise ValueError("algorithm does not match the requested run")
    for name, expected in (("map_id", case["map_id"]),
                           ("start_state", case["start_state"]), ("timeout_s", timeout_s)):
        if raw[name] != expected and not (raw["status"] == "ERROR" and raw[name] is None):
            raise ValueError(f"{name} does not match the requested run")
    if raw["start_state"] is not None:
        _snapshot(raw["start_state"], tuple(case["start_state"]["bridges"]))
    metrics = raw["metrics"]
    if set(metrics) != set(METRICS):
        raise ValueError("metrics must have exactly five contract fields")
    actions = raw["actions"]
    result = SolverResult(**{
        k: v for k, v in raw.items() if k not in ("schema_version", "cost_model", "metrics")
    }, metrics=SolverMetrics(**metrics)).to_dict()
    if raw["status"] == "SOLVED" and not actions and any(metrics.values()):
        raise ValueError("already solved start must have five zero measurements")
    _json(result)
    return result


def _worker(binding, case, timeout_s, destination):
    stage = "binding"
    try:
        if isinstance(binding, str):
            module, name = binding.split(":")
            binding = getattr(importlib.import_module(module), name)
        if not callable(binding):
            raise ValueError("binding must be callable or module:function")
        stage = "input"
        path = Path(case["map_path"])
        if _hash(path.read_bytes()) != case["map_sha256"]:
            raise ValueError("map bytes changed before the run")
        stage = "solve"
        raw = binding(path, case["start_state"], timeout_s=timeout_s)
        stage = "result"
        if isinstance(raw, SolverResult):
            raw = raw.to_dict()
        if _hash(path.read_bytes()) != case["map_sha256"]:
            raise ValueError("map bytes changed during the run")
        message = {"result": raw}
        _json(message)
    except Exception as exc:
        message = {"issue": f"{stage}_error", "error": f"{type(exc).__name__}: {exc}"}
    Path(destination).write_text(_json(message), encoding="utf-8")


def _run_one(binding, case, timeout_s, process_grace_s):
    context = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix="bloxorz-benchmark-") as temporary:
        destination = Path(temporary) / "result.json"
        process = context.Process(target=_worker, args=(binding, case, timeout_s, destination))
        started = perf_counter()
        try:
            ForkingPickler.dumps(binding)
            process.start()
            process.join(timeout_s + process_grace_s)
            if process.is_alive():
                process.terminate()
                process.join(5)
                if process.is_alive():
                    process.kill()
                    process.join()
                message = {"issue": "process_error", "error": "process wall limit exceeded"}
            elif process.exitcode != 0 or not destination.exists():
                message = {"issue": "process_error", "error": f"process exit code {process.exitcode}; no usable result"}
            else:
                message = json.loads(destination.read_text(encoding="utf-8"))
            message.update(worker_pid=process.pid, exitcode=process.exitcode,
                           wall_time_s=perf_counter() - started)
            return message
        except Exception as exc:
            return {"issue": "process_error", "error": f"{type(exc).__name__}: {exc}",
                    "worker_pid": process.pid, "exitcode": process.exitcode,
                    "wall_time_s": perf_counter() - started}
        finally:
            if process.is_alive():
                process.terminate()
                process.join()
            process.close()


def _load_cases(inventory, root):
    content = Path(inventory).read_bytes()
    entries = json.loads(content)["maps"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("inventory.maps must be a nonempty list")
    cases, seen = [], set()
    for entry in entries:
        map_id = entry["id"]
        if not isinstance(map_id, str) or not map_id.strip() or map_id in seen:
            raise ValueError("inventory IDs must be nonempty and unique")
        seen.add(map_id)
        path = (Path(root) / entry["path"]).resolve()
        data = path.read_bytes()
        digest = _hash(data)
        if digest != entry["sha256"]:
            raise ValueError(f"{map_id}: map SHA256 differs from inventory")
        game_map = json.loads(data)
        if game_map["id"] != map_id:
            raise ValueError(f"{map_id}: map ID differs from inventory")
        bridges = game_map["bridges"]
        bridge_ids = tuple(sorted(bridge["id"] for bridge in bridges))
        if len(set(bridge_ids)) != len(bridge_ids):
            raise ValueError(f"{map_id}: duplicate bridge IDs")
        raw_snapshot = entry.get("start_state", {
            "mode": "UPRIGHT", "cells": [game_map["start"]], "active": None,
            "bridges": {bridge["id"]: bridge["initial_open"] for bridge in bridges},
        })
        snapshot = _snapshot(raw_snapshot, bridge_ids)
        cases.append({"map_id": map_id, "map_path": str(path), "map_sha256": digest,
                      "start_state": snapshot,
                      "snapshot_sha256": _hash(_json(snapshot).encode("utf-8"))})
    return cases, _hash(content)


def _environment():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "machine": platform.node(), "platform": platform.platform(),
        "processor": platform.processor(), "logical_cpus": os.cpu_count(),
        "python": sys.version, "python_executable": sys.executable,
        "code_commit": git("rev-parse", "HEAD"),
        "code_dirty": bool(git("status", "--porcelain")),
        "source_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): _hash(path.read_bytes())
            for path in sorted([*ROOT.glob("src/**/*.py"), Path(__file__)])
        },
        "timeout_s": 60.0, "runs_per_pair": 3, "process_start_method": "spawn",
        "search_measurements": "solver perf_counter/tracemalloc; wall_time_s is separate",
        "replay_validation": "not_performed_by_runner",
    }


def _summary(cases, algorithms, runs, readiness):
    rows = []
    for case in cases:
        for algorithm in algorithms:
            pair = [r["result"] for r in runs
                    if r["map_id"] == case["map_id"] and r["algorithm"] == algorithm]
            solved = [r for r in pair if r["status"] == "SOLVED"]
            row = {"map_id": case["map_id"], "algorithm": algorithm,
                   "expected_runs": 3, "recorded_runs": len(pair),
                   "readiness_issues": sum(r["map_id"] == case["map_id"]
                                           and r["algorithm"] == algorithm for r in readiness)}
            row.update({status: sum(r["status"] == status for r in pair) for status in STATUSES})
            row.update({f"median_{name}": median(r["metrics"][name] for r in solved)
                        if solved else None for name in METRICS})
            rows.append(row)
    return rows


def _write_csv(path, rows, columns):
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(inventory, bindings, output, *, root=ROOT, algorithms=ALGORITHMS,
                  process_grace_s=30.0):
    """Run three trials at 60s per pair; bindings accept (path, snapshot, *, timeout_s)."""
    algorithms = tuple(algorithms)
    if not algorithms or len(set(algorithms)) != len(algorithms) or any(
        algorithm not in ALGORITHMS for algorithm in algorithms
    ):
        raise ValueError("algorithms must be unique BFS/DFS/UCS/ASTAR names")
    if set(bindings) - set(ALGORITHMS):
        raise ValueError("unknown binding algorithm")
    process_grace_s = validate_timeout(process_grace_s)
    cases, inventory_sha256 = _load_cases(inventory, root)
    environment = _environment()
    environment.update(inventory_path=str(Path(inventory).resolve()),
                       inventory_sha256=inventory_sha256, process_grace_s=process_grace_s,
                       bindings={key: value if isinstance(value, str)
                                 else f"{getattr(value, '__module__', type(value).__module__)}:"
                                      f"{getattr(value, '__qualname__', type(value).__qualname__)}"
                                 for key, value in bindings.items()})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {"environment": environment, "cases": cases, "runs": [], "readiness": [],
              "summary": [], "complete": False}

    def save():
        report["summary"] = _summary(cases, algorithms, report["runs"], report["readiness"])
        temporary = output / "report.tmp"
        temporary.write_text(_json(report) + "\n", encoding="utf-8")
        temporary.replace(output / "report.json")

    save()
    for case in cases:
        for algorithm in algorithms:
            base = {"map_id": case["map_id"], "algorithm": algorithm,
                    "map_sha256": case["map_sha256"],
                    "snapshot_sha256": case["snapshot_sha256"]}
            if algorithm not in bindings:
                report["readiness"].append({**base, "run_index": None,
                    "issue": "missing_binding", "error": "caller must provide an engine/solver binding",
                    "worker_pid": None, "exitcode": None, "wall_time_s": None})
                save()
                continue
            for run_index in range(1, 4):
                message = _run_one(bindings[algorithm], case, 60.0, process_grace_s)
                if "result" in message:
                    try:
                        message["result"] = _validate_result(message["result"], case, algorithm, 60.0)
                    except Exception as exc:
                        message = {**message, "issue": "invalid_result",
                                   "error": f"{type(exc).__name__}: {exc}"}
                        message.pop("result")
                record = {**base, "run_index": run_index, **message}
                report["readiness" if "issue" in message else "runs"].append(record)
                save()
    columns = ["map_id", "algorithm", "map_sha256", "snapshot_sha256", "run_index",
               "worker_pid", "exitcode", "wall_time_s"]
    flat = []
    for record in report["runs"]:
        result = record["result"]
        flat.append({**{k: v for k, v in record.items() if k != "result"},
                     "status": result["status"], **result["metrics"],
                     "result_json": _json(result)})
    _write_csv(output / "runs.csv", flat, columns + ["status", *METRICS, "result_json"])
    _write_csv(output / "readiness.csv", report["readiness"], columns + ["issue", "error"])
    _write_csv(output / "summary.csv", report["summary"], list(report["summary"][0]))
    report["complete"] = True
    save()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/map_bundle.json")
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="base directory for inventory map paths")
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    parser.add_argument("--algorithms", nargs="+", choices=ALGORITHMS, default=ALGORITHMS)
    parser.add_argument("--binding", action="append", default=[], metavar="ALGORITHM=MODULE:FUNCTION")
    parser.add_argument("--process-grace-s", type=float, default=30.0)
    args = parser.parse_args(argv)
    bindings = {}
    for binding in args.binding:
        name, separator, target = binding.partition("=")
        if not separator or name not in ALGORITHMS or target.count(":") != 1 or name in bindings:
            parser.error("bindings must be unique ALGORITHM=MODULE:FUNCTION entries")
        bindings[name] = target
    try:
        report = run_benchmark(args.inventory, bindings, args.output, root=args.root,
                               algorithms=args.algorithms, process_grace_s=args.process_grace_s)
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    print(f"{len(report['runs'])} solver results; {len(report['readiness'])} readiness issues; {args.output}")
    return 1 if report["readiness"] else 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
