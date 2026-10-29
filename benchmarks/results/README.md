# benchmarks/results

**Lưu gì / làm gì:** JSON/CSV kết quả từng lượt và bảng số liệu thời gian, bộ nhớ đỉnh, số nút mở rộng, độ dài lời giải.

**Phụ trách:** Thành viên 4 thu thập; thành viên 5 tạo bảng so sánh.

Mỗi phiên của [runner](../README.md) dùng một thư mục mới chứa `report.json`,
`runs.csv`, `readiness.csv`, `summary.csv`. Giữ các file cùng nhau để đối chiếu
môi trường/commit/hash map/snapshot và toàn bộ SolverResult. Lỗi hoặc binding
thiếu ở bảng tình trạng; không có lượt SOLVED thì trung vị là N/A.

## Phiên hiện tại

[2026-10-27 — đồng bộ heuristic, nguồn 486a584](2026-10-27-486a584-heuristic-update/README.md)
chứa dữ liệu runner, xác minh replay, bảng theo map, bảng tổng hợp và đoạn LaTeX.
Đọc `verification.json` để biết chính xác số lượt được kiểm chứng; không suy từ
`complete=true` rằng mọi cặp đều SOLVED.

Các phiên trước (nếu có) giữ nguyên, không ghi đè. Số liệu trong PDF cũ không được
coi là kết quả của phiên này chỉ vì cùng tên map/heuristic. Môi trường máy, commit,
source hash và quy tắc heuristic của từng phiên phải được ghi rõ.
