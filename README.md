# Bloxorz — Hướng dẫn chạy và chơi game

Game giải đố Bloxorz với giao diện Pygame, chơi thủ công và giải tự động bằng BFS, DFS, UCS, A*.

## 1. Chạy bản đóng gói trên Windows

Không cần cài Python hoặc Pygame.

1. Giải nén gói game nếu nhận được file ZIP.
2. Mở thư mục `dist`, nhấp đúp `Bloxorz.exe`.
3. Chờ cửa sổ game xuất hiện, chọn chơi mới và chọn map.

Hoặc chạy từ PowerShell tại thư mục gốc project:

```powershell
.\dist\Bloxorz.exe
```

Bản đóng gói theo `Bloxorz.spec` là một file thực thi, có kèm dữ liệu map và nhạc trong `data/`. Lần mở đầu có thể cần thêm thời gian giải nén dữ liệu tạm. Bản `.exe` sử dụng mã nguồn và dữ liệu tại thời điểm build; sau khi sửa code hoặc map, cần đóng gói lại để cập nhật.

## 2. Chạy từ mã nguồn

Cần Python 3.10 trở lên. Phiên benchmark gần nhất sử dụng Python 3.12.6.

Giải nén bài nộp, mở PowerShell tại thư mục source có `README.md`, `requirements.txt`, `src/` và `data/` (thư mục `Source/` nếu bài nộp được tổ chức theo mẫu), sau đó chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.gui.manual.game
```

Hai lệnh đầu chỉ cần thực hiện khi chuẩn bị môi trường lần đầu. Những lần sau, mở game bằng:

```powershell
.\.venv\Scripts\python.exe -m src.gui.manual.game
```

Không cần kích hoạt môi trường ảo khi gọi Python bằng đường dẫn trên. Nếu máy dùng lệnh `py` thay cho `python`, dùng `py -3 -m venv .venv` ở bước tạo môi trường.

Giữ nguyên cấu trúc `src/` và `data/`. Game đọc map JSON trong `data/maps/` và nhạc trong `data/bgm/`.

`requirements.txt` chỉ chứa Pygame, thư viện ngoài cần để chạy game và cả bốn solver. Các thư viện còn lại phục vụ chạy game thuộc thư viện chuẩn Python; PyInstaller chỉ cần khi tự đóng gói lại EXE.

## 3. Mục tiêu và luật chơi

Lăn khối đến ô đích và **đứng thẳng trên đích** để thắng. Khối rơi nếu một phần nằm ngoài mặt sàn hoặc trên cầu đang tắt.

| Loại ô / cơ chế | Cách chơi |
| --- | --- |
| Ô thường | Đỡ khối đứng hoặc nằm |
| Đích | Khối lớn phải đứng thẳng tại đây để thắng |
| Fragile — ô dễ vỡ | Khối lớn đứng thẳng sẽ làm vỡ ô và thua; khối nằm hoặc khối nhỏ có thể đi qua |
| Công tắc nhẹ — soft | Kích hoạt khi khối đè lên |
| Công tắc nặng — heavy | Kích hoạt khi khối lớn đứng thẳng lên |
| Cầu — bridge | Chỉ đi qua được khi cầu mở; công tắc điều khiển trạng thái cầu |
| Toggle / permanent | Tùy map, công tắc đổi trạng thái cầu hoặc đặt cầu mở/đóng theo cấu hình |
| Split | Tách khối lớn thành hai khối nhỏ và chuyển tới các vị trí quy định trong map |
| Nhập khối | Đưa hai khối nhỏ về vị trí liền kề phù hợp để nhập lại |

Di chuột lên ô để xem **tên loại ô và tọa độ**. Các ô đặc biệt có nhãn mờ để dễ nhận diện.

## 4. Điều khiển và chọn màn

| Phím / thao tác | Chức năng |
| --- | --- |
| Mũi tên hoặc `W A S D` | Di chuyển khối theo hướng nhìn hiện tại |
| `Tab` | Đổi khối đang điều khiển khi đã tách |
| `R` / nút Restart | Chơi lại map hiện tại |
| `L` | Mở danh sách chọn map |
| `Q` / `E` | Xoay góc nhìn |
| Cuộn chuột trong màn chơi | Thu phóng |
| Giữ nút chuột giữa và kéo | Điều chỉnh góc nhìn |
| `Esc` | Về menu; nhấn tại menu để thoát |

Ở màn chọn map:

- Nhấp chuột vào map để bắt đầu chơi, hoặc dùng `↑` / `↓` rồi nhấn `Enter`.
- Dùng nút trang trước/trang sau, `←` / `→` hoặc `Page Up` / `Page Down` để chuyển trang.
- `F2` xem chi tiết các map nạp lỗi; `F5` tải lại danh sách sau khi chỉnh JSON khi chạy từ source.

Trong Settings có thể chỉnh âm lượng, độ sáng và chế độ toàn màn hình. Sau khi xoay camera, xem chỉ dẫn hướng điều khiển trên màn hình để xác định hướng di chuyển.

## 5. Giải tự động và phát lại

Solver giải từ **trạng thái hiện tại**, bao gồm vị trí khối, cấu hình cầu và trạng thái tách khối.

1. Mở bảng Solver bằng nút `<<` ở cạnh phải màn hình.
2. Chọn thuật toán bằng nút trên bảng hoặc phím `1`–`4`.
3. Chờ kết quả. Khi có lời giải, nhấn `Space` / Play để khối tự di chuyển tới đích.

| Phím | Chức năng |
| --- | --- |
| `1` | Chạy BFS |
| `2` | Chạy DFS |
| `3` | Chạy UCS |
| `4` | Chạy A* |
| `C` | Hủy lượt tìm kiếm |
| `Space` | Phát / tạm dừng lời giải |
| `N` | Đi từng bước lời giải |
| `X` | Dừng phát lại và trở về trạng thái bắt đầu của lượt giải |
| `F` | Đổi tốc độ phát lại: 0,5x / 1x / 2x / 4x |
| `F1` | Xem chi tiết lỗi solver |

Bảng Solver hiển thị trạng thái và các chỉ số tìm kiếm. `UNSOLVABLE` nghĩa là đã tìm hết mà không có lời giải; `TIMEOUT` nghĩa là hết thời gian, chưa kết luận map vô nghiệm. Di chuyển thủ công hợp lệ, restart hoặc đổi map sẽ xóa lời giải đang nạp.

BFS ưu tiên ít hành động; UCS và A* ưu tiên tổng chi phí; DFS tìm một lời giải theo thứ tự duyệt và có thể trả đường dài.

## 6. Tự đóng gói lại thành EXE

Thực hiện trên Windows, tại thư mục gốc project. Đóng game trước khi build:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm Bloxorz.spec
```

