# Mô hình bài toán Bloxorz — Thành viên 1

## Trạng thái

Trạng thái là `State(mode, cells, active, bridges)`. Khối nguyên có ba tư thế: đứng (`UPRIGHT`, chiếm một ô), nằm ngang (`HORIZONTAL`, chiếm hai ô kề nhau cùng hàng) hoặc nằm dọc (`VERTICAL`, chiếm hai ô kề nhau cùng cột). Tọa độ là cặp `(row, col)` bắt đầu từ 0; `cells` luôn sắp theo hàng rồi cột. Khi tách, mode là SPLIT, active xác định khối đang điều khiển. bridges chứa trạng thái các nhóm cầu theo thứ tự ID từ điển; cả hai trường đều tham gia khóa chống lặp.

Map là dữ liệu cố định, không nằm trong trạng thái. Khóa chống lặp là `(mode, cells, active, bridges)`. Trạng thái rơi không được đưa vào không gian tìm kiếm.

## Hành động

Khối nguyên có bốn hành động: `UP`, `DOWN`, `LEFT`, `RIGHT`. Mỗi hành động tạo tư thế và vị trí mới theo bảng trong [đặc tả engine](../../contracts/engine.md). Engine kiểm tra tất cả ô mà khối chiếm sau khi lăn trước khi chấp nhận trạng thái kế tiếp.

## Chuyển trạng thái và luật ô

Ra ngoài bảng hoặc vào `void` làm khối rơi và lượt chơi thua. `floor` đỡ khối ở mọi tư thế. `goal` đỡ khối nhưng chỉ thắng khi khối đứng thẳng trên đúng ô đích. `fragile` đỡ khối nằm nhưng làm khối đứng thẳng rơi. Engine trả một trong các kết quả `OK`, `WON`, `LOST`, `INVALID`; chỉ `OK` và `WON` có trạng thái kế tiếp cho solver.

GUI và các solver gọi cùng hàm chuyển trạng thái để dùng chung luật. Engine không phụ thuộc giao diện và không sửa map hoặc trạng thái đầu vào.

## Điều kiện đích

Trạng thái thắng khi `mode == UPRIGHT` và ô duy nhất trong `cells` trùng tọa độ `goal` của map. Khối nằm qua ô goal chưa thắng.

## Chi phí

Chi phí chuẩn là `1 + 2*F + T`, do `calculate_step_cost` trong `src/solvers/costs/calc.py` cung cấp; `step_cost` của engine chỉ chuyển tiếp. `F` đếm fragile mới chiếm ở trạng thái cuối; `T` đếm soft mới chiếm và heavy mới chiếm khi trạng thái cuối đứng thẳng. Đây là quy ước chi phí, khác với sự kiện kích hoạt trước teleport/nhập. SWITCH có giá 1. BFS tối ưu số hành động; UCS/A* tối ưu tổng cost.

## Heuristic phối hợp với TV5

A* dùng goal indicator cho map có split/teleport hoặc snapshot bắt đầu SPLIT;
cầu/công tắc không split dùng Manhattan. Map tĩnh nhỏ dùng Reverse BFS có
fallback Manhattan. Manhattan hiện dùng h=1 khi khối nằm phủ goal, thay cho 4.
Bộ benchmark 18 map gồm 6 Reverse BFS, 8 Manhattan và 4 goal indicator.
Xem [đặc tả chi phí/heuristic](../../../src/solvers/costs/README.md) và
[phiên số liệu mới](../../../benchmarks/results/2026-10-27-486a584-heuristic-update/README.md).


## Cơ chế nâng cao và mô hình trạng thái

Cầu đỡ khối khi mở, tương đương void khi đóng. Soft được nhấn bởi bất kỳ phần
khối nào; heavy và split chỉ nhận nguyên khối đứng. Kích hoạt được xác định từ
trạng thái trước bước và vị trí ngay sau chuyển động. Các tác động toggle/permanent
được áp dụng theo ID công tắc; engine kiểm tra lại ô đỡ sau thay đổi cầu.

Split chuyển khối đứng tới hai vị trí floor định trước. Một lượt chỉ di chuyển
khối active; SWITCH đổi lựa chọn và có chi phí 1. Hai khối cạnh nhau theo cạnh
nhập thành khối ngang/dọc. Cờ cầu và active phải có trong khóa trạng thái vì chúng
ảnh hưởng đến các hành động và trạng thái kế tiếp. Không cần lưu cờ công tắc đã
nhấn vì có thể suy ra từ vị trí, mode và map; không cần lưu ô fragile đã vỡ vì
bước đứng trên đó kết thúc lượt chơi ngay.

## Kiểm chứng tích hợp

Các kiểm thử trong tests/engine bao gồm từng cơ chế và trường hợp nhiều công
tắc tác động cùng cầu, cầu đóng dưới khối nhỏ, thay đổi active khi sắp xếp,
teleport/nhập khối và round-trip snapshot. tests/integration/test_advanced_shared_engine.py
kiểm tra GUI, cả bốn solver, replay, tổng chi phí, timeout/hủy và trạng thái vô nghiệm.
Các số đo hiệu năng cần được thu riêng trong benchmark; unit test không thay benchmark.
