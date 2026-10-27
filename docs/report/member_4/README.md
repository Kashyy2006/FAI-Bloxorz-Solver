# BFS, DFS, bộ map và phương pháp thí nghiệm

**Phụ trách:** Thành viên 4. **Bản thảo và bàn giao:** 17/10/2026.

**Cập nhật 27/10/2026:** phần bàn giao bên dưới là hồ sơ lịch sử ngày 17/10,
không phải trạng thái tích hợp/số liệu mới nhất. Hiện có binding solver thật;
A* đã đổi quy tắc chọn heuristic và hiệu chỉnh Manhattan.
Xem [phiên benchmark đồng bộ](../../../benchmarks/results/2026-10-27-486a584-heuristic-update/README.md)
để lấy số liệu hiện tại, không dùng thống kê fixture bên dưới làm số liệu game.


Đã có bộ 18 map kèm nguồn/hash/hồ sơ, callable BFS/DFS, runtime/kết quả dùng
chung và runner độc lập. Kiểm tra thành phần đạt **153/153 test, không skip**.
Chưa có số đo hiệu năng game thật hoặc xác nhận engine/replay trên bộ map;
trạng thái bàn giao thành phần không thay cho nghiệm thu hệ thống.

## Nội dung và phiên bản bàn giao

Bàn giao trực tiếp bằng repo cùng manifest, không cần tạo ZIP riêng. Giữ cả
dữ liệu nguồn, notice và ghi chú chuyển đổi khi đóng gói bài nộp.

| Sản phẩm | Điểm vào và tài liệu |
| --- | --- |
| 18 JSON, inventory, SHA256, nguồn và trạng thái từng map | [Manifest](../../../data/map_bundle.json), [catalog](../../../data/maps/README.md) |
| Nguồn ngoại tuyến, notice và cách chuyển đổi | [Nguồn map](../../../data/references/README.md), [file nguồn](../../../data/references/map_sources/README.md), [converter](../../../data/references/convert_maps.py) |
| Mục đích, witness/phân tích và mức tin cậy từng map | [Hồ sơ kiểm tra](../../../data/references/map-bundle-evidence.md) |
| BFS | [Mã](../../../src/solvers/bfs/solver.py), [chữ ký, ví dụ fixture và JSON](../../../src/solvers/bfs/README.md) |
| DFS | [Mã](../../../src/solvers/dfs/solver.py), [chữ ký, ví dụ fixture và JSON](../../../src/solvers/dfs/README.md) |
| Runtime, dựng đường và SolverResult | [Common](../../../src/solvers/common/README.md), [hợp đồng solver](../../contracts/solver.md) |
| Runner, binding và định dạng JSON/CSV | [Hướng dẫn chạy](../../../benchmarks/README.md), [mã runner](../../../benchmarks/run.py), [thư mục kết quả](../../../benchmarks/results/README.md) |
| Kiểm thử độc lập | [Hướng dẫn](../../../tests/solvers/README.md), lệnh và số lượng ở dưới |

Mã nguồn được kiểm tra tại branch `feature/TV4-search-and-evaluation`, HEAD
`fed00b91546de8c9202dd416a39321455d581398`; working tree sạch trước khi bổ sung
tài liệu bàn giao. Các commit dưới đây đã nằm trong HEAD đó:

| Phần | Commit |
| --- | --- |
| Khóa bộ 18 map và manifest | `3ca03d903ec0bda15e5b69712aacaaec54f3a0e4` |
| Callable BFS và metadata cầu | `e45c2c389ef8fad6b19da7be137c0835a10f8d9b` |
| Callable DFS và kiểm thử hợp đồng | `bb7ca2463fe27307e4deb68738a08bdaabf650cc` |
| Runner cách ly tiến trình, JSON/CSV | `fed00b91546de8c9202dd416a39321455d581398` |

SHA256 byte của `data/map_bundle.json`:
`650e1c17b5c1c47f211d67d1f95dfc38589d0cd49fe59675f162e29c6f4daa50`.
Hash của từng map nằm trong manifest. Tài liệu bàn giao bổ sung sau HEAD trên;
khi thu số đo phải lưu commit/dirty flag của đúng phiên chạy, không dùng
commit nền này thay cho phiên bản đã thay đổi.