Kết quả: `dist/Bloxorz.exe`. Lệnh build thay thế bản EXE cũ cùng tên. Spec đã cấu hình entry point `launcher.py`, kèm thư mục `data/` và ẩn cửa sổ console. Hãy mở bản EXE mới để kiểm tra chọn map, chơi thủ công và chạy solver trước khi gửi cho người khác.

## 7. Xử lý sự cố

- **Không tìm thấy Python:** cài Python có bật PATH, hoặc dùng `py -3` để tạo môi trường ảo.
- **`No module named pygame`:** cài Pygame bằng đúng Python dùng chạy game: `.\.venv\Scripts\python.exe -m pip install pygame`.
- **Không có map / map không hợp lệ:** kiểm tra `data/maps/`, mở phần lỗi map bằng `F2` tại màn chọn map. Khi chạy source, sửa JSON rồi nhấn `F5` để tải lại.
- **Solver báo ERROR:** nhấn `F1` để đọc thông báo đầy đủ và ghi lại tên map, thuật toán, trạng thái trước khi chạy.
- **EXE không phản ánh code/map mới:** build lại theo mục 6. Có thể chạy từ source để xem traceback trong terminal.

## Tài liệu cho phát triển và báo cáo

- [Đặc tả engine, map và solver](docs/contracts/README.md).
- [Hướng dẫn benchmark](benchmarks/README.md).
- [Kết quả benchmark đồng bộ heuristic 27/10/2026](benchmarks/results/2026-10-27-486a584-heuristic-update/README.md).
- [Quy tắc chi phí và heuristic](src/solvers/costs/README.md).

Chạy toàn bộ kiểm thử từ gốc project:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```
