# tests/solvers

**Lưu gì / làm gì:** Kiểm thử lời giải hợp lệ, chống lặp, chi phí, heuristic và trạng thái kết thúc.

**Phụ trách:** Thành viên 4 phụ trách BFS/DFS; thành viên 5 phụ trách UCS/A*.

Kiểm dữ liệu chuyển đổi map (thư viện chuẩn, chạy ngoại tuyến từ repo root):

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_map_conversion.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

Test chuyển đổi kiểm schema v1, tọa độ/liên kết cầu/công tắc/split, đối chiếu dữ liệu nguồn, hash/notice/catalog, từ chối nguồn sai và không ghi đè file. Giữ nguyên bộ test bốn map basic. Test dữ liệu không chạy engine, GUI, replay hoặc xác nhận khả giải.