## Thuật toán và hợp đồng callable

Mỗi nút tìm kiếm là trạng thái đầy đủ `(mode, cells, active, bridges)`.
Khóa phải giữ cả khối đang điều khiển và cấu hình cầu: hai trạng thái cùng vị
trí nhưng khác các trường này có thể có tập bước đi khác nhau. Caller cung
cấp map/state hợp lệ và callback của engine; solver không đọc JSON, cài luật
chuyển động hoặc thay snapshot hiện tại bằng initial state.

**BFS:** dùng `deque` FIFO, đánh dấu visited đồng thời lưu parent/action khi
enqueue. Kiểm goal khi dequeue, trước mở rộng; giữ đường phát hiện đầu tiên
khi key xuất hiện lại. Vì mỗi cạnh là một action, BFS tìm đường ít action
nhất, kể cả SWITCH. Chi phí chỉ là tổng cost của đường đã chọn, không bảo
đảm nhỏ nhất khi cost giữa các cạnh khác nhau.

**DFS:** dùng stack `list`, lấy bằng `pop()`, push theo thứ tự đảo của danh
sách successors để ưu tiên action đầu của engine. Đánh dấu và lưu parent
khi push, mỗi full key chỉ khám phá một lần. Đây là DFS đồ thị iterative,
không đệ quy, không giới hạn độ sâu; cây parent có thể khác DFS đệ quy khi có
cạnh chéo. DFS không bảo đảm ít bước hoặc rẻ nhất.

Cả hai dựng actions bằng parent sau khi tìm thấy goal, không lưu cả đường
đi cho từng nút. Với đồ thị hữu hạn và khóa đầy đủ, không bị dừng sớm bởi
timeout/hủy/lỗi, cả hai tìm được goal đạt tới được hoặc duyệt đến cạn
frontier. Thời gian trung bình O(V+E), cấu trúc tìm kiếm O(V), với V/E tính
theo các key/cạnh đạt tới được và giả định thao tác khóa/callback có chi phí
hằng. DFS hiện có visited/parent nên bộ nhớ không chỉ O(độ sâu).

```python
from src.solvers.bfs.solver import solve_bfs
from src.solvers.dfs.solver import solve_dfs

# Cả hai có cùng bộ đối số; caller cung cấp các biến/callback bên dưới.
result = solve_bfs(
    game_map, current_state,
    map_id=map_id, bridge_ids=bridge_ids,
    state_key=state_key, is_goal=is_goal, successors=successors,
    validate_start_state=validate_start_state,
    timeout_s=60.0, cancel_event=cancel_event,
)
payload = result.to_dict()
```

Đây là mẫu nối API, không phải chương trình độc lập. Ví dụ chạy được và JSON
đủ 11 trường nằm trong hai README solver ở bảng bàn giao. Các ví dụ đó được
gắn nhãn **đồ thị fixture**; số đo từ lượt chạy fixture không phải hiệu năng
Bloxorz. Không có JSON benchmark map game thật để bàn giao trong phiên này.

Các keyword `map_id`, `bridge_ids` và bốn callback đều bắt buộc. Validator
phải ném lỗi có lý do khi snapshot sai; không dùng no-op khi tích hợp.
`bridge_ids` là tuple ID duy nhất theo thứ tự từ điển, khớp bridge bits và
đúng map; chỉ dùng `()` cho map thật không có cầu. Successors giữ thứ tự
UP, DOWN, LEFT, RIGHT, SWITCH, chỉ trả bước hợp lệ cùng `action/state/cost`.
Không đổi schema JSON hoặc lược bỏ trường khi chuyển cho GUI/runner.

Kết quả gồm SOLVED, UNSOLVABLE, TIMEOUT, CANCELLED, ERROR. Ngoài SOLVED,
actions/solution_length/solution_cost đều null. ERROR giữ lý do và số đo đã
thu; chỉ ERROR được có trường envelope chưa xác thực bằng null. Start hợp
lệ đã thắng trả actions=[] và năm metrics bằng 0 sau validation, kể cả event
đã set. Khi search, hủy ưu tiên trước timeout; timeout là hợp tác và không
ngắt được callback đang chặn. Không chạy các solver đo đồng thời trong một
tiến trình hoặc bật tracemalloc quanh callable từ bên ngoài.

