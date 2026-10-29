# benchmarks

**Lưu gì / làm gì:** Runner độc lập cho BFS, DFS, UCS và A*; nhận inventory và binding do bên gọi cung cấp, lưu kết quả từng lượt và bảng tổng hợp.

**Phụ trách:** Thành viên 4.

## Chạy trên Windows

Chỉ dùng thư viện chuẩn Python, không cần Pygame. Chạy từ gốc repo:

```powershell
python -m benchmarks.run --output benchmarks/results/readiness-check
```

Lệnh trên kiểm inventory mặc định `data/map_bundle.json`, gồm 18 map trong
`data/maps/`. Khi chưa truyền binding, runner ghi
72 cặp map/thuật toán vào bảng tình trạng với `missing_binding`, không chạy
solver và không tạo số đo. Exit code là 1 vì còn mục chưa chạy.

Khi bên tích hợp đã cung cấp module import được, ví dụ
`src.solvers.solve` có các hàm `run_bfs`/`run_dfs`, dùng:

```powershell
python -m benchmarks.run --inventory data/map_bundle.json --output benchmarks/results/bfs-dfs --algorithms BFS DFS --binding BFS=src.solvers.solve:run_bfs --binding DFS=src.solvers.solve:run_dfs
```

Module binding trong ví dụ đã có trong repo. Thêm `--binding UCS=src.solvers.solve:run_ucs` và
`--binding ASTAR=src.solvers.solve:run_astar` để chạy đủ bốn thuật toán. Thiếu binding
không được thay bằng solver giả. `python benchmarks/run.py ...` cũng được hỗ trợ.
Đường dẫn map trong inventory được tính từ gốc repo; đổi bằng `--root PATH`
khi dùng inventory ngoài repo. `--output` phải là thư mục mới để giữ kết quả cũ.

## Hợp đồng binding và inventory

Binding là hàm Python ở cấp module, có chữ ký:

```python
def run_bfs(map_path: Path, snapshot: dict, *, timeout_s: float):
    # Nạp map, chuyển snapshot và nối callback/metadata của engine tại đây.
    # Trả SolverResult hoặc dict đầy đủ theo solver contract.
    ...
```

Runner gọi binding trong tiến trình mới bằng phương thức `spawn` cho từng
lượt. Chuỗi `module:function` được import trong tiến trình đó; API Python
cũng nhận callable có thể pickle. Không dùng lambda/hàm cục bộ làm binding.
Không chạy tác vụ ở cấp module khi import. Chương trình gọi API phải đặt
lời gọi trong `if __name__ == "__main__":`:

```python
from benchmarks.run import run_benchmark

if __name__ == "__main__":
    report = run_benchmark(
        "data/map_bundle.json",
        {"BFS": "src.solvers.solve:run_bfs"},
        "benchmarks/results/bfs",
        algorithms=("BFS",),
    )
```

Binding chịu trách nhiệm:

- Dùng loader và validator ngữ nghĩa của engine thật; không dùng validator no-op.
- Chuyển đúng `mode/cells/active/bridges`, giữ snapshot giữa ván và cấu hình
  cầu; tuple bridge flags theo ID từ điển. Không reset về initial state.
- Gọi callable solver thật, truyền đủ callback và metadata bắt buộc. Với BFS/DFS,
  dùng [solve_bfs](../src/solvers/bfs/README.md) và
  [solve_dfs](../src/solvers/dfs/README.md); không truyền trực tiếp hai hàm này
  làm binding vì chữ ký nhận map/state đã nạp khác chữ ký binding.
- Giữ mốc `perf_counter`/`tracemalloc` theo
  [benchmark contract](../docs/contracts/benchmark.md), gồm overhead tracing.
  Binding/loader/validation không nằm trong `search_time_s`.
- Trả đúng map_id, algorithm, snapshot, timeout, cost model, heuristic và năm
  metrics. Với ERROR, envelope chưa xác thực có thể null theo
  [solver contract](../docs/contracts/solver.md). Runner giữ nguyên null.

Inventory là JSON có `maps`, mỗi phần tử chứa `id`, `path`, `sha256` và
tùy chọn `start_state` dạng JSON snapshot. Các metadata khác của manifest
được phép giữ nguyên. Runner kiểm ID duy nhất, ID trong file, SHA256 byte,
hình học snapshot và bridge IDs. Đây là kiểm tra cấu trúc, không thay engine
validator hoặc chứng minh map khả giải. Không sửa JSON map để thêm snapshot.

Khi không có `start_state`, runner chọn snapshot đầu map một cách tường minh:
UPRIGHT tại `start`, active=null, cầu theo `initial_open` và ID từ điển.
Nếu đã có snapshot nhưng sai/null, runner từ chối inventory trước khi tạo
output; không thay bằng initial state. Tất cả lượt và thuật toán của cùng
map nhận cùng snapshot. Hash snapshot là SHA256 của UTF-8
`json.dumps(snapshot, ensure_ascii=False, allow_nan=False, sort_keys=True)`.

## Chạy đo và đọc kết quả

- Chạy tuần tự, mỗi cặp đúng ba lượt, `run_index` từ 1 đến 3 và timeout tìm
  kiếm 60 giây; không có tùy chọn giảm số lượt/timeout cho số liệu bàn giao.
