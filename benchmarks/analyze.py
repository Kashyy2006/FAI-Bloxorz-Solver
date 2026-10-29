"""Verify a real benchmark and generate report-ready measurements and plots.

Raw report.json/runs.csv/summary.csv are never modified. Run with the matching
source checkout; source and map hashes are checked before engine replay.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean, median

from benchmarks.run import ROOT, _validate_result
from src.contracts import ALGORITHMS
from src.engine import (is_goal, load_map, state_from_dict, step_cost,
                        transition, Status)
from src.solvers.costs.calc import heuristic_name

METRICS = ("search_time_s", "peak_memory_bytes", "expanded_nodes",
           "solution_length", "solution_cost")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(report_path, chart_dir):
    report_path, chart_dir = Path(report_path).resolve(), Path(chart_dir).resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    env = report["environment"]
    date_label = datetime.fromisoformat(env["created_at"]).astimezone(timezone(timedelta(hours=7))).date().isoformat()
    if not report["complete"] or report["readiness"]:
        raise ValueError("Benchmark is incomplete or has readiness issues")
    for relative, expected in env["source_sha256"].items():
        if digest(ROOT / relative) != expected:
            raise ValueError(f"Source changed since measurement: {relative}")
    inventory_path = Path(env["inventory_path"])
    if digest(inventory_path) != env["inventory_sha256"]:
        raise ValueError("Inventory changed since measurement")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    groups = {entry["id"]: entry.get("group", "other") for entry in inventory["maps"]}
    cases = {case["map_id"]: case for case in report["cases"]}
    models = {}
    for map_id, case in cases.items():
        path = Path(case["map_path"])
        if digest(path) != case["map_sha256"]:
            raise ValueError(f"Map changed since measurement: {map_id}")
        models[map_id] = load_map(path)

    pairs = {(map_id, algo): [] for map_id in cases for algo in ALGORITHMS}
    details = []
    for record in report["runs"]:
        map_id, algo = record["map_id"], record["algorithm"]
        case, model = cases[map_id], models[map_id]
        result = _validate_result(record["result"], case, algo, env["timeout_s"])
        expected_h = (heuristic_name(model, case["start_state"]["mode"] == "SPLIT")
                      if algo == "ASTAR" else None)
        if result["heuristic"] != expected_h:
            raise ValueError(f"Heuristic metadata differs: {map_id}/{algo}")
        pairs[(map_id, algo)].append(record)
        detail = {"map_id": map_id, "algorithm": algo,
                  "run_index": record["run_index"], "status": result["status"],
                  "replay_checked": False}
        if result["status"] == "SOLVED":
            state = state_from_dict(model, result["start_state"])
            cost = 0
            for action in result["actions"]:
                edge = transition(model, state, action)
                if edge.status not in (Status.OK, Status.WON):
                    raise ValueError(f"Replay failed: {map_id}/{algo}: {edge.reason}")
                cost += step_cost(model, state, action, edge.next_state)
                state = edge.next_state
            metrics = result["metrics"]
            if (not is_goal(model, state) or cost != metrics["solution_cost"]
                    or len(result["actions"]) != metrics["solution_length"]):
                raise ValueError(f"Replay goal/length/cost mismatch: {map_id}/{algo}")
            detail.update(replay_checked=True, verified_cost=cost,
                          verified_length=len(result["actions"]))
        details.append(detail)

    for key, records in pairs.items():
        if sorted(record["run_index"] for record in records) != [1, 2, 3]:
            raise ValueError(f"Expected three unique trials: {key}")
        values = [record["result"] for record in records]
        # Timing/memory can fluctuate. Search outcome and deterministic path data
        # should remain stable under the fixed input/order for each algorithm.
        signatures = {(value["status"], tuple(value["actions"] or []),
                       value["metrics"]["expanded_nodes"],
                       value["metrics"]["solution_length"], value["metrics"]["solution_cost"])
                      for value in values}
        if len(signatures) != 1:
            raise ValueError(f"Search outcomes differ between repetitions: {key}")

    paired_ids = [map_id for map_id in cases if all(
        all(r["result"]["status"] == "SOLVED" for r in pairs[(map_id, algo)])
        for algo in ALGORITHMS)]
    if not paired_ids:
        raise ValueError("No common solved maps for a fair aggregate comparison")
    per_map = []
    for (map_id, algo), records in pairs.items():
        solved = [r["result"] for r in records if r["result"]["status"] == "SOLVED"]
        per_map.append({"map_id": map_id, "group": groups[map_id], "algorithm": algo,
                        "heuristic": records[0]["result"]["heuristic"],
                        "status": records[0]["result"]["status"],
                        "recorded_runs": len(records),
                        **{metric: median(r["metrics"][metric] for r in solved) if solved else None
                           for metric in METRICS}})
    lookup = {(row["map_id"], row["algorithm"]): row for row in per_map}
    for map_id in paired_ids:
        if lookup[(map_id, "ASTAR")]["solution_cost"] != lookup[(map_id, "UCS")]["solution_cost"]:
            raise ValueError(f"A*/UCS cost mismatch: {map_id}")
        if any(lookup[(map_id, "BFS")]["solution_length"] > lookup[(map_id, algo)]["solution_length"]
               for algo in ALGORITHMS):
            raise ValueError(f"BFS length invariant failed: {map_id}")
    aggregate = [{"algorithm": algo, "common_solved_maps": len(paired_ids),
                  **{metric: mean(lookup[(map_id, algo)][metric] for map_id in paired_ids)
                     for metric in METRICS}} for algo in ALGORITHMS]
    verification = {
        "report_sha256": digest(report_path), "analysis_source_sha256": digest(Path(__file__)),
        "source_and_inventory_hashes_match": True, "all_map_hashes_match": True,
        "runs_checked": len(details), "solved_replays_checked": sum(d["replay_checked"] for d in details),
        "status_counts": dict(Counter(d["status"] for d in details)),
        "three_trials_per_pair": True, "deterministic_outcomes": True,
        "astar_ucs_costs_match_on_common_solved_maps": True,
        "bfs_has_minimum_length_on_common_solved_maps": True,
        "scope": "SOLVED replay checks prove path legality/goal/length/cost, not an independent proof of UNSOLVABLE",
        "details": details,
    }
    out = report_path.parent
    (out / "verification.json").write_text(json.dumps(verification, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    write_csv(out / "per_map_medians.csv", per_map)
    write_csv(out / "aggregate.csv", aggregate)
    write_latex(out / "report_tables.tex", aggregate, date_label)
    draw_charts(chart_dir, paired_ids, lookup, env["code_commit"][:7], date_label)
    names = Counter(lookup[(map_id, "ASTAR")]["heuristic"] for map_id in cases)
    faster = sum(lookup[(m, "ASTAR")]["search_time_s"] < lookup[(m, "UCS")]["search_time_s"] for m in paired_ids)
    fewer = sum(lookup[(m, "ASTAR")]["expanded_nodes"] < lookup[(m, "UCS")]["expanded_nodes"] for m in paired_ids)
    dfs_fastest = sum(lookup[(m, "DFS")]["search_time_s"] == min(lookup[(m, a)]["search_time_s"] for a in ALGORITHMS) for m in paired_ids)
    discussion = (
        f"Trên {len(paired_ids)} map giải được chung, A* và UCS trả cùng chi phí tối ưu. "
        f"A* mở rộng ít nút hơn UCS trên {fewer}/{len(paired_ids)} map, nhưng chỉ nhanh hơn trên "
        f"{faster}/{len(paired_ids)} map. Chi phí tính heuristic và tiền xử lý được tính vào thời gian tìm kiếm; "
        "giảm số nút mở rộng không bảo đảm giảm thời gian thực thi. "
        f"DFS nhanh nhất trên {dfs_fastest}/{len(paired_ids)} map trong phiên đo này, nhưng không bảo đảm "
        "lời giải ngắn nhất hay chi phí thấp nhất. Các chênh lệch thời gian là quan sát từ ba lượt đo, "
        "chưa phải kết luận có ý nghĩa thống kê."
    )
    (out / "discussion.tex").write_text("% Generated from the matching benchmark report.\n" + discussion + "\n", encoding="utf-8")
    rows = ["| Thuật toán | Time (ms) | Peak Python (MiB) | Expanded | Length | Cost |",
            "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in aggregate:
        rows.append(f"| {row['algorithm']} | {row['search_time_s']*1000:.2f} | "
                    f"{row['peak_memory_bytes']/2**20:.4f} | {row['expanded_nodes']:.2f} | "
                    f"{row['solution_length']:.2f} | {row['solution_cost']:.2f} |")
    text = f"""# Benchmark đồng bộ heuristic ngày {date_label}

