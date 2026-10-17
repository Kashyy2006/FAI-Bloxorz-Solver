# Nguồn map và ghi chú chuyển đổi

**Phụ trách:** Thành viên 4 ghi nguồn; thành viên 5 tổng hợp tài liệu. Khảo sát ngày **15/10/2026** qua trang repo, GitHub API và nội dung raw tại các commit dưới đây. Chỉ lấy dữ liệu map và giấy phép; không tải/chạy thuật toán giải của nguồn.

**Cập nhật dữ liệu 17/10/2026:** đã chuyển 6 map AchrafMez và 7 map Frank Buss / Damien Clarke vào `data/maps/prepared/` qua 5 lô kiểm tra dữ liệu. Có [dữ liệu nguồn ngoại tuyến](map_sources/README.md), [converter](convert_maps.py), [ghi chú Achraf](achraf-map-conversion.md), [ghi chú Frank](frank-map-conversion.md) và [hash từng map](../maps/README.md#dữ-liệu-đã-chuyển-đổi). Bộ đã khóa **18 map** gồm 4 basic và 14 prepared, có một fixture original vô nghiệm nâng cao. [Manifest](../map_bundle.json) khóa đường dẫn/nguồn/hash/trạng thái; [hồ sơ từng map](map-bundle-evidence.md) ghi mục đích, witness/phân tích, mức tin cậy và khảo sát bổ sung trước khi tự tạo. Chưa xác nhận engine/replay/solver. Các mục khảo sát dưới đây ghi bằng chứng tại thời điểm khảo sát/lựa chọn.

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

Đó là kết quả vòng khởi tạo ngày 15/10, khi bộ dữ liệu gồm bốn map. Vòng khảo sát ngày 17/10 bên dưới mở rộng sang cơ chế nâng cao; kết quả chuyển đổi sau khảo sát được ghi ở đầu tài liệu.

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

Khảo sát nguồn ngoài đã tìm được ứng viên cho bảy nhóm cơ chế; **chưa có map vô nghiệm nâng cao được xác minh**. Nhóm cầu/công tắc và permanent có ứng viên nhiều cơ chế, cần witness đúng vai trò khi chọn map. Không đếm một level vào nhiều nhóm. Danh sách lựa chọn nằm bên dưới; việc chuyển JSON và xác nhận khả giải bằng engine vẫn chưa thực hiện.

Notice lưu nguyên byte cho hai nguồn dùng trong mẫu khảo sát: [AchrafMez-LICENSE.txt](AchrafMez-LICENSE.txt), [FrankBuss-license.txt](FrankBuss-license.txt). Giấy phép nguồn chỉ áp dụng phần dữ liệu tương ứng, không thay giấy phép toàn dự án. Không tiếp nhận code game/solver ngoài vào source của nhóm.

## Nguồn cho danh sách 18 map

**Ngày 17/10/2026.** Danh sách có ID, nhóm chính, difficulty dự kiến, bộ tối thiểu 15, ba map bổ sung và hai mở rộng nằm ở [catalog map](../maps/README.md#danh-sách-18-map-mục-tiêu). Chọn **13 map adapted mới và một fixture original vô nghiệm nâng cao**, giữ nguyên bốn map cũ (3 original, 1 adapted). Bộ đã khóa: 18 map, 14 adapted + 4 original. Đã có đủ JSON và manifest bộ cuối; các mục lựa chọn bên dưới giữ căn cứ nguồn, không thay bằng chứng engine.

### Nguồn đã chọn và byte kiểm tra lại

AchrafMez: giữ layout/start/goal và số hàng, pad cuối hàng ngắn bằng void; hàng rỗng cuối `level7` được giữ thành 17 void theo parser nguồn (JSON 12 × 17). Mã ô và liên kết theo [ánh xạ nguồn](advanced-map-source-survey.md#2-ánh-xạ-achrafmez-và-ứng-viên), giữ [MIT nguyên byte](AchrafMez-LICENSE.txt). File tải từ các URL ghim dưới đây, không tải hoặc chạy solver nguồn.

| ID dự kiến | File nguồn tại commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9` | Byte raw | SHA256 raw |
| --- | --- | ---: | --- |
| `fragile_01` | [level3.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level3.txt) | 161 | `7a36a4589fc483222920db929c00d86f1f80ed69a4afe353e1842899b97024e8` |
| `fragile_02` | [level7.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level7.txt) | 199 | `86e5db7b81ce39d4f6d3973e86a1b95d3190b1adc2f5c0e26cbb0dd4daf75293` |
| `soft_toggle_01` | [level4.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level4.txt) | 107 | `75687be941975108e25639cf906cba6a4f3adfc8ec3deaeaf1ed0228dcef8dad` |
| `soft_toggle_02` | [level6.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level6.txt) | 179 | `80a936bcd644fc1fe389d419c004f57e6a7452e758a87d3d094ad57fdf367413` |
| `heavy_01` | [level5.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level5.txt) | 161 | `f896dfc1ecbee5c17348b90144800c051c469d4307f0a8efa0a3cf0e8a207414` |
| `heavy_02` | [level10.txt](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level10.txt) | 179 | `de6d0f5542ef8c06990ca8518d92fd28f49e7846d7797ec463fc9ab71918d38d` |

Frank Buss/Damien Clarke: bảy màn được chọn cùng ở [Vide/levels.py](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/levels.py), commit `775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562`. Đọc phần literal chưa xoay bằng AST, không import/exec script hoặc dùng dữ liệu C đã xoay. File 27.641 byte, SHA256 `5c2773bb4c91126d9ae0be3cb1023b9b3c20d36323d1b9c5f967d51a02550bec`. Đối chiếu literal với [bloxorzlevels.txt](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/bloxorzlevels.txt) (18.833 byte, SHA256 `3e3dec961678e2b00d8d2d7cd2ea89aed2f2fd05b9ffb6b0ca1e88f04af5d6a3`): cả 33 màn trong danh sách chính khớp. Giữ [notice riêng](FrankBuss-license.txt), credit cả hai tác giả, phạm vi bài học phi thương mại.

Tọa độ bảng dưới đã đổi thành [row,col]. Nhóm cầu tách theo trạng thái đầu và toàn bộ tác động từng switch, không theo hình kề nhau hoặc chỉ ký tự l/r/k/q.

| ID dự kiến | Level nguồn | Start → goal | Nhóm cầu / switch | Điểm cần giữ |
| --- | --- | --- | --- | --- |
| `bridge_01` | 14 `levelub` / 210362 | [2,4] → [8,3] | 2 / 2 | Hai heavy toggle, hai hàng cầu đóng riêng |
| `permanent_open_01` | 18 `levelsc` / 284933 | [4,2] → [8,12] | 3 / 6 | Soft on/off và heavy toggle; giữ mọi effect |
| `permanent_close_01` | 11 `leveldw` / 291709 | [5,2] → [1,4] | 1 / 1 | Cầu mở ban đầu, soft off |
| `split_merge_01` | 8 `levelss` / 499707 | [4,1] → [4,13] | 0 / 1 | Destinations [[1,10],[7,10]], active_destination=0 |
| `split_merge_02` | 9 `levelre` / 074355 | [4,1] → [6,7] | 0 / 1 | Destinations [[4,12],[4,2]], active sau sort=1 |
| `combined_01` | 15 `levelht` / 098598 | [8,1] → [8,12] | 4 / 5 | Split, heavy/soft, toggle/off; hai trạng thái cầu ban đầu |
| `combined_02` | 20 `leveltb` / 543019 | [2,8] → [8,13] | 3 / 6 | Split + soft toggle/off; giữ đè bằng khối không active |

**Tọa độ goal `levelss`:** raw đặt e ở x=13, y=4, nên goal là [4,13]. Tọa độ ở mục 5 hồ sơ khảo sát đã được đối chiếu với dữ liệu nguồn.

### Chọn/loại và khoảng trống

- Không lấy thêm bản của cùng màn từ [GBA levels.json](https://github.com/jacobcoughenour/bloxorz_gba/blob/f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d/game/levels.json), commit `f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d`. Tải lại 23.599 byte, SHA256 `f30ed31fd4259c336a7ecdd4870ab4f74b13c7c17055e9e6cc8a045eac6406fe`; chín bản `ub`, `dw`, `sc`, `ss`, `re`, `ht`, `tb`, `kn`, `hg` trùng literal Frank về tiles/spawn/switches/splits. Chỉ đọc để loại trùng, không tiếp nhận bộ GBA.
- Không thêm basic từ A/Matías vì bốn map đang có đủ vai trò. F `levelpp` bị loại nguyên trạng do đích split không phải floor; `leveltw`/`leveldd`/`levelmp`/`levelgv` không chọn vì effect hỗn hợp trên cùng switch. Không gỡ effect khó hoặc đổi nhãn thành original.
- Các nguồn ooodnakov, Otfried, lm-pcg chưa có quyền tiếp nhận rõ trong hồ sơ khảo sát vẫn không được chọn; không có kết luận mới về giấy phép của chúng.
- Giữ tối đa hai mở rộng từ cùng nguồn F: `levelkn` → `combined_03`, `levelhg` → `combined_04`, chưa tính vào 18; metadata biểu diễn được bằng schema, đích split là floor/không kề cạnh và khác bộ chính. Chỉ xét sau khi đủ nhóm và bộ chính đạt kiểm tra dữ liệu.
- Tự thiết kế duy nhất `advanced_unsolvable_01` vì khảo sát không có nguồn vô nghiệm nâng cao đủ căn cứ. [Blueprint và lý do](../maps/README.md#blueprint-original-cho-khoảng-trống-vô-nghiệm-nâng-cao) nằm ngoài map JSON. Đã có [JSON prepared](../maps/prepared/advanced_unsolvable_01.json), kiểm dữ liệu và [hồ sơ bất biến/witness tay](map-bundle-evidence.md#advanced_unsolvable_01); chưa xác minh witness bằng engine.

### Kiểm tra danh sách lựa chọn

- Đối chiếu trực tiếp catalog, dữ liệu nguồn và contract map-format/engine với yêu cầu cơ chế của đề bài.
- Script tạm chỉ đọc AST/literal/JSON và chuẩn hóa dữ liệu; không đưa code ngoài vào source, không gọi game/solver ngoài. Kiểm start trên floor, đúng một goal, target bridge, effect đồng nhất mỗi switch, split destinations floor/khác nhau/không kề cạnh; đếm nhóm theo toàn bộ liên kết.
- So 153 cặp của 18 ứng viên theo layout/start/goal/cơ chế sau bỏ viền void, chuẩn hóa tịnh tiến, tám phép quay/đối xứng, bỏ tên ID nhóm và giữ active destination. Không trùng cả khi kiểm thêm hình học/start/goal mà bỏ phân biệt loại ô. Blueprint original cũng nằm trong phép so. Đây không phải test chuẩn JSON đã chuyển hoặc xác minh luật nâng cao.
- Hai notice khớp raw từng byte; sáu hash A và hai hash dữ liệu F ở trên khớp byte tải lại. Tại lúc chốt lựa chọn chưa có JSON prepared; hash đầu ra sau chuyển đổi nằm ở [catalog](../maps/README.md#dữ-liệu-đã-chuyển-đổi).
- Đối chiếu bảng lựa chọn: 18 ID duy nhất; bộ 15 và bộ 18 khớp bảng phân bố nhóm, permanent có mở/đóng; ba map +3 đúng vai trò soft/heavy/split. Link và anchor nội bộ tồn tại, hash nguồn trong nhật ký khớp raw, bốn JSON cũ và các notice giữ nguyên byte.
- `python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v`: **104/104 đạt, không skip**, gồm bảy test map cũ. `git diff --check` đạt với các thay đổi tài liệu. Không thêm test/game validator mới cho bước chọn danh sách; kiểm tra lựa chọn dùng assert trong script tạm, dữ liệu prepared còn phải kiểm sau chuyển đổi. Chưa chạy engine nâng cao, GUI, replay hoặc benchmark.

AI hỗ trợ đọc đề bài, kiểm nguồn/metadata, chọn và loại trùng, soạn blueprint và hồ sơ. Chưa có kết quả solver hoặc số đo hiệu năng cho các map được chọn mới.

## Quy ước nguồn

- Map adapted phải giữ URL nguồn/commit, định danh level, bảng chuyển đổi và mô tả mọi ô/luật đã đổi. `source.conversion_notes` là đường dẫn từ repo root, không phải từ thư mục map.
- Giữ notice/giấy phép của dữ liệu đã tiếp nhận; [matuneville-LICENSE.txt](matuneville-LICENSE.txt) là bản byte nguyên gốc từ commit được ghim. Không sao chép giấy phép này thành giấy phép cho toàn repo.
- Map original ghi nguồn nội bộ đúng thực tế. Không gắn URL ngoài vào map tự thiết kế để gọi là adapted.
- Lời giải và chứng cứ thuộc [danh mục map](../maps/README.md), không thêm trường ngoài schema vào JSON. Nghiệm thu replay và map nâng cao vẫn chưa xác nhận. Nguồn có test không chứng minh engine nhóm đã chạy.