- Runner không bật tracemalloc hoặc tính lại metrics quanh binding. Solver
  sở hữu mốc đo search và peak Python; `wall_time_s` ghi riêng, gồm startup,
  import, loader và truyền kết quả, không dùng thay `search_time_s`.
- Giới hạn process mặc định 90 giây từ lúc bắt đầu tạo process: 60 giây cộng
  `--process-grace-s 30`. Nếu callback không hợp tác hoặc tổng thời gian vượt
  giới hạn, runner dừng process và ghi `process_error` cùng thời gian chờ thực
  tế/exit code. Đây không phải TIMEOUT của solver. Có thể tăng grace cho loader
  chậm; vẫn giữ timeout search 60 giây.
- Lỗi import/binding, ngoại lệ thoát khỏi callable, process crash và kết quả
  sai hợp đồng nằm trong `readiness`, không tạo SolverResult thay thế. ERROR
  do solver trả đúng hợp đồng vẫn là một lượt solver thật.
- `report.json` chứa môi trường máy/CPU/Python, commit/dirty flag, hash nguồn
  Python trong repo, hash inventory, từng map/snapshot, binding và toàn bộ
  SolverResult của mỗi lượt. Giữ mã binding cùng phiên bản code khi đo thật.
- `runs.csv` chứa mỗi lượt hợp lệ, năm metrics và `result_json` đầy đủ để
  round-trip null/snapshot/actions. `readiness.csv` ghi mục thiếu/lỗi riêng;
  `run_index` trống cho cặp chưa có binding. Giữ CSV cùng report để có môi trường đo.
- `summary.csv` và `report.summary` đếm đủ năm status, số lượt đã ghi/mục lỗi;
  trung vị năm metrics chỉ dùng SOLVED. Không có SOLVED thì JSON là null,
  CSV là ô trống (N/A), không dùng số 0 thay thế.
- Report được lưu sau mỗi lượt/mục thiếu. `complete=false` cho phiên bị ngắt;
  CSV chỉ hoàn thành cuối phiên. `complete=true` nghĩa runner đã duyệt xong,
  vẫn phải xem readiness và số status để biết cặp nào đủ dữ liệu. CLI trả 1
  khi có readiness issue, 0 khi mọi lời gọi đã trả kết quả đúng hợp đồng;
  status ERROR trong kết quả vẫn phải được đọc khi phân tích.

SOLVED chỉ dùng làm số liệu game đã xác nhận sau khi bên tích hợp replay bằng
engine thật. Runner không xác nhận replay hoặc lấy `expected_solvable` quyết
định status. Binding thật đã có tại `src.solvers.solve:run_bfs/run_dfs/run_ucs/run_astar`.
Phiên mới và kết quả replay nằm trong [mục kết quả](results/README.md).

## Kiểm thử

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_benchmark.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

Test dùng thư mục tạm: process riêng/tuần tự, ba lượt, CLI Windows, public
BFS/DFS trên đồ thị fixture, metadata/hash/snapshot, JSON–CSV/status/null,
trung vị SOLVED, thiếu binding, lỗi callable/import/process, ngắt phiên và
không ghi đè. Fixture không mô phỏng luật Bloxorz và không xuất thành dữ liệu
hiệu năng bàn giao. Không thêm dependency hoặc triển khai engine/UCS/A* trong runner.

### Tiền xử lý Reverse BFS

A* dựng đồ thị đảo một lần cho mỗi lượt giải map tĩnh nhỏ, sau khi bắt đầu runtime.
`search_time_s` và `peak_memory_bytes` bao gồm tiền xử lý; `expanded_nodes` chỉ đếm
nút mở rộng của A*, không cộng các tư thế duyệt khi dựng heuristic. Kiểm tra hủy/
timeout trong các vòng dựng đồ thị và BFS ngược; dừng trước tìm kiếm vẫn giữ số đo.
Không dùng cache từ lượt trước trong solver/benchmark. Cache của helper tra cứu
heuristic độc lập không được dùng cho các lượt tìm kiếm có đo. Map động và map tĩnh
lớn không dựng Reverse BFS. Start đã thắng giữ fast path không tiền xử lý.

## Phiên đồng bộ heuristic 27/10/2026

- [Kết quả, môi trường và xác minh replay](results/2026-10-27-486a584-heuristic-update/README.md).
- Chạy đủ bốn thuật toán bằng các binding thật; không dùng kết quả cũ thay cho
  lượt mới. Mỗi cặp 3 lượt, timeout 60 giây, cùng manifest 18 map.
- A* hiện có 6 map Reverse BFS, 8 Manhattan, 4 goal indicator. Manhattan khi nằm
  phủ goal dùng h=1. Tên heuristic giữ tương thích nhưng công thức đã đổi;
  commit/hash nguồn là căn cứ nhận diện phiên bản.
- Sau khi runner hoàn tất, dùng `python -m benchmarks.analyze --report PATH/report.json --charts OUTPUT_DIR`
  để kiểm tra từng lời giải bằng engine, tạo bảng/biểu đồ và đoạn bảng LaTeX.
  Bước phân tích không sửa các số đo gốc; kiểm tra source/map hash trước khi replay.
