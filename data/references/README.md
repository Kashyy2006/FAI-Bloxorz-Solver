# Nguồn map và ghi chú chuyển đổi

**Phụ trách:** Thành viên 4 ghi nguồn; thành viên 5 tổng hợp tài liệu. Khảo sát ngày **15/10/2026** qua trang repo, GitHub API và nội dung raw tại các commit dưới đây. Chỉ lấy dữ liệu map và giấy phép; không tải/chạy thuật toán giải của nguồn.

## Truy xuất bộ cơ bản

| Map ID | Loại nguồn | Tác giả / nguồn cụ thể | Xử lý |
| --- | --- | --- | --- |
| `basic_01` | original | Nhóm, ví dụ đầy đủ `basic_01` trong [contract map v1](../../docs/contracts/map-format.md) | Giữ nguyên dữ liệu/metadata, kể cả `source.reference=Team-created` |
| `basic_turn_01` | adapted | Matías (`matuneville`), `level_2_2` trong repo [bloxorz-pathfinding](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs) | Chuyển ma trận số sang schema v1; giữ layout, start, goal; xem [ghi chú](basic_turn_01.md) và [giấy phép MIT](matuneville-LICENSE.txt) |
| `basic_cycle_01` | original | TV4, thiết kế nội bộ ngày 15/10/2026 | Sàn hình chữ nhật, chu trình và nhánh khác đường giải; không chuyển từ màn ngoài |
| `basic_unsolvable_01` | original | TV4, thiết kế nội bộ ngày 15/10/2026 | Hành lang nhỏ và goal cô lập; nhãn false là kỳ vọng kiểm thử |

## Nhật ký khảo sát

| Ứng viên đã đọc | Phiên bản / định dạng | Quyết định và lý do |
| --- | --- | --- |
| Matías / [bloxorz-pathfinding: levels_testing.rs](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs) | Commit `6af854a88ac3983ffed2ee12a9e26c4cc338aa76`; dữ liệu ma trận trong test Rust; MIT | **Chọn `level_2_2`**: 4 × 4, chỉ ô cơ bản, có test gốc nêu expected length 7; chuyển dữ liệu thủ công, không lấy solver |
| AchrafMez / [bloxorz: level0.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level0.txt) | Commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9`; text 6 × 5; [MIT](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/LICENSE.md), Copyright 2026 AchrafMez | Không tiếp nhận: đã chọn nguồn ma trận nhỏ có kỳ vọng độ dài cụ thể. Lưu làm ứng viên, chưa kiểm tra khả năng giải theo engine nhóm |
| ooodnakov / [bloxorz_PAAI: level/1.json](https://github.com/ooodnakov/bloxorz_PAAI/blob/7a1ec2bfb97d66edc867ce17e208697b922fd38a/level/1.json) | Commit `7a1ec2bfb97d66edc867ce17e208697b922fd38a`; JSON với size/maps/box/swX/swQ/swO, khác schema nhóm | Không tiếp nhận: JSON không dùng trực tiếp được; GitHub metadata trả license=null và tree không có file LICENSE. Không suy đoán quyền sử dụng; có nguồn MIT thay thế |

Đã tìm được JSON có sẵn, nhưng không cùng schema; vì vậy bộ hiện tại dùng một map ma trận được chuyển đổi. Không khẳng định đã khảo sát toàn bộ nguồn map trên Internet. Không tiếp nhận thêm màn để tăng số lượng ngoài bộ 4 map khởi tạo.

## Quy ước nguồn

- Map adapted phải giữ URL nguồn/commit, định danh level, bảng chuyển đổi và mô tả mọi ô/luật đã đổi. `source.conversion_notes` là đường dẫn từ repo root, không phải từ thư mục map.
- Giữ notice/giấy phép của dữ liệu đã tiếp nhận; [matuneville-LICENSE.txt](matuneville-LICENSE.txt) là bản byte nguyên gốc từ commit được ghim. Không sao chép giấy phép này thành giấy phép cho toàn repo.
- Map original ghi nguồn nội bộ đúng thực tế. Không gắn URL ngoài vào map tự thiết kế để gọi là adapted.
- Lời giải và chứng cứ thuộc [danh mục map](../maps/README.md), không thêm trường ngoài schema vào JSON. Trạng thái load/replay engine vẫn đang chờ; nguồn có test không chứng minh engine nhóm đã chạy.
