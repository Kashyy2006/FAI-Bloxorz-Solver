# Engine nâng cao — Thành viên 1

Engine Python dùng chung cho GUI và BFS/DFS/UCS/A*. Không phụ thuộc Pygame.

| File | Trách nhiệm |
| --- | --- |
| models.py | State bất biến, chuẩn hóa cells và giữ đúng khối active sau sắp xếp |
| map_loader.py | Schema v1 đầy đủ; Bridge/Switch/GameMap bất biến, kiểm tra mọi liên kết |
| rules.py | Chuyển động, ô đỡ, công tắc, cầu, teleport, nhập khối và chi phí chuẩn |
| serialization.py | Snapshot JSON và xác thực trạng thái cho GUI/worker/replay |

## API công khai

Import từ `src.engine`: `load_map`, `parse_map`, `initial_state`, `transition`,
`successors`, `state_key`, `is_goal`, `validate_state`, `state_to_dict`, `state_from_dict`, `step_cost`.

GameMap.bridges và GameMap.switches là tuple sắp theo ID từ điển; GameMap.bridge_ids
xác định thứ tự bool trong State.bridges. GUI truyền snapshot với bridges là object ID → bool.
State key chứa mode, cells, active và mọi cờ cầu; không chứa g hay lịch sử đường đi.

## Quy tắc nâng cao

- Soft: bất kỳ phần khối; heavy/split: chỉ nguyên khối đứng.
- Chỉ kích hoạt khi chuyển từ chưa nhấn sang nhấn; SWITCH không kích hoạt.
- toggle đảo từng nhóm cầu; permanent đặt giá trị open mỗi lần nhấn.
- Nhiều công tắc: xử lý theo ID. Kiểm tra ô đỡ trước và sau cập nhật cầu.
- Split dịch chuyển đến hai floor không kề nhau, active theo active_destination.
- Hai khối kề cạnh tự nhập; khối nhỏ không thắng hoặc kích hoạt heavy/split.
- Không kích hoạt dây chuyền sau teleport/nhập trong cùng lượt.
- Events: SWITCH_ACTIVATED, BRIDGE_CHANGED, BLOCK_SPLIT, BLOCK_MERGED.
  LOST vẫn giữ events xảy ra trước khi phát hiện rơi; next_state là None.

## Chi phí thống nhất với TV5

`cost = 1 + 2*F + T`. F đếm fragile mới chiếm ở trạng thái cuối, T đếm
soft/heavy vừa nhấn sau chuyển động, trước teleport/nhập. step_cost và transition
cùng dùng _activated_switches; SWITCH giá 1. calculate_step_cost của TV5 chỉ
chuyển tiếp sang step_cost; UCS/A* cộng Successor.cost một lần.

## Tích hợp và chạy thử

- GUI gọi engine qua adapter trong src/gui/manual/game.py; Tab đổi khối nhỏ.
- src/solvers/solve.py điều phối solver thật. A* dùng heuristic cơ sở 0 tại goal,
  1 ở trạng thái khác (admissible/consistent cả khi có teleport).
- Map mẫu: data/maps/advanced_bridge_01.json và advanced_split_01.json.
- Chạy game: `python -m src.gui.manual.game` từ gốc repo.
- Chạy đủ kiểm thử: `python -m unittest discover -s tests -t . -v`.

Chi tiết luật và schema nằm tại docs/contracts/. Việc thay đổi luật/chi phí cần
được TV1 phối hợp TV3–TV5 cập nhật ở hợp đồng và kiểm thử tích hợp.
