# tests/solvers

**Lưu gì / làm gì:** Kiểm thử lời giải hợp lệ, chống lặp, chi phí, heuristic và trạng thái kết thúc.

**Phụ trách:** Thành viên 4 phụ trách BFS/DFS; thành viên 5 phụ trách UCS/A*.

Kiểm dữ liệu chuyển đổi map (thư viện chuẩn, chạy ngoại tuyến từ repo root):

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_map_conversion.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_map_bundle.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

Test chuyển đổi kiểm schema v1, tọa độ/liên kết cầu/công tắc/split, đối chiếu dữ liệu nguồn, hash/notice/catalog, từ chối nguồn sai và không ghi đè file. Giữ nguyên bộ test bốn map basic. Test dữ liệu không chạy engine, GUI, replay hoặc xác nhận khả giải.

Test bundle dùng [manifest](../../data/map_bundle.json) để kiểm đúng 18 map và đủ nhóm, bốn basic ở root cùng 14 prepared, metadata/nguồn/notice/hash/hồ sơ từng ID, không tính draft. Chống trùng hình học/start/goal qua padding, tịnh tiến và tám phép quay/đối xứng; có ca kiểm phép chuẩn hóa và dữ liệu schema sai. Dùng chung assertion cấu trúc với test chuyển đổi; không thay validator ngữ nghĩa của engine.
