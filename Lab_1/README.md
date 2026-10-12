# Lab 1 - Bloxorz Solver

Project Python: game Bloxorz với GUI Pygame và 4 thuật toán BFS, DFS, UCS, A*. Hiện chỉ chuẩn bị thư mục làm việc; chưa viết code, cài thư viện hay tạo môi trường.

## Cấu trúc thư mục

```text
Lab_1/
├── src/
│   ├── engine/         # Trạng thái, đọc map, luật game và hàm dùng chung
│   ├── gui/            # Chơi thủ công, điều khiển solver và phát lại
│   └── solvers/        # BFS, DFS, UCS, A* và giao diện kết quả chung
├── data/
│   ├── maps/           # Map JSON theo schema thống nhất
│   └── references/     # Nguồn map và tài liệu tham khảo
├── tests/              # Kiểm thử luật game, solver và tích hợp
├── benchmarks/
│   ├── results/        # Kết quả JSON, bảng số liệu
│   └── charts/         # Biểu đồ so sánh 4 solver
├── docs/
│   ├── report/         # Các phần báo cáo và PDF tổng hợp
│   └── video/          # Kịch bản, phụ đề, demo và link YouTube
└── submission/         # Bản đóng gói bài nộp
```

Các thư mục chứa `.gitkeep` để Git lưu được thư mục trống. Khi bắt đầu lập trình, nhóm bổ sung điểm chạy chương trình, danh sách thư viện và hướng dẫn cài đặt/chạy.

## Phân công

Chưa có tên thành viên; dùng STT từ 1 đến 5.

| Thành viên | Công việc code và dữ liệu | Báo cáo và video |
| --- | --- | --- |
| **1 - Game engine** | Thiết kế trạng thái, đọc map JSON; xử lý di chuyển, thắng/thua, ô dễ vỡ, cầu, công tắc, tách/nhập khối; cung cấp hàm chung cho GUI/solver; kiểm thử luật game. | Viết mô hình bài toán: trạng thái, hành động, chuyển trạng thái, điều kiện thắng và quy ước luật game. |
| **2 - GUI chơi thủ công** | Làm GUI Pygame; vẽ map, khối và các loại ô; điều khiển bàn phím; chọn màn, New Game, Restart, thông báo thắng/thua. | Viết giao diện và hướng dẫn chơi; quay demo thủ công thể hiện di chuyển, thắng/thua và cơ chế đặc biệt. |
| **3 - GUI solver và video** | Nút chạy 4 solver từ trạng thái hiện tại; chạy nền, đọc JSON kết quả, hiển thị thống kê; phát lại, tạm dừng, hủy lời giải; kiểm thử tích hợp. | Viết hướng dẫn cài đặt/chạy và luồng giải tự động; quay demo solver, dựng toàn bộ video, thêm phụ đề/lời dẫn, đăng YouTube công khai và bàn giao link. |
| **4 - BFS, DFS, map và benchmark** | Viết BFS/DFS, chống lặp, dựng lời giải, timeout và xuất JSON chung; tìm map JSON có sẵn hoặc chuyển map tham khảo sang schema chung, ghi nguồn; chuẩn bị bộ map cố định theo độ khó, đủ cơ chế và màn không giải được; làm bộ đo và benchmark 4 solver. | Viết BFS, DFS, mô tả bộ map và phương pháp thí nghiệm; bàn giao bảng số liệu, nguồn map. |
| **5 - UCS, A* và báo cáo tổng hợp** | Viết UCS/A*, hàm chi phí chung; thiết kế và kiểm chứng heuristic; xuất JSON chung; tạo bảng, biểu đồ so sánh. | Viết UCS, A*, chi phí, heuristic và phân tích kết quả; tổng hợp PDF, bảng phân công/tỷ lệ hoàn thành, tài liệu tham khảo, phụ lục dùng AI và link video; đóng gói bài nộp. |

## Thống nhất trước khi code

- Engine và cả 4 solver dùng chung trạng thái, luật game, schema map JSON và schema kết quả. Trạng thái cần lưu hướng khối, trạng thái cầu và thông tin hai khối khi tách.
- Kết quả solver gồm trạng thái kết thúc, chuỗi hành động, thời gian tìm kiếm, bộ nhớ đỉnh, số nút mở rộng và độ dài lời giải; phân biệt không có lời giải, timeout và hủy.
- UCS/A* dùng chung hàm chi phí; giải thích chi phí và kiểm chứng tính admissible/consistent của heuristic theo chi phí đó.
- Benchmark dùng cùng bộ map, trạng thái đầu, cách đo và timeout cho cả 4 solver.
- Bài nộp gồm source, hướng dẫn chạy, danh sách thư viện và báo cáo PDF có link video công khai; đặt tên file nén theo MSSV các thành viên.
