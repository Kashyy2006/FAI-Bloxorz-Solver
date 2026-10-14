# Hợp đồng dùng chung Bloxorz

**Phiên bản 1.0 — mốc 14/10.** Bộ tài liệu bàn giao thiết kế của thành viên 1,
dựa trên nội dung nhóm cung cấp. Các quy ước chi tiết là quyết định triển khai
của nhóm. Tài liệu chưa phải code engine hay kết quả kiểm thử.

| Tài liệu | Nội dung | Người đảm nhận |
| --- | --- | --- |
| [engine.md](engine.md) | State, chuyển động, luật ô, API và events | Thành viên 1 |
| [map-format.md](map-format.md) | Schema, kiểm tra và ví dụ map JSON | Thành viên 1 và 4 |
| [solver.md](solver.md) | Chi phí, heuristic cơ sở, API và JSON kết quả | Thành viên 1 phối hợp 3–5 |
| [benchmark.md](benchmark.md) | Cách đo, chạy và tổng hợp thí nghiệm | Thành viên 4 và 5 |

Đọc engine → map-format → solver → benchmark. GUI và cả bốn solver dùng
cùng luật engine. Khi thay đổi hợp đồng, cập nhật phiên bản và thông báo nhóm.

## Quyết định đã thống nhất trong bộ tài liệu

- Khối active sau tách lấy từ `destinations[active_destination]`, không mặc định luôn là 0.
- `difficulty` chỉ là easy/medium/hard; kỳ vọng vô nghiệm dùng `expected_solvable`.
- So sánh ID theo thứ tự từ điển; công tắc kích hoạt theo cạnh chưa nhấn → nhấn.
- Từ chối trường JSON ngoài schema. Ví dụ khai báo nâng cao là đoạn minh họa;
  ví dụ basic_01 là map đầy đủ.
- Chi phí `1 + 2*F + T`; A* ban đầu dùng goal_indicator_v1.

## Phần thành viên 1 cần triển khai tiếp

Engine/validator tại `src/engine/`, kiểm thử tại `tests/engine/`, mô hình bài toán
trong `docs/report/member_1/`. Hoàn thành các file này chỉ hoàn thành phần
chốt thiết kế, không thay thế nhiệm vụ code và kiểm thử engine.
