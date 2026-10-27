# Bloxorz Solver - FAI

Project Python với GUI Pygame và 4 solver BFS, DFS, UCS, A*. Các thư mục làm việc nằm trực tiếp tại gốc project. Môi trường chạy cần Python 3.10+ và Pygame.

| Thư mục | Nội dung | Phụ trách |
| --- | --- | --- |
| `src/engine/` | Trạng thái, map, luật game và API chung | Thành viên 1 |
| `src/gui/manual/` | GUI chơi thủ công | Thành viên 2 |
| `src/gui/solver/` | GUI solver, chạy nền và phát lại | Thành viên 3 |
| `src/solvers/bfs/`, `dfs/`, `common/` | BFS, DFS và tiện ích solver chung | Thành viên 4 |
| `src/solvers/ucs/`, `astar/`, `costs/` | UCS, A* và hàm chi phí | Thành viên 5 |
| `data/` | Map JSON và nguồn tham khảo | Thành viên 4; thành viên 5 tổng hợp nguồn |
| `tests/` | Kiểm thử engine, solver và tích hợp | Thành viên 1, 3, 4, 5 |
| `benchmarks/` | Bộ đo, kết quả và biểu đồ | Thành viên 4 đo; thành viên 5 phân tích |
| `docs/contracts/` | Hợp đồng trạng thái, API và JSON | Thành viên 1 chủ trì, thành viên 3-5 phối hợp |
| `docs/report/member_1/` đến `member_5/` | Các phần báo cáo theo thành viên | Mỗi người viết phần mình; thành viên 5 tổng hợp |
| `docs/video/` | Demo thủ công, demo solver, dựng video và link công khai | Thành viên 2 và 3 |
| `submission/` | Đóng gói source và báo cáo để nộp | Thành viên 5 |

Mỗi thư mục có README riêng mô tả nội dung và người đảm nhận. STT 1-5 thay cho tên thành viên chưa được cung cấp.

[Bàn giao BFS/DFS, bộ 18 map và runner](docs/report/member_4/README.md) có
phiên bản mã, hướng dẫn sử dụng, bằng chứng kiểm tra và các việc cần tích hợp.

Mốc 14/10: nhóm chốt cấu trúc trạng thái, hàm chuyển trạng thái, định dạng map JSON, kết quả solver và hàm chi phí dùng chung. Ghi các đặc tả được nhóm thống nhất vào `docs/contracts/`.

## Chạy bản tích hợp engine nâng cao

```powershell
python -m src.gui.manual.game
python -m unittest discover -s tests -t . -v
```

GUI và bốn solver dùng engine chung. Dùng Tab đổi khối nhỏ; phím 1–4 chọn
BFS/DFS/UCS/A*. Map advanced_bridge_01 thử cầu/công tắc/fragile;
advanced_split_01 thử teleport và nhập khối. Cần Python 3.10+ và Pygame.

## Đồng bộ heuristic và số liệu (27/10/2026)

A* dùng Reverse BFS trên 6 map, Manhattan trên 8 map và goal indicator trên 4 map
của bộ benchmark 18 map. Manhattan có hiệu chỉnh 1 khi nằm phủ goal.
Xem [quy tắc heuristic](src/solvers/costs/README.md) và
[phiên benchmark mới](benchmarks/results/2026-10-27-486a584-heuristic-update/README.md).

`dist/Bloxorz.exe` đang là bản đóng gói trước hai thay đổi heuristic `d65e0c4` và
`486a584`; cần build lại từ source hiện tại nếu muốn dùng cùng phiên bản với số liệu
mới. Lượt đồng bộ tài liệu/test/benchmark này không cập nhật executable.