- Commit nguồn: `{env['code_commit']}`; `code_dirty={str(env['code_dirty']).lower()}`.
  Trạng thái working tree được ghi tại lúc đo; hash từng file thực thi nằm trong report.json.
- Python: `{env['python'].splitlines()[0]}`; hệ điều hành: `{env['platform']}`.
- CPU: `{env['processor']}`; số logical CPU: {env['logical_cpus']}.
- Thời điểm UTC: `{env['created_at']}`; không dùng cấu hình máy của phiên báo cáo cũ.
- {len(cases)} map × 4 solver × 3 lượt = {len(details)} lượt; timeout 60 giây; spawn riêng và chạy tuần tự.
- Trạng thái: `{verification['status_counts']}`; readiness issues: {len(report['readiness'])}.
- Đã replay qua engine {verification['solved_replays_checked']} lời giải SOLVED: đúng goal, length và cost.
- Kiểm tra hash nguồn/map, metadata heuristic, ba lượt/cặp, dữ liệu đường đi ổn định,
  cost A*/UCS và length BFS: đạt. Không dùng expected_solvable để sinh kết quả.
- Phân bố heuristic A*: `{dict(names)}`.

## Bảng tổng hợp

Chỉ dùng {len(paired_ids)} map có 3/3 lượt SOLVED cho **cả bốn thuật toán**.
Mỗi ô là trung bình cộng của các trung vị theo map; không phải trung vị của toàn bộ lượt.
Length gồm SWITCH; peak là tracemalloc Python, không phải RSS. Thời gian và peak
A* bao gồm tiền xử lý; expanded không gồm đồ thị tiền xử lý.

