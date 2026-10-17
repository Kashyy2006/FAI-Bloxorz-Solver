# Nguồn map và ghi chú chuyển đổi

**Phụ trách:** Thành viên 4 ghi nguồn; thành viên 5 tổng hợp tài liệu. Khảo sát ngày **15/10/2026** qua trang repo, GitHub API và nội dung raw tại các commit dưới đây. Chỉ lấy dữ liệu map và giấy phép; không tải/chạy thuật toán giải của nguồn.

## Truy xuất bộ cơ bản

| Map ID                | Loại nguồn | Tác giả / nguồn cụ thể                                                                                                                                                                                        | Xử lý                                                                                                                                  |
| --------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `basic_01`            | original   | Nhóm, ví dụ đầy đủ `basic_01` trong [contract map v1](../../docs/contracts/map-format.md)                                                                                                                     | Giữ nguyên dữ liệu/metadata, kể cả `source.reference=Team-created`                                                                     |
| `basic_turn_01`       | adapted    | Matías (`matuneville`), `level_2_2` trong repo [bloxorz-pathfinding](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs) | Chuyển ma trận số sang schema v1; giữ layout, start, goal; xem [ghi chú](basic_turn_01.md) và [giấy phép MIT](matuneville-LICENSE.txt) |
| `basic_cycle_01`      | original   | TV4, thiết kế nội bộ ngày 15/10/2026                                                                                                                                                                          | Sàn hình chữ nhật, chu trình và nhánh khác đường giải; không chuyển từ màn ngoài                                                       |
| `basic_unsolvable_01` | original   | TV4, thiết kế nội bộ ngày 15/10/2026                                                                                                                                                                          | Hành lang nhỏ và goal cô lập; nhãn false là kỳ vọng kiểm thử                                                                           |

## Nhật ký khảo sát

| Ứng viên đã đọc                                                                                                                                                                            | Phiên bản / định dạng                                                                                                                                                                         | Quyết định và lý do                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Matías / [bloxorz-pathfinding: levels_testing.rs](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs) | Commit `6af854a88ac3983ffed2ee12a9e26c4cc338aa76`; dữ liệu ma trận trong test Rust; MIT                                                                                                       | **Chọn `level_2_2`**: 4 × 4, chỉ ô cơ bản, có test gốc nêu expected length 7; chuyển dữ liệu thủ công, không lấy solver                                              |
| AchrafMez / [bloxorz: level0.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level0.txt)                                                    | Commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9`; text 6 × 5; [MIT](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/LICENSE.md), Copyright 2026 AchrafMez | Không tiếp nhận: đã chọn nguồn ma trận nhỏ có kỳ vọng độ dài cụ thể. Lưu làm ứng viên, chưa kiểm tra khả năng giải theo engine nhóm                                  |
| ooodnakov / [bloxorz_PAAI: level/1.json](https://github.com/ooodnakov/bloxorz_PAAI/blob/7a1ec2bfb97d66edc867ce17e208697b922fd38a/level/1.json)                                             | Commit `7a1ec2bfb97d66edc867ce17e208697b922fd38a`; JSON với size/maps/box/swX/swQ/swO, khác schema nhóm                                                                                       | Không tiếp nhận: JSON không dùng trực tiếp được; GitHub metadata trả license=null và tree không có file LICENSE. Không suy đoán quyền sử dụng; có nguồn MIT thay thế |

Đó là kết quả vòng khởi tạo ngày 15/10; bộ đang có vẫn gồm bốn map. Vòng khảo sát ngày 17/10 bên dưới mở rộng sang cơ chế nâng cao, chưa bổ sung map vào inventory.

## Khảo sát nguồn nâng cao ngày 17/10/2026

**Đã hoàn thành khảo sát nguồn nâng cao:** đọc lại ba đầu mối cũ, mở rộng bốn nguồn, ghim commit, đọc dữ liệu/notice, thử ánh xạ và chốt khoảng trống. Hồ sơ đầy đủ, bảng level, khác luật, SHA256 và mẫu schema nằm ở [khảo sát nguồn map nâng cao](advanced-map-source-survey.md).

| Nguồn đã đọc | Đề xuất chọn map | Căn cứ / giới hạn |
| --- | --- | --- |
| AchrafMez/bloxorz | Ưu tiên fragile và toggle soft/heavy | Đọc 13 `level0`–`level12`, parser/luật liên quan và MIT; có mẫu ánh xạ đầy đủ `level4` |
| FrankBuss/bloxorz | Chọn làm nguồn cho bài học phi thương mại: permanent, split/merge, kết hợp | Đọc dữ liệu 33 level trong danh sách chính và notice riêng; không gọi là MIT thuần, không tự mở rộng sang dùng thương mại |
| matuneville/bloxorz-pathfinding | Giữ `level_2_2` đã tiếp nhận; dự phòng basic | Bốn ma trận test đã đọc chỉ có mã 0/1/2/3, không bù nhóm nâng cao |
| ooodnakov/bloxorz_PAAI | Không tiếp nhận trong vòng này | Đã đọc JSON; metadata không khai báo license, tree không có notice cấp quyền rõ |
| otfried/cs109-scala | Tham khảo định dạng, không tiếp nhận level | Text có toggle/permanent/split rõ nhưng chưa thấy license cấp quyền; khác định dạng không phải lý do loại |
| jacobcoughenour/bloxorz_gba | Dự phòng, chưa tiếp nhận | JSON 33 level, GPL-3.0; chưa chọn vì đã có nguồn phù hợp và tránh thêm gói điều kiện phân phối; GPL không đồng nghĩa cấm dùng |
| sublevelgames/lm-pcg | Không tiếp nhận trong vòng này | Đã đọc mẫu dataset JSON switch và README; chưa thấy notice cấp quyền dataset, không suy quyền từ repo gốc |

Các nguồn ngoài đã có ứng viên cho bảy nhóm cơ chế; **chưa có map vô nghiệm nâng cao được xác minh**. Nhóm cầu/công tắc và permanent có ứng viên nhiều cơ chế, cần witness đúng vai trò khi chọn map. Không đếm một level vào nhiều nhóm. Chưa chốt 14 map bổ sung, chưa tạo map original để bù và chưa xác nhận khả giải bằng engine.

Notice lưu nguyên byte cho hai nguồn dùng trong mẫu khảo sát: [AchrafMez-LICENSE.txt](AchrafMez-LICENSE.txt), [FrankBuss-license.txt](FrankBuss-license.txt). Giấy phép nguồn chỉ áp dụng phần dữ liệu tương ứng, không thay giấy phép toàn dự án. Không tiếp nhận code game/solver ngoài vào source của nhóm.

## Quy ước nguồn

- Map adapted phải giữ URL nguồn/commit, định danh level, bảng chuyển đổi và mô tả mọi ô/luật đã đổi. `source.conversion_notes` là đường dẫn từ repo root, không phải từ thư mục map.
- Giữ notice/giấy phép của dữ liệu đã tiếp nhận; [matuneville-LICENSE.txt](matuneville-LICENSE.txt) là bản byte nguyên gốc từ commit được ghim. Không sao chép giấy phép này thành giấy phép cho toàn repo.
- Map original ghi nguồn nội bộ đúng thực tế. Không gắn URL ngoài vào map tự thiết kế để gọi là adapted.
- Lời giải và chứng cứ thuộc [danh mục map](../maps/README.md), không thêm trường ngoài schema vào JSON. Bốn map basic đã load theo snapshot 16/10; nghiệm thu replay và map nâng cao vẫn chưa xác nhận. Nguồn có test không chứng minh engine nhóm đã chạy.
