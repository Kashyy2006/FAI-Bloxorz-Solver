# Khảo sát nguồn map nâng cao

**TV4, ngày 17/10/2026.** Căn cứ: [map schema v1](../../docs/contracts/map-format.md) và [luật nhóm](../../docs/contracts/engine.md). Dữ liệu và catalog được đối chiếu trực tiếp với source nhóm sau lần sửa `basic_01` tại commit `e79f416115ee98513e9b8f037185f66d8f0c8ff1`.

Đã hoàn thành phần khảo sát, **không phải nghiệm thu bộ map**. Chưa chốt danh sách map bổ sung hoặc chuyển đổi theo lô. Các mẫu dưới đây ở trong tài liệu, không nằm trong `data/maps`, `prepared` hoặc inventory. Không chạy ứng dụng, script chuyển đổi hay solver của nguồn; chỉ đọc dữ liệu, notice và phần parser/luật cần để hiểu mã ô. Script nguồn được đọc như văn bản/literal, không `exec`/import.

## 1. Nguồn, phiên bản và quyết định

Link trong bảng đều ghim commit đã đọc qua GitHub API/raw ngày khảo sát; không chỉ dựa vào mô tả repo hoặc kết quả tìm kiếm.

| Nguồn / commit | File đã đọc / định dạng | Quyết định và lý do |
| --- | --- | --- |
| Matías / `matuneville/bloxorz-pathfinding`, `6af854a88ac3983ffed2ee12a9e26c4cc338aa76` | [Bốn ma trận trong test](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs), [MIT](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/LICENSE) | Giữ `level_2_2` cũ; ba màn còn lại chỉ là dự phòng basic. Không có dữ liệu fragile/cầu/split trong bốn ma trận đã đọc. |
| AchrafMez / `AchrafMez/bloxorz`, `898188ed31cf31d4ce4c39fec3e3846ed037eee9` | [13 level text](https://github.com/AchrafMez/bloxorz/tree/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels), [parser map.c](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/src/map.c), [box.c](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/src/box.c), [MIT](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/LICENSE.md) | **Ưu tiên chuyển** fragile và toggle. Có dữ liệu công tắc thật, không chỉ tên trong README. Hai file `zfortest`/`zlevel120` ngoài dãy chính chưa được xét. |
| Frank Buss và Damien Clarke theo notice / `FrankBuss/bloxorz`, `775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562` | [bloxorzlevels.txt](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/bloxorzlevels.txt), [levels.py](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/levels.py), [level.c](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/source/level.c), [block.c](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/source/block.c), [bloxorz.c](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/source/bloxorz.c), [notice](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/license.txt) | **Nguồn dùng được cho phạm vi bài học phi thương mại**, giữ nguyên notice và credit cả hai tên. Notice có hạn chế thương mại, không ghi nguồn này là MIT thuần. Có 33 màn trong danh sách `levels` chính; không đếm mọi biến `level*` là một màn được phát hành. Ưu tiên permanent/split/kết hợp theo mục 3. |
| `ooodnakov/bloxorz_PAAI`, `7a1ec2bfb97d66edc867ce17e208697b922fd38a` | [level/1.json](https://github.com/ooodnakov/bloxorz_PAAI/blob/7a1ec2bfb97d66edc867ce17e208697b922fd38a/level/1.json) đã khảo sát trước; đọc thêm [level/8.json](https://github.com/ooodnakov/bloxorz_PAAI/blob/7a1ec2bfb97d66edc867ce17e208697b922fd38a/level/8.json): size/maps/box/swX/swQ/swO/bridge | **Không tiếp nhận**: GitHub license=null, tree chưa thấy LICENSE/notice cấp quyền. File `8.json` còn ghi `level:4`, nên phải định danh theo đường dẫn, không dùng trường level làm ID tin cậy. Khác JSON có thể chuyển, nhưng không giải quyết thiếu quyền tiếp nhận. |
| Otfried Cheong / `otfried/cs109-scala`, `0097f4a7aac22e45868938d91476878bf422c8b2` | [Bài hướng dẫn chính chủ](https://otfried.org/courses/cs109/project-bloxorz.html), [README](https://github.com/otfried/cs109-scala/blob/0097f4a7aac22e45868938d91476878bf422c8b2/README.md), [level08](https://github.com/otfried/cs109-scala/blob/0097f4a7aac22e45868938d91476878bf422c8b2/bloxorz/levels/level08.txt), [level11](https://github.com/otfried/cs109-scala/blob/0097f4a7aac22e45868938d91476878bf422c8b2/bloxorz/levels/level11.txt) | **Tham khảo, chưa tiếp nhận**: text có metadata split, bridge ban đầu mở và permanent đóng; API license=null, tree/README không cho thấy giấy phép rõ. Không loại vì cần pad hàng hoặc đổi trục. |
| Jacob Coughenour / `jacobcoughenour/bloxorz_gba`, `f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d` | [game/levels.json](https://github.com/jacobcoughenour/bloxorz_gba/blob/f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d/game/levels.json): 33 object có tiles/spawn/switches/splits; [README](https://github.com/jacobcoughenour/bloxorz_gba/blob/f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d/README.md), [GPL-3.0](https://github.com/jacobcoughenour/bloxorz_gba/blob/f57ebb6bd57e9d2b42ab478a3d19e53028e62b1d/LICENSE) | **Dự phòng, không tiếp nhận lượt này**: JSON thuận tiện nhưng các level `ss`, `re`, `ht` trùng cấu trúc nguồn Frank đã đọc; không tăng số map bằng cách lấy cùng màn từ hai repo. GPL không cấm sử dụng; chưa chọn để tránh thêm gói điều kiện phân phối khi đã có nguồn phù hợp. |
| `sublevelgames/lm-pcg`, `9ea82e1b34116327163584a9fd608cd427e5f243` | [Bài tác giả](https://sublevelgames.com/blogs/2025-10-20-generate-bloxorz-map-with-gpt-2/), [README](https://github.com/sublevelgames/lm-pcg/blob/9ea82e1b34116327163584a9fd608cd427e5f243/readme.md), [puzzle_switch_all.json](https://github.com/sublevelgames/lm-pcg/blob/9ea82e1b34116327163584a9fd608cd427e5f243/data/bloxorz/puzzle_switch_all.json): grid phẳng/grid_w/grid_h/move/collectables/gimmick/switch | **Không tiếp nhận**: chưa tìm thấy license cấp quyền cho dataset tại commit; không suy giấy phép từ repo mà nó fork. Có thêm collectables và luật Mindcraft cần đối chiếu, không coi `move` là oracle theo luật nhóm. Chỉ đọc mẫu trong bộ switch, không tuyên bố kiểm toàn bộ các bộ bridge/glass. |

Chưa tiếp nhận dữ liệu từ các nguồn bị loại/dự phòng vào repo nhóm. Bản tải để đọc nằm trong thư mục tạm, không phải artifact bàn giao. Không liên hệ tác giả xin phép trong lượt khảo sát này.

## 2. Ánh xạ AchrafMez và ứng viên

Tọa độ text là hàng/cột từ 0. Giữ số hàng; pad cuối hàng ngắn bằng `void` tới chiều rộng lớn nhất, không quay/cắt layout. `.` và `-` đều là void trong parser; F=floor, S=floor+start, T=goal, O=fragile. Ký tự A–Z còn lại là soft; chữ số 0–9 là heavy, nối 0→a, 1→b, ...; chữ thường là ô bridge cùng nhóm ký tự và ban đầu đóng. Mỗi công tắc đảo nhóm cầu có chữ tương ứng.

| File trong `levels/` | Cơ chế nhìn thấy từ dữ liệu | Quyết định khảo sát |
| --- | --- | --- |
| `level0.txt`, `level1.txt`, `level2.txt` | Basic | Dự phòng; không bù thiếu cơ chế |
| `level3.txt`, `level7.txt` | Fragile, bố cục khác nhau | Ưu tiên hai ứng viên fragile |
| `level4.txt` | Soft A→a, heavy 1→b, hai nhóm cầu | Ưu tiên toggle; đã thử schema đầy đủ ở mục 4 |
| `level5.txt` | Heavy 0→a | Ưu tiên ca heavy |
| `level6.txt` | Soft A/B/C→a/b/c | Ưu tiên soft nhiều cầu |
| `level8.txt`, `level9.txt` | Soft/heavy/cầu | Dự phòng toggle; cần kiểm witness riêng |
| `level10.txt` | Fragile + heavy 0→a | Ứng viên heavy có tương tác fragile |
| `level11.txt`, `level12.txt` | Nhiều công tắc/cầu; level11 có fragile | Dự phòng; không suy từ nhiều cơ chế thành ca split |

`map.c` không có mã split hoặc effect permanent; không dùng nguồn này để bù hai nhóm đó. `box.c` có cờ pressed và chỉ bỏ cờ khi rời ô, nhưng còn kiểm goal trước công tắc và chưa thấy kiểm lại toàn bộ hỗ trợ sau toggle trong `checkbox`. Vì vậy chỉ tiếp nhận layout/link cầu; contract nhóm quyết định luật, không lấy app nguồn làm oracle. Cơ chế giới hạn thời gian/số bước của app không chuyển sang map nhóm. Không có lời giải tham chiếu đã kiểm cho các ứng viên mới; bỏ `expected_solvable` khi chưa đủ căn cứ.

## 3. Ánh xạ FrankBuss và sàng lọc theo level

Chọn dữ liệu **chưa xoay** trong `Vide/bloxorzlevels.txt`/phần literal `Vide/levels.py`: 10 hàng × 15 cột. Nguồn ghi tọa độ `[x,y]`; chuyển thành `[row,col]=[y,x]`. Không trộn với `plevels.py`/C sinh ra: script nguồn xoay 90 độ thành 15 hàng × 10 cột.

| Mã nguồn / metadata | Đích schema v1 |
| --- | --- |
| space / b / e / f | void / floor / goal / fragile |
| s / h / v | soft / heavy / split, khai báo đúng một switch cho mỗi ô |
| l,r / k,q | bridge ban đầu đóng / mở; không suy nhóm chỉ từ cặp ký tự |
| onoff / on / off | toggle / permanent open=true / permanent open=false |
| swatch + x + y | Tìm từ tọa độ switch trong grid; không tách chuỗi chữ số theo một vị trí cố định |
| Mảng split `[x1,y1,x2,y2]` | destinations `[[y1,x1],[y2,x2]]`, active_destination=0 theo khối SPLIT1 được điều khiển trước |

Nhóm cầu phải tách theo **trạng thái đầu và toàn bộ tác động từ từng công tắc**, rồi đặt ID ổn định. Các ô kề nhau vẫn có thể cần hai nhóm nếu chịu tác động khác nhau. Một công tắc nguồn vừa `on` vừa `off` trên các đích khác nhau không biểu diễn trực tiếp bằng một `effect` của schema v1; không tự nhân bản công tắc trên cùng ô hoặc bỏ bớt tác động.

Số màn dưới đây lấy từ danh sách `levels` chính trong `levels.py`, không lấy thứ tự khai báo biến trong file text.

| Level nguồn | Cơ chế / dữ liệu đã đối chiếu | Đề xuất chọn map |
| --- | --- | --- |
| 8 `levelss` (499707) | Split [x4,y4]→[10,1],[10,7]; hai đích b, cách 6 ô | Ưu tiên split; thử ánh xạ mục 5 |
| 9 `levelre` (074355) | Split [13,4]→[12,4],[2,4]; hai đích b, cách 10 ô | Ưu tiên split khác đường đi; cần giữ active khi sort |
| 10 `levelpp` (300590) | Split có đích [13,1] chính là ô v; còn soft/heavy/toggle | **Không chọn chuyển nguyên trạng**: destinations phải là floor; cần thay layout/đích có ghi chú nếu xét lại |
| 11 `leveldw` (291709) | Soft [8,6] đặt off hai ô k ban đầu mở [6,0],[6,1] | Ưu tiên permanent đóng |
| 14 `levelub` (210362) | Hai heavy điều khiển hai hàng cầu đóng | Ứng viên nhóm cầu; không phải ca cầu cô lập mọi cơ chế khác |
| 15 `levelht` (098598) | Soft/heavy/toggle/off + split [7,5]→[13,1],[1,8], cả hai đích b | Ưu tiên kết hợp; tác động từng switch đồng nhất mode |
| 18 `levelsc` (284933) | Có soft đặt on, soft đặt off, heavy toggle; target cùng switch đồng nhất effect | Ứng viên permanent mở; có cả đóng nên cần witness nêu đúng công tắc |
| 20 `leveltb` (543019) | Soft toggle/off + split [7,4]→[13,1],[13,7], cả hai đích b | Ưu tiên kết hợp thứ hai, khác `levelht` |
| 24 `levelkn` (088198) | Heavy permanent on + split, đích [6,7],[8,7] là b, không kề cạnh | Dự phòng permanent mở/kết hợp |
| 26 `levelhg` (426329) | Soft off/heavy on + split, đích [12,3],[10,5] là b | Dự phòng kết hợp |
| 17 `leveltw`, 25 `leveldd`, 29 `levelmp`, 30 `levelgv` | Có một switch tác động khác mode lên các ô khác nhau | Không chọn chuyển nguyên trạng bằng schema hiện tại |

Nguồn có luật cần lưu ý: Vectrex xử lý merge trước một số kiểm tra tile/switch trong `bloxorz.c`, còn nhóm xác định cạnh nhấn trước teleport/merge; không có căn cứ coi oracle nguồn là tương đương. `level.c` xác nhận k/q ban đầu mở và on/off là phép đặt, không phải toggle một lần. `block.c` cho thấy điều khiển SPLIT1 trước, hoán đổi và merge theo cạnh. Chỉ dùng hiểu metadata, không chép luật vào engine nhóm.

## 4. Thử ánh xạ đầy đủ: AchrafMez `level4.txt`

Nguồn 6 × 17; giữ layout/start/goal. A ở [2,3], 1 ở [1,9]; cầu a=[3,5],[3,6], b=[4,11],[4,12]. Bản xem trước sau **chỉ dùng kiểm tra phép ánh xạ**, không phải file prepared hoặc map đã xác nhận engine. `id` và `conversion_notes` dưới đây dành riêng mẫu tài liệu, chưa phải ID/path của map bàn giao. Chưa gắn difficulty được đo hoặc nhãn khả giải; medium chỉ là dự kiến.

```json
{
  "schema_version": 1,
  "id": "trial_achraf_level4",
  "name": "Conversion trial: Achraf level4",
  "difficulty": "medium",
  "rows": 6,
  "cols": 17,
  "grid": [
    ["void", "void", "void", "void", "void", "void", "void", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "floor", "void"],
    ["void", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "heavy", "floor", "void", "void", "floor", "goal", "floor", "void"],
    ["void", "floor", "floor", "soft", "floor", "void", "void", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "floor", "void"],
    ["void", "floor", "floor", "floor", "floor", "bridge", "bridge", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "floor", "void"],
    ["void", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "floor", "floor", "bridge", "bridge", "floor", "floor", "floor", "void"],
    ["void", "floor", "floor", "floor", "floor", "void", "void", "floor", "floor", "floor", "floor", "void", "void", "void", "void", "void", "void"]
  ],
  "start": [3, 1],
  "bridges": [{"id": "b01", "cells": [[3, 5], [3, 6]], "initial_open": false}, {"id": "b02", "cells": [[4, 11], [4, 12]], "initial_open": false}],
  "switches": [{"id": "s01", "cell": [2, 3], "type": "soft", "effect": {"mode": "toggle", "targets": ["b01"]}}, {"id": "s02", "cell": [1, 9], "type": "heavy", "effect": {"mode": "toggle", "targets": ["b02"]}}],
  "source": {"kind": "adapted", "reference": "https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels/level4.txt", "conversion_notes": "data/references/advanced-map-source-survey.md"}
}
```

`source.kind=adapted` dù sau này cần sửa layout. Khi tiếp nhận map thật, ghi notes riêng và đổi ID/path theo danh sách map đã chọn. Notice MIT nguyên byte: [AchrafMez-LICENSE.txt](AchrafMez-LICENSE.txt).

## 5. Kiểm tra thêm metadata split: FrankBuss `levelss`

Chuyển start [x1,y4]→[4,1], goal [x12,y4]→[4,12], split [x4,y4]→[4,4]. destinations `[[1,10],[7,10]]` đều là b→floor, khác nhau và không kề cạnh. active_destination=0 điều khiển ô [1,10], sau sort active vẫn 0. Với `levelre`, destinations giữ `[[4,12],[4,2]]`; sau sort cells thành `[[4,2],[4,12]]`, active phải là 1 để giữ điều khiển [4,12]. Đây là đối chiếu metadata, chưa chạy transition/SWITCH/merge.

```json
{
  "id": "s01",
  "cell": [4, 4],
  "type": "split",
  "destinations": [[1, 10], [7, 10]],
  "active_destination": 0
}
```

Notice [FrankBuss-license.txt](FrankBuss-license.txt) giữ nguyên cả hạn chế thương mại và credit Frank Buss/Damien Clarke. Khi phân phối dữ liệu chuyển đổi, giữ notice và ghi ngày/phần chuyển đổi; không đổi nhãn thành dữ liệu original của nhóm.

## 6. Kết luận khảo sát và khoảng trống

| Nhóm map còn thiếu | Ứng viên nguồn ngoài qua khảo sát | Việc chọn và chuyển đổi map phải giải quyết |
| --- | --- | --- |
| Fragile ×2 | Achraf `level3`, `level7` | Chọn witness nằm được đỡ/đứng rơi, chưa xác nhận khả giải |
| Cầu ×1 | Frank `levelub`, hoặc Achraf `level4` | Chọn một vai trò chính; nếu cần fixture cầu cô lập thật sự thì thiết kế nhỏ sau khảo sát này |
| Soft/toggle ×2 | Achraf `level6`, `level4`; có màn dự phòng | Witness giữ đè/rời/nhấn lại; không gán một map đồng thời vào nhóm heavy |
| Heavy ×2 | Achraf `level5`, `level10` | Witness nằm không nhấn/UPRIGHT nhấn; khối nhỏ cần fixture split hoặc test độc lập |
| Permanent ×2 | Frank `levelsc` cho đặt mở, `leveldw` cho đặt đóng; `levelkn` dự phòng | `levelsc` không thuần một hiệu ứng, phải chọn/ghi witness rõ; nếu không phù hợp vai trò thì dùng fixture original có lý do |
| Split/merge ×2 | Frank `levelss`, `levelre` | Đích floor đã kiểm; SWITCH/merge/active và khả giải chưa kiểm engine |
| Kết hợp ×2 | Frank `levelht`, `leveltb`; `levelhg` dự phòng | Tách nhóm cầu đúng signature; giữ mọi effect, không dùng `levelpp` nguyên trạng |
| Vô nghiệm nâng cao ×1 | **Chưa có nguồn đủ căn cứ** | Có thể tự thiết kế ca tối thiểu sau khảo sát này; phân tích tay riêng, không gọi đã chứng minh engine |

Đây là **pool ứng viên**, không phải danh sách 18 map đã chốt, không đếm vào inventory hiện tại. Chưa cần tự tạo hàng loạt: trước hết dùng nguồn ngoài cho các nhóm đã có ứng viên. Ngoài map vô nghiệm, các witness hồi quy cô lập (cầu, permanent, heavy ở SPLIT) có thể còn cần map tự thiết kế; mỗi map đó phải dẫn nhật ký này và lý do cụ thể. Không tăng số lượng bằng cách xoay/đổi tên cùng màn hoặc lấy bản trùng từ GBA/CS109.

Nếu phạm vi sử dụng về sau vượt bài học phi thương mại, dừng dùng dữ liệu Frank để rà quyền hoặc thay bằng thiết kế độc lập; không suy notice của repo khác mở rộng quyền nguồn này. Khảo sát này không kết luận đã có 14 map adapted phù hợp mọi mục tiêu kiểm thử.

## 7. Bằng chứng kiểm tra

SHA256 tính trên byte raw, chưa chuẩn hóa newline. Các link dữ liệu ở trên đủ truy xuất lại; chỉ notice và mẫu tài liệu được lưu vào repo.

| File nguồn | Byte | SHA256 |
| --- | ---: | --- |
| Achraf `LICENSE.md` | 1066 | `42a2d09d2b6a927b8754ae6f8b72bd77c5ec56c0221896a9ed4b125ced9a1196` |
| Achraf `levels/level3.txt` | 161 | `7a36a4589fc483222920db929c00d86f1f80ed69a4afe353e1842899b97024e8` |
| Achraf `levels/level4.txt` | 107 | `75687be941975108e25639cf906cba6a4f3adfc8ec3deaeaf1ed0228dcef8dad` |
| Achraf `levels/level7.txt` | 199 | `86e5db7b81ce39d4f6d3973e86a1b95d3190b1adc2f5c0e26cbb0dd4daf75293` |
| Frank `license.txt` | 1369 | `3811ab0b0c1ee1d7c9c6709f6ea180ee712ab2a6a4ceee4930ea579f02c536ce` |
| Frank `Vide/bloxorzlevels.txt` | 18833 | `3e3dec961678e2b00d8d2d7cd2ea89aed2f2fd05b9ffb6b0ca1e88f04af5d6a3` |
| Otfried `bloxorz/levels/level08.txt` | 140 | `a9be7844dd21d6c9570dd9d90ccf6c701c9e196280669b950483932c0ba5bb78` |
| GBA `game/levels.json` | 23599 | `f30ed31fd4259c336a7ecdd4870ab4f74b13c7c17055e9e6cc8a045eac6406fe` |

Kết quả kiểm tra ngày 17/10/2026:

- Tải lại hai notice ở commit ghim: bản lưu trong repo **trùng từng byte** với raw, đúng SHA256 trong bảng. `.gitattributes` đặt `-text` cho hai notice để Git không chuyển newline.
- Mẫu Achraf `level4`: grid 6 × 17, start/goal, toàn bộ ô bridge, switch type và target khớp text nguồn; JSON đọc được, không thêm `expected_solvable`.
- Đọc literal, không chạy script Frank: danh sách chính có 33 màn; kiểm start/goal/kích thước, target bridge, effect đồng nhất từng switch và destinations floor/không kề cạnh cho bảy ứng viên `ss`, `re`, `ht`, `tb`, `sc`, `dw`, `ub`. Phát hiện đích v của `pp` để loại chuyển nguyên trạng. Đây là sàng lọc, không phải validator/engine nghiệm thu từng map.
- JSON GBA có 33 màn; layout và spawn của `ss`, `re`, `ht` trùng dữ liệu Frank tương ứng, không dùng làm ba map mới khác nguồn.
- Tám dòng byte/hash trong bảng khớp bản raw đã đọc; các link file nội bộ trong README/hồ sơ tồn tại. Inventory vẫn bốn JSON; không sửa map hoặc source/test.
- `python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v`: **104/104 đạt, không skip**. Trong đó bảy test map có chạy; không cần chạy lặp lại riêng cùng test.
- `git diff --cached --check` cảnh báo 24 dòng của notice Frank vì nguồn dùng CR-CR-LF; giữ nguyên byte đã xác minh, không sửa notice để xóa cảnh báo. Kiểm whitespace các file còn lại đạt. Không chạy engine/GUI/benchmark hoặc solver nguồn; các kiểm tra cấu trúc bên trên không chứng minh khả giải.

AI hỗ trợ tìm nguồn, đối chiếu metadata, soạn hồ sơ và kiểm tra byte/phép ánh xạ. Không có số đo solver/benchmark từ lượt này. Không gọi khung dự kiến 2–3 giờ trong kế hoạch là thời gian đã thực hiện.