""" + "\n".join(rows) + "\n\n## Nhận xét theo phiên đo\n\n" + discussion + """

## File bàn giao

- `report.json`, `runs.csv`, `summary.csv`, `readiness.csv`: dữ liệu runner gốc, không sửa sau đo.
- `verification.json`: hash report và các kiểm tra replay/invariant theo từng lượt.
- `per_map_medians.csv`: 72 cặp map/thuật toán, trạng thái, heuristic và trung vị SOLVED (N/A nếu vô nghiệm).
- `aggregate.csv`: trung bình các trung vị trên tập map giải được chung.
- `report_tables.tex`: bảng LaTeX để thay bảng số liệu cũ trong báo cáo; chưa sửa PDF ngoài repo.
- `discussion.tex`: nhận xét so sánh được tính từ chính phiên đo này.
- Biểu đồ PNG/SVG nằm trong thư mục cùng tên ở `benchmarks/charts/`.

Kết quả này thay cho số liệu A* dùng quy tắc cũ khi mô tả phiên bản hiện tại.
Không trộn thời gian/bộ nhớ giữa các cấu hình máy hay các phiên đo.
Không thay đổi trọng số cost, bộ map hoặc tên heuristic JSON trong lượt đồng bộ này.
Executable cũ chưa được build lại và không đại diện cho phiên đo này.

Tái lập phân tích: `python -m benchmarks.analyze --report PATH/report.json --charts CHART_DIR`.
Cần matplotlib để xuất hình; phân tích từ chối source/map không khớp phiên đo.
"""
    (out / "README.md").write_text(text, encoding="utf-8")
    print(f"Verified {len(details)} trials and {verification['solved_replays_checked']} solved replays.")
    print("\n".join(rows))


def write_latex(path, rows, date_label):
    lines = [r"% Generated from the matching benchmark report; do not mix with older measurements.",
             r"\begin{table}[htbp]", r"\centering\small",
             r"\begin{tabular}{lrrrrr}\hline",
             r"Thuật toán & Time (ms) & Peak (MiB) & Expanded & Length & Cost \\\hline"]
    for row in rows:
        values = (row["search_time_s"]*1000, row["peak_memory_bytes"]/2**20,
                  row["expanded_nodes"], row["solution_length"], row["solution_cost"])
        formatted = [f"{value:.{4 if i == 1 else 2}f}".replace(".", ",") for i, value in enumerate(values)]
        lines.append(row["algorithm"].replace("ASTAR", "A*")+" & "+" & ".join(formatted)+r" \\")
    lines += [r"\hline\end{tabular}",
              r"\caption{Phiên đo " + date_label + r": trung bình các trung vị theo map có nghiệm chung, ba lượt mỗi cặp.}",
              r"\label{tab:benchmark-heuristic-update}", r"\end{table}"]
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def draw_charts(output, map_ids, lookup, commit, date_label):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    colors = ("#2563a6", "#bd8700", "#cd543d", "#8b4c9a")
    markers = ("o", "s", "^", "D")
    specs = (("search_time_s", "search_time", "Search time (ms)", 1000),
             ("peak_memory_bytes", "peak_memory", "Peak Python memory (MiB)", 1/2**20),
             ("expanded_nodes", "expanded_nodes", "Expanded nodes (A* preprocessing excluded)", 1),
             ("solution_length", "solution_length", "Solution length (actions, including SWITCH)", 1),
             ("solution_cost", "solution_cost", "Total solution cost", 1))
    for metric, filename, title, scale in specs:
        fig, ax = plt.subplots(figsize=(8.5, 9.5))
        for i, algo in enumerate(ALGORITHMS):
            xs = [lookup[(map_id, algo)][metric]*scale for map_id in map_ids]
            ys = [j+(i-1.5)*.12 for j in range(len(map_ids))]
            ax.scatter(xs, ys, label=algo.replace("ASTAR", "A*"), color=colors[i], marker=markers[i], s=38)
        ax.set_yticks(range(len(map_ids)), map_ids, fontsize=11)
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlabel(title+"; logarithmic scale", fontsize=11)
        ax.set_title(title, fontsize=14, pad=35)
        ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncols=4, frameon=False)
        ax.grid(axis="x", which="both", alpha=.2)
        ax.set_axisbelow(True)
        fig.text(.03, .015, f"Median of 3 trials per map/algorithm | source {commit} | {date_label}\n"
                 "Python tracemalloc peak, not RSS. A* time/peak include preprocessing.", fontsize=9)
        fig.tight_layout(rect=(0, .055, 1, 1))
        fig.savefig(output / f"{filename}.png", dpi=220)
        fig.savefig(output / f"{filename}.svg")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--charts", required=True, type=Path)
    args = parser.parse_args()
    analyze(args.report, args.charts)


if __name__ == "__main__":
    main()
