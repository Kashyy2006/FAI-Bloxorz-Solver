# benchmarks/results

**Lưu gì / làm gì:** JSON/CSV kết quả từng lượt và bảng số liệu thời gian, bộ nhớ đỉnh, số nút mở rộng, độ dài lời giải.

**Phụ trách:** Thành viên 4 thu thập; thành viên 5 tạo bảng so sánh.

Mỗi phiên của [runner](../README.md) dùng một thư mục mới chứa `report.json`,
`runs.csv`, `readiness.csv`, `summary.csv`. Giữ các file cùng nhau để đối chiếu
môi trường/commit/hash map/snapshot và toàn bộ SolverResult. Lỗi hoặc binding
thiếu ở bảng tình trạng; không có lượt SOLVED thì trung vị là N/A.

Chưa có số liệu benchmark game thật được lưu. Kết quả fixture chỉ nằm trong
thư mục tạm của test. Kết quả SOLVED cần replay bằng engine trước khi dùng
làm bảng so sánh game đã xác nhận.