## Bộ map và mức bằng chứng

Inventory thực tế khớp đúng **18 JSON = 4 basic + 14 prepared**; không có file
draft hoặc JSON ngoài inventory. Phân loại nguồn: **14 adapted + 4 original**.
Các map được kiểm chống trùng hình học/start/goal qua padding, tịnh tiến và
tám phép quay/đối xứng; mỗi map tính một nhóm chính.

| Nhóm chính | Số map | Vai trò kiểm tra |
| --- | ---: | --- |
| Basic | 4 | Hai bước, đổi hướng, chu trình và goal cô lập |
| Fragile | 2 | Nằm được đỡ, đứng rơi, cost khi mới chiếm ô |
| Cầu | 1 | Hai nhóm cầu và cùng vị trí khác bridge bits |
| Soft/toggle | 2 | Nhấn/rời/nhấn lại, nhiều cầu độc lập |
| Heavy | 2 | Nằm/khối nhỏ không nhấn, UPRIGHT nhấn |
| Permanent | 2 | Đặt mở và đặt đóng, kích hoạt lại không đảo |
| Split/merge | 2 | Tách, SWITCH, active sau sort và nhập khối |
| Kết hợp | 2 | Tương tác cầu/công tắc với khối tách và giữ đè |
| Vô nghiệm nâng cao | 1 | Phân tích bất biến cầu luôn đóng |
| **Tổng** | **18** | Difficulty còn là dự kiến, chưa suy từ số đo |

Nguồn adapted gồm một map Matías/matuneville, sáu map AchrafMez và bảy map
Frank Buss / Damien Clarke. Giữ [notice Matías](../../../data/references/matuneville-LICENSE.txt),
[notice AchrafMez](../../../data/references/AchrafMez-LICENSE.txt) và
[notice Frank Buss / Damien Clarke](../../../data/references/FrankBuss-license.txt).
Nguồn Frank được chọn trong phạm vi bài học phi thương mại theo notice đã
lưu. URL/commit nguồn, byte ghim và cách đổi tọa độ/ô/cơ chế nằm trong
[ghi chú basic](../../../data/references/basic_turn_01.md),
[ghi chú Achraf](../../../data/references/achraf-map-conversion.md) và
[ghi chú Frank](../../../data/references/frank-map-conversion.md).
Không tiếp nhận mã game/solver bên ngoài vào phần thuật toán.

Mỗi map có mục đích, witness hoặc phân tích và mức tin cậy: 3
`manual_reference`, 13 `manual_local`, 2 `manual_invariant`. Tất cả đang có
`data=passed`, `engine/replay/solver=not_run` trong manifest. Witness cục bộ
chưa chứng minh đi được từ initial state tới snapshot; màn adapted chưa
được suy là khả giải chỉ vì nguồn có phát hành. `expected_solvable` chỉ là
oracle đối chiếu, không được dùng để tạo status. Timeout không chứng minh vô
nghiệm, loader từ chối map cũng không chứng minh vô nghiệm.

## Phương pháp thí nghiệm và cách tái lập

Theo [hợp đồng benchmark](../../contracts/benchmark.md), chạy cùng byte map
và snapshot cho mọi solver; **60 giây search, ba lượt/cặp**, tuần tự và mỗi
lượt là tiến trình mới qua `spawn`. Với 18 map, BFS/DFS cần 108 lượt; cả bốn
solver cần 216 lượt khi có binding hợp lệ.

| Chỉ số | Ranh giới đo |
| --- | --- |
| `search_time_s` | `perf_counter` trước tạo cấu trúc tìm kiếm, dừng trước dựng actions; không gồm loader, validation/snapshot, GUI, replay, serialize |
| `peak_memory_bytes` | `tracemalloc` từ trước tạo cấu trúc, qua dựng actions; lấy peak và cleanup trước xuất JSON; không phải RSS |
| `expanded_nodes` | Số lần gọi successors, gồm lời gọi ném lỗi; không tính goal |
| `solution_length` | Số action, gồm SWITCH |
| `solution_cost` | Tổng Successor.cost của đường đã chọn theo `base1_fragile2_switch1_v1` |

