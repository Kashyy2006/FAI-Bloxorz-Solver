# docs/report/member_5

**Lưu gì / làm gì:** UCS, A*, chi phí, heuristic, phân tích kết quả; phân công/tỷ lệ hoàn thành, tài liệu tham khảo và phụ lục dùng AI.

**Phụ trách:** Thành viên 5.

## Cập nhật heuristic và số liệu ngày 27/10/2026

- Cost giữ nguyên `1 + 2*F + T`; nguồn chuẩn là `calculate_step_cost`, engine chỉ chuyển tiếp.
- A* chọn goal indicator khi có split/teleport hoặc bắt đầu SPLIT; map có cầu/công
  tắc nhưng không split dùng Manhattan. Map tĩnh nhỏ dùng Reverse BFS; map tĩnh lớn
  hơn 1000 tư thế dùng Manhattan.
- Manhattan: `ceil(min Manhattan distance / 2)`; khối lớn nằm phủ goal có h=1,
  không còn 4. Nhận xét h=4 không nhất quán trong bản báo cáo trước không còn mô tả code hiện tại.
- Trong 18 map: 6 Reverse BFS, 8 Manhattan, 4 goal indicator. Đây là chiến lược chính;
  Manhattan còn có thể được dùng làm fallback khi Reverse BFS không có khoảng cách.
- UCS không dùng heuristic. Reverse BFS được tính vào time/peak của A*, không cộng
  vào expanded; đồ thị heuristic được dựng lại mỗi lượt đo.

### Dữ liệu dùng để cập nhật báo cáo

Xem [phiên benchmark mới](../../../benchmarks/results/2026-10-27-486a584-heuristic-update/README.md).
Dùng `report_tables.tex` để thay bảng tổng hợp cũ, `per_map_medians.csv` cho số liệu
từng map, `aggregate.csv` cho trung bình các trung vị. Kiểm tra `verification.json`
trước khi dẫn số lời giải đã replay. Bảng tổng hợp chỉ dùng tập map SOLVED chung.

[Biểu đồ PNG/SVG](../../../benchmarks/charts/2026-10-27-486a584-heuristic-update/)
được xuất từ cùng dữ liệu; tên file tương ứng từng chỉ số. Khi thay bảng/biểu đồ,
phải cập nhật cả môi trường máy, commit/dirty flag và phần nhận xét, không chỉ thay
con số. Không trộn số liệu từ máy của phiên báo cáo cũ với phiên đo hiện tại.

PDF/nguồn LaTeX ngoài repo chưa được sửa tự động. Cần bỏ phân bố cũ ``6 Reverse
BFS + 12 goal indicator`` và công thức hiệu chỉnh 4 khi ghép báo cáo mới.
Executable cũ chưa được build lại trong lượt đồng bộ này.
