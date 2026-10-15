# tests

**Lưu gì / làm gì:** Kiểm thử luật game, solver và tích hợp GUI.

**Phụ trách:** Thành viên 1, 3, 4 và 5 theo thư mục con.

## Chạy kiểm thử

Từ thư mục gốc project, dùng Python có cài `pygame`:

```console
python -m unittest discover -s tests -v
```

Chỉ chạy phần tích hợp GUI solver:

```console
python -m unittest discover -s tests/integration -t . -v
```

Các test controller dùng SDL dummy, không mở cửa sổ thật và không cần thiết bị
âm thanh. Test backend/result/worker không cần khởi tạo Pygame. Các file
`__init__.py` giúp unittest phát hiện test trong thư mục con.