Giữ tracing nhất quán, ghi rõ overhead công cụ đo. `wall_time_s` là thời
gian process riêng, không thay search time. Runner mặc định chờ tối đa 90
giây/lượt; process vượt giới hạn được ghi `process_error` với thời gian chờ
thực tế, không tạo TIMEOUT giả của solver.

Từng lượt hợp lệ giữ toàn bộ SolverResult, run_index 1–3, môi trường máy/CPU/
Python, commit/dirty flag, hash mã Python/inventory/map/snapshot và binding
trong `report.json`; giữ cùng `runs.csv`, `readiness.csv`, `summary.csv`.
Tổng hợp trung vị năm metrics chỉ từ SOLVED, kèm số lượt đủ năm status và
các lượt thiếu/lỗi. Không có SOLVED thì JSON=null, CSV trống (N/A).
SOLVED phải replay bằng engine trước khi dùng làm số liệu game đã xác nhận.

Kiểm tra đầu vào hiện tại, chạy từ repo root với thư mục output mới:

```powershell
python -m benchmarks.run --inventory data/map_bundle.json --output benchmarks/results/readiness-check
```

Đã chạy cú pháp này với output trong thư mục tạm: exit code **1** đúng dự
kiến, `complete=true`, **0 lượt solver, 72 mục missing_binding**, 72 dòng
summary; CSV tương ứng có 0/72/72 dòng dữ liệu. Đây là kiểm tra tình trạng,
không phải phiên đo hiệu năng. Không lưu kết quả fixture vào thư mục bàn giao.

Khi có binding engine, dùng lệnh BFS/DFS và chữ ký
`binding(map_path, snapshot, *, timeout_s)` trong
[README runner](../../../benchmarks/README.md). Module binding minh họa trong
README chưa có trong repo. Không truyền trực tiếp `solve_bfs`/`solve_dfs`
làm binding vì chữ ký khác; chương trình gọi API phải có guard
`if __name__ == "__main__":` để an toàn với Windows spawn.

## Kiểm tra thực tế ngày 17/10/2026

