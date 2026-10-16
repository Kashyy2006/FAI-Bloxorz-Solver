# Mô hình bài toán Bloxorz — Thành viên 1

## Trạng thái

Ở phiên bản cơ bản, trạng thái là `State(mode, cells, active, bridges)`. Khối nguyên có ba tư thế: đứng (`UPRIGHT`, chiếm một ô), nằm ngang (`HORIZONTAL`, chiếm hai ô kề nhau cùng hàng) hoặc nằm dọc (`VERTICAL`, chiếm hai ô kề nhau cùng cột). Tọa độ là cặp `(row, col)` bắt đầu từ 0; `cells` luôn sắp theo hàng rồi cột. Ở mốc này `active` là `None`, còn `bridges` là tuple rỗng.

Map là dữ liệu cố định, không nằm trong trạng thái. Khóa chống lặp là `(mode, cells, active, bridges)`. Trạng thái rơi không được đưa vào không gian tìm kiếm.

## Hành động

Khối nguyên có bốn hành động: `UP`, `DOWN`, `LEFT`, `RIGHT`. Mỗi hành động tạo tư thế và vị trí mới theo bảng trong [đặc tả engine](../../contracts/engine.md). Engine kiểm tra tất cả ô mà khối chiếm sau khi lăn trước khi chấp nhận trạng thái kế tiếp.

## Chuyển trạng thái và luật ô

Ra ngoài bảng hoặc vào `void` làm khối rơi và lượt chơi thua. `floor` đỡ khối ở mọi tư thế. `goal` đỡ khối nhưng chỉ thắng khi khối đứng thẳng trên đúng ô đích. `fragile` đỡ khối nằm nhưng làm khối đứng thẳng rơi. Engine trả một trong các kết quả `OK`, `WON`, `LOST`, `INVALID`; chỉ `OK` và `WON` có trạng thái kế tiếp cho solver.

GUI và các solver gọi cùng hàm chuyển trạng thái để dùng chung luật. Engine không phụ thuộc giao diện và không sửa map hoặc trạng thái đầu vào.

## Điều kiện đích

Trạng thái thắng khi `mode == UPRIGHT` và ô duy nhất trong `cells` trùng tọa độ `goal` của map. Khối nằm qua ô goal chưa thắng.

## Chi phí

Chi phí theo hợp đồng chung là `1 + 2*F + T`: `F` là số ô fragile mới được khối chiếm; `T` là số công tắc soft/heavy vừa kích hoạt. Engine cơ bản chưa có công tắc nên `T = 0`. Bước thường có giá 1; bước chiếm thêm một ô fragile có giá 3. BFS tối ưu số bước, UCS/A* tối ưu tổng chi phí.

## Phạm vi mốc 18/10

Bản cơ bản xử lý map nền, các hướng lăn, tư thế khối, rơi, goal và fragile. Cầu, công tắc, tách/nhập chưa được triển khai; validator từ chối rõ map có tile nâng cao để ngăn kết quả sai. Các cơ chế đó nằm trong đặc tả chung và sẽ bổ sung sau.
