# Bloxorz Solver - FAI

Project Python với GUI Pygame và 4 solver BFS, DFS, UCS, A*. Các thư mục làm việc nằm trực tiếp tại gốc project. Chưa cài môi trường hay thư viện.

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