Python **3.12.10**, Windows; lệnh từ gốc repo, không cài dependency mới,
không skip hoặc làm yếu test. Không dùng discovery từ `tests` làm kết quả
tổng vì hiện lệnh đó bỏ sót thư mục engine/solvers.

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
python -m unittest discover -s tests/engine -v
python -m unittest discover -s tests/integration -t . -v
```

| Nhóm trong lệnh test thành phần | Số test đạt |
| --- | ---: |
| BFS: lõi + callable | 16 + 5 = 21 |
| DFS: lõi + callable + runtime | 10 + 5 + 24 = 39 |
| Common + runtime/kết quả dùng chung | 17 + 31 = 48 |
| Map basic + conversion + bundle | 7 + 11 + 8 = 26 |
| Runner benchmark | 19 |
| **Tổng thành phần** | **153/153, không skip** |

Kiểm tra bổ sung: **12/12 test engine cơ bản đạt**. Nhóm integration phát
hiện 26 mục: **23 đạt, 2 thất bại, 1 lỗi import**, không skip. Hai test
`test_direct_file_from_another_working_directory` và
`test_module_from_project_root` trong
[test_game_launch.py](../../../tests/integration/test_game_launch.py) thất bại;
module [test_solver_controller.py](../../../tests/integration/test_solver_controller.py)
không import được. Cả ba đều báo `ModuleNotFoundError: No module named
'pygame'`. Các test dùng placeholder đang đạt không xác nhận bốn solver thật.

Đã đối chiếu riêng tập đường dẫn inventory với toàn bộ JSON trong
`data/maps/`, ID trong file, SHA256 từng file và SHA256 manifest ở trên.
Các ví dụ fixture chạy độc lập của hai README solver được kiểm tra lại
trong lượt bàn giao; không có thay đổi hành vi thuật toán hoặc dữ liệu map.

## Việc bên tích hợp cần thực hiện

| Bên nhận | Đầu vào/việc cần hoàn tất | Bằng chứng cần bổ sung |
| --- | --- | --- |
| Thành viên 1: engine | Nhận đủ map/schema, loader nâng cao, validator ngữ nghĩa cho snapshot và metadata bridge ID đúng map; cung cấp state_key/is_goal/successors với step cost theo contract | Load từng map; replay witness từ initial/snapshot, full key/cầu/active, công tắc giữ đè/nhấn lại, nhập khối; duyệt cạn map vô nghiệm |
| Thành viên 3: dispatcher/GUI solver | Nối callable BFS/DFS thật vào điểm gọi chung, giữ snapshot hiện tại, event hủy, run_id và JSON/status; đối chiếu cách GUI nhận ERROR có envelope null | Chạy/replay map basic rồi nâng cao; snapshot giữa ván/đã thắng, cancel/restart/đổi màn, bỏ kết quả cũ |
| Thành viên 2 và 3: GUI/replay | Chuẩn bị môi trường Pygame, nối GUI với luật/transition của engine và bộ map đã xác nhận | Chạy lại ca launch/controller lỗi ở trên; kiểm lời giải bằng transition thật, không bằng placeholder |
| Thành viên 5: UCS/A*, chi phí và báo cáo chung | Cung cấp callable cùng hợp đồng status/metrics và binding import được; dùng cost model chung và heuristic đã thống nhất | Đối chiếu chi phí với engine, bốn solver trên cùng map/snapshot; nhận raw JSON/CSV để tổng hợp bảng/biểu đồ |
| Thành viên 4: chạy đo và hỗ trợ phần đã bàn giao | Nhận binding hợp lệ, chạy runner theo phương pháp trên; sửa lỗi map/BFS/DFS/common/runner khi có ca tái hiện thuộc phạm vi mình | Giữ raw đủ ba lượt/cặp, replay SOLVED trước nghiệm thu và ghi rõ mọi lượt thiếu/lỗi |

Giới hạn đã biết tại phiên bản này: loader engine từ chối bridge/switch/split;
GUI còn dùng solver tạm; UCS mới có lõi `_search`, thư mục A* chưa có mã
triển khai, chưa có binding benchmark game thật. Helper chi phí của thành
viên 5 còn lấy thuộc tính map không có trong GameMap cơ bản; cần đối chiếu
với step cost engine trước khi đo. Không coi việc đủ dữ liệu và test callback
là xác nhận các phần tích hợp này đã hoàn tất.

Các ca hồi quy cần giữ khi nối hệ thống: cùng cells khác cầu/active; snapshot
giữa ván; input đã thắng nhưng metadata sai; hủy tại deadline; cạn frontier
so với timeout; ERROR envelope null; callback/process không hợp tác;
JSON–CSV giữ nguyên null và snapshot; từ chối ghi đè dữ liệu/kết quả cũ.

## Ghi nhận hỗ trợ AI

Codex hỗ trợ khảo sát/chuyển dữ liệu, soạn mã và test BFS/DFS/common/runner,
đối chiếu hợp đồng và tài liệu như đã ghi trong các README thành phần. Trong
lượt bàn giao này, AI đọc mã/tài liệu, chạy các lệnh kiểm tra nêu trên, đối
chiếu inventory/hash và soạn bản thảo này. Người phụ trách cần rà nội dung
trước khi ghép báo cáo chung.

Tóm tắt yêu cầu dùng trong lượt này, không phải trích nguyên văn prompt:
“Hoàn thiện bàn giao bộ map, BFS/DFS và runner theo yêu cầu đã cung cấp;
kiểm lại test/hash/phiên bản; ghi rõ phần đã xác minh và phần còn chờ tích
hợp, chỉ đưa nội dung kỹ thuật liên quan vào tài liệu.” Không có nhật ký
nguyên văn đầy đủ của các prompt trước trong repo; không dựng lại thành
lịch sử đã lưu. Không dùng AI hoặc fixture để tạo số liệu benchmark game giả.
