# Bộ map

**Phụ trách:** Thành viên 4, phối hợp thành viên 1 về schema/engine. Chuẩn bị ngày 15/10/2026 theo [schema v1](../../docs/contracts/map-format.md).

**Dữ liệu đã khóa ngày 17/10/2026:** 4 map basic ở root và **14 map nâng cao trong `prepared/`**, tổng **18 JSON** (14 adapted + 4 original). [Manifest](../map_bundle.json) khóa inventory, nguồn/hash và trạng thái riêng từng map; [hồ sơ kiểm tra](../references/map-bundle-evidence.md) ghi mục đích, witness/phân tích và mức tin cậy. Xem thêm [hash chuyển đổi](#dữ-liệu-đã-chuyển-đổi), [ghi chú Achraf](../references/achraf-map-conversion.md) và [ghi chú Frank](../references/frank-map-conversion.md). Dữ liệu đạt kiểm tra; engine/replay/solver chưa xác nhận, map nâng cao chưa đưa vào menu.

Bộ khởi tạo có 4 map dùng chung cho GUI và các solver. Chỉ có `floor`, `void`, `goal`; tất cả ở mức `easy`, `bridges=[]`, `switches=[]`. Phần nâng cao đã được bổ sung trong prepared; bộ dữ liệu chưa có số đo benchmark cuối kỳ.

**Trạng thái:** JSON và test dữ liệu đã được chuẩn bị. Lời giải, chu trình và tập trạng thái dưới đây là oracle đối chiếu từ contract/nguồn và rà luật bằng tay; **chưa nghiệm thu replay bằng engine thật**. Lượt kiểm tra ngày 17/10 chỉ kiểm tra dữ liệu và test thành phần TV4. Nhãn `expected_solvable` không phải kết quả solver và không được dùng để quyết định status.

## Danh mục

| ID / file | Kích thước | Start | Goal | Kỳ vọng có lời giải | Nguồn / vai trò |
| --- | --- | --- | --- | --- | --- |
| [basic_01](basic_01.json) | 3 × 7 | [1,1] | [1,4] | true | Ví dụ nội bộ trong contract, hai bước |
| [basic_turn_01](basic_turn_01.json) | 4 × 4 | [0,2] | [2,3] | true | Chuyển từ map `level_2_2`, đổi hướng và nằm qua goal |
| [basic_cycle_01](basic_cycle_01.json) | 7 × 9 | [1,1] | [4,7] | true | Nội bộ, chu trình và nhánh phụ |
| [basic_unsolvable_01](basic_unsolvable_01.json) | 3 × 9 | [1,1] | [1,7] | false | Nội bộ, goal cô lập |

Nguồn từng map và nhật ký khảo sát ở [data/references](../references/README.md); map chuyển đổi có [ghi chú riêng](../references/basic_turn_01.md) và giấy phép đi kèm. Map đổi hướng giữ nguyên dữ liệu nguồn 4 × 4, thay cho phương án tự thiết kế trên hình chữ nhật.

## Lời giải và chứng cứ tham chiếu

Tọa độ `[row, col]` từ 0. Trong các bảng, U/H/V viết tắt cho UPRIGHT/HORIZONTAL/VERTICAL. Trạng thái nguyên khối luôn có `active=None`, `bridges=()`; test tích hợp phải so full `state_key`. Actions và chứng cứ để ngoài JSON để không thêm trường trái schema.

### Hai bước lăn

`RIGHT, RIGHT`: U [[1,1]] → H [[1,2],[1,3]] → U [[1,4]] thắng. Length/cost = 2 theo ví dụ đầy đủ của contract.

### Đổi hướng và nằm qua goal

Chuỗi tham chiếu: `DOWN, RIGHT, UP, LEFT, DOWN, DOWN, RIGHT`.

| Sau hành động | Mode | Cells | Kỳ vọng khi replay |
| --- | --- | --- | --- |
| Bắt đầu | U | [[0,2]] | Chưa thắng |
| DOWN | V | [[1,2],[2,2]] | OK |
| RIGHT | V | [[1,3],[2,3]] | OK: nằm qua goal, chưa thắng |
| UP | U | [[0,3]] | OK |
| LEFT | H | [[0,1],[0,2]] | OK |
| DOWN | H | [[1,1],[1,2]] | OK |
| DOWN | H | [[2,1],[2,2]] | OK |
| RIGHT | U | [[2,3]] | WON |

Length/cost đề xuất = 7. Test gốc của nguồn cũng ghi độ dài kỳ vọng 7; chưa chạy solver của repo để xác nhận. Hai hành động đầu là witness riêng cho ca goal bị khối nằm chiếm mà `is_goal` vẫn false. Không cần sửa goal hoặc loại ô nào của nguồn.

### Chu trình và nhánh phụ

- Lời giải tham chiếu: `RIGHT, RIGHT, RIGHT, RIGHT, DOWN, DOWN`, length/cost đề xuất = 6. Các mốc đứng lần lượt là [1,1] → [1,4] → [1,7] → [4,7]. Chưa dùng làm khẳng định tối ưu.
- Chu trình: `RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, UP, UP`. Các mốc đứng: [1,1] → [1,4] → [4,4] → [4,1] → [1,1]; không đi qua goal. Replay phải về đúng full key ban đầu.
- Nhánh khác đường giải: `DOWN, DOWN` từ initial state đến U [[4,1]]. Không khẳng định đây là ngõ cụt.

Mỗi chuỗi trên bắt đầu lại từ initial state. Không nối chuỗi sau WON. Sự tồn tại của chu trình không thay thế kiểm thử chống lặp ở solver; không yêu cầu DFS trả đúng chuỗi hoặc độ dài tối ưu.

### Goal cô lập

Oracle dự kiến gồm đúng 3 state đạt được. Bảng dưới liệt kê đầy đủ 4 hướng từ mỗi state theo luật cơ bản:

| State | UP / DOWN | LEFT | RIGHT |
| --- | --- | --- | --- |
| U [[1,1]] | LOST | LOST | H [[1,2],[1,3]] |
| H [[1,2],[1,3]] | LOST | U [[1,1]] | U [[1,4]] |
| U [[1,4]] | LOST | H [[1,2],[1,3]] | LOST |

Goal [1,7] nằm ngoài tập trên. Đây là chứng minh theo bố trí và bảng luật, chưa phải bằng chứng engine chạy: khi có engine cần duyệt `successors` đến cạn frontier, đối chiếu tập 3 full key và không có goal. Solver chuẩn phải trả UNSOLVABLE, các trường actions/length/cost là null; timeout không chứng minh vô nghiệm.

## Kiểm tra dữ liệu

Từ repo root, không cần cài thêm thư viện:

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_maps.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

Test map kiểm tra danh mục, layout/start/goal, metadata và kiểu dữ liệu cơ bản, bản sao ví dụ contract, nguồn/ghi chú chuyển đổi/giấy phép và SHA256 dưới đây. Test dùng đường dẫn từ vị trí file, không phụ thuộc working directory. Không chấp nhận chạy 0 test làm bằng chứng đạt.

Đã chạy ngày 15/10/2026 với Python 3.12.10: **7/7 test dữ liệu đạt; tổng 31/31 test solver đạt** (11 BFS, 13 common, 7 map). Các test BFS hiện dùng đồ thị giả; kết quả này không bao gồm kiểm thử engine, replay hoặc benchmark.

Đây là test fixture cho bộ cơ bản, **không thay validator `load_map` của engine** và không chạy luật game. Chưa có kiểm thử engine bị skip để làm suite xanh.

## Phiên bản dữ liệu

Chuẩn bị trên code nền `b08210650ad836d47283806d35682ec92258322d`, Python 3.12.10. Hash SHA256 đối chiếu lại từ byte JSON ngày 17/10/2026 tại HEAD nền `e79f416115ee98513e9b8f037185f66d8f0c8ff1`:

| ID | SHA256 |
| --- | --- |
| `basic_01` | `104bf008099b4a760cf79acdcf29ae9caf0b0d7c9c33df42286d7371f4236e58` |
| `basic_turn_01` | `aad9c38aae3c630ac3e9d4f36cc1d8a91bf4440505e7082b94a0fda2b95bb2d3` |
| `basic_cycle_01` | `6054d54a00890ac32d90886e5125e4cd0d80b9312d72e1fd64c1b04c7428f82f` |
| `basic_unsolvable_01` | `4d515ea5ea56accfe9f4199fea96100eb8d2582df0c63187c81ca8170ab1b6ae` |

Hash khóa bản dữ liệu đã chuẩn bị; chưa tuyên bố bộ map đã nghiệm thu engine. Khi thay map, cập nhật hash và oracle liên quan, chạy lại kiểm tra trước khi thu số liệu. Mọi solver phải dùng cùng file/hash và trạng thái đầu; không gán kết quả của bản cũ cho bản mới.

## Kiểm tra dữ liệu và sửa hash ngày 17/10/2026

- Branch: `feature/TV4-search-and-evaluation`; HEAD trước sửa: `e79f416115ee98513e9b8f037185f66d8f0c8ff1`; working tree sạch.
- Python 3.12.10. Hai lệnh ở mục kiểm tra dữ liệu được chạy từ repo root, pattern giữ đúng chữ hoa `TV4`, không có test bị skip.
- Trước sửa: map **6/7 đạt**, TV4 **103/104 đạt** (7 test map nằm trong 104 test TV4). Lỗi duy nhất: `test_map_hashes_are_recorded_in_catalog`, subtest `basic_01`.
- `basic_01` khớp toàn bộ JSON ví dụ contract qua `test_two_rolls_map_matches_full_contract_example`. Catalog lưu hash byte cũ sau commit `e79f416`; chỉ sửa hash catalog, không đổi JSON hoặc bỏ/nới assertion. Ba hash còn lại khớp.
- Sau sửa: map **7/7 đạt**, TV4 **104/104 đạt**. Giữ nguyên layout/start/goal, nguồn (3 original, 1 adapted), nhãn kỳ vọng và toàn bộ oracle của bốn map.
- Lượt kiểm tra ngày 17/10 không chạy engine, GUI hoặc integration; kết quả test dữ liệu và thành phần không thay cho nghiệm thu hệ thống.

### Nhóm cơ chế cần bổ sung map

Bốn map hiện có chỉ thuộc nhóm basic (đã đủ 4). Chưa có map cho các nhóm dưới đây; mỗi map bổ sung chỉ tính vào một nhóm chính:

| Nhóm chính còn thiếu | Cần thêm tối thiểu | Mục tiêu thêm | Phân biệt cần có |
| --- | ---: | ---: | --- |
| Fragile | 2 | 2 | Nằm được đỡ / đứng rơi, hai vai trò hoặc bố trí khác nhau |
| Cầu | 1 | 1 | Mở/đóng và witness cấu hình cầu |
| Soft/toggle | 1 | 2 | Nhấn mới, giữ đè, rời rồi nhấn lại |
| Heavy | 1 | 2 | Nằm/khối nhỏ không nhấn, UPRIGHT mới nhấn |
| Permanent | 2 | 2 | Một map đặt mở, một map đặt đóng |
| Split/merge | 1 | 2 | Tách, SWITCH, active sau sort và nhập |
| Kết hợp | 2 | 2 | Có cầu/công tắc cùng split/merge |
| Vô nghiệm nâng cao | 1 | 1 | Phân tích kỳ vọng rõ, chưa coi là chứng minh engine |
| **Tổng bổ sung** | **11** | **14** | **Cộng 4 basic = tối thiểu 15, mục tiêu 18 map** |

Lượt kiểm tra dữ liệu chưa tiếp nhận hoặc tự thiết kế map mới. Nguồn ngoài cho các nhóm còn thiếu được ghi trong [nhật ký nguồn](../references/README.md).

## Danh sách 18 map mục tiêu

**Chốt lựa chọn ngày 17/10/2026, tại HEAD nền `53623791166261f234ceeae5b05c463ded9c397e`.** Chọn **18 map = 4 map cũ + 13 map chuyển từ nguồn ngoài + 1 map original bù vô nghiệm nâng cao**. Bộ tối thiểu là 15 dòng đánh dấu **15**; ba dòng **+3** nâng lên 18. Không đổi tên/xoay/đối xứng một màn để tăng số lượng. Sau bổ sung fixture original, **inventory có đủ 18 JSON**, manifest khóa file/hash/nguồn/trạng thái và hồ sơ từng ID có witness hoặc phân tích tay cùng mức tin cậy. Kiểm dữ liệu không chứng minh engine hoặc khả giải của map adapted.

Nguồn **A** = AchrafMez, commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9`, MIT; **F** = FrankBuss/Damien Clarke, commit `775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562`, chỉ chọn trong phạm vi bài học phi thương mại và giữ notice. URL từng level, hash nguồn và quyết định loại ở [nhật ký nguồn](../references/README.md#nguồn-cho-danh-sách-18-map). Không lấy code game hoặc solver nguồn.

### Danh sách 4 + 14

Mỗi dòng tính đúng một nhóm chính, kể cả khi có cơ chế phụ. Difficulty dưới đây là **dự kiến**, chưa đo solver. 14 ID nâng cao đã có file `data/maps/prepared/<id>.json`, gồm 13 adapted và một original vô nghiệm. Bốn ID basic giữ đường dẫn hiện tại.

| Bộ | ID | Nguồn / level | Nhóm chính | Difficulty | Chuyển đổi và vai trò kiểm tra |
| --- | --- | --- | --- | --- | --- |
| 15 | `basic_01` | Original, ví dụ contract | Basic | easy | Giữ nguyên; hai bước, đứng vào goal |
| 15 | `basic_turn_01` | Matías `level_2_2`, MIT, nguồn cũ | Basic | easy | Giữ nguyên; đổi hướng, nằm qua goal chưa thắng |
| 15 | `basic_cycle_01` | Original, nguồn cũ | Basic | easy | Giữ nguyên; chu trình và nhánh phụ |
| 15 | `basic_unsolvable_01` | Original, nguồn cũ | Basic | easy | Giữ nguyên; goal cô lập, oracle ba state |
| 15 | `fragile_01` | A `levels/level3.txt` | Fragile | medium | Pad void cuối hàng; giữ fragile; witness nằm được đỡ/đứng rơi |
| 15 | `fragile_02` | A `levels/level7.txt` | Fragile | hard | Giữ các dải fragile và ô floor xen giữa; bố cục khác `level3`, kiểm bước rời fragile |
| 15 | `bridge_01` | F 14 `levelub` (210362) | Cầu | medium | Đổi x/y sang row/col; hai nhóm cầu ban đầu đóng, hai heavy toggle điều khiển riêng; kiểm cùng vị trí khác bridge bits |
| 15 | `soft_toggle_01` | A `levels/level4.txt` | Soft/toggle | medium | Giữ soft A→a, heavy 1→b và cả hai cầu; soft nhấn/rời/nhấn lại; không tính thêm vào nhóm heavy |
| +3 | `soft_toggle_02` | A `levels/level6.txt` | Soft/toggle | hard | Giữ A/B/C và ba nhóm cầu a/b/c; khác bài hai cầu, kiểm nhiều bridge bits độc lập |
| 15 | `heavy_01` | A `levels/level5.txt` | Heavy | medium | 0→a; giữ layout, witness nằm không nhấn và UPRIGHT nhấn |
| +3 | `heavy_02` | A `levels/level10.txt` | Heavy | hard | 0→a và fragile; kiểm trọng lượng công tắc cùng đường fragile, khác bài heavy đơn |
| 15 | `permanent_open_01` | F 18 `levelsc` (284933) | Permanent | hard | Giữ on/off/toggle; chọn soft [1,7] đặt mở [4,8],[4,9], nhấn lại vẫn mở; giữ các switch khác |
| 15 | `permanent_close_01` | F 11 `leveldw` (291709) | Permanent | medium | Cầu [0,6],[1,6] ban đầu mở; soft [6,8] đặt đóng, nhấn lại vẫn đóng |
| 15 | `split_merge_01` | F 8 `levelss` (499707) | Split/merge | medium | Split [4,4]→[[1,10],[7,10]], active_destination=0; tách, SWITCH và nhập theo cạnh |
| +3 | `split_merge_02` | F 9 `levelre` (074355) | Split/merge | hard | Split [4,13]→[[4,12],[4,2]], active_destination=0; sau sort active=1, đường nối khác `levelss` |
| 15 | `combined_01` | F 15 `levelht` (098598) | Kết hợp | hard | Giữ soft/heavy, toggle/off, cầu mở/đóng và split [5,7]→[[1,13],[8,1]]; kiểm khối nhỏ không nhấn heavy |
| 15 | `combined_02` | F 20 `leveltb` (543019) | Kết hợp | hard | Giữ soft toggle/off, cầu và split [4,7]→[[1,13],[7,13]]; khối nhỏ nhấn soft và giữ đè khi đổi điều khiển |
| 15 | `advanced_unsolvable_01` | Original, JSON và phân tích bên dưới | Vô nghiệm nâng cao | easy | Cầu luôn đóng và soft chỉ đặt đóng; chứng cứ bất biến cầu, khác goal cô lập basic |

### Kiểm độ phủ và bộ tối thiểu

| Nhóm chính | Bộ 15 | Bộ 18 | Phân biệt đã dành vai trò |
| --- | ---: | ---: | --- |
| Basic | 4 | 4 | Hai bước / đổi hướng / chu trình / vô nghiệm |
| Fragile | 2 | 2 | Hai bố cục, nằm được đỡ và đứng rơi |
| Cầu | 1 | 1 | Hai nhóm cầu đóng, mở/đóng độc lập và full bridge key |
| Soft/toggle | 1 | 2 | Nhấn mới/rời/nhấn lại; giữ đè bằng khối tách ở `combined_02` |
| Heavy | 1 | 2 | Nằm không nhấn / đứng nhấn; khối nhỏ không nhấn ở `combined_01` |
| Permanent | 2 | 2 | Đặt mở và đặt đóng, kích hoạt lại không đảo |
| Split/merge | 1 | 2 | Tách / SWITCH / nhập; ca đảo active nằm ở bộ +3 |
| Kết hợp | 2 | 2 | Cầu/công tắc cùng split, gồm tương tác khối nhỏ |
| Vô nghiệm nâng cao | 1 | 1 | Bất biến cầu luôn đóng, không dùng timeout làm chứng minh |
| **Tổng** | **15** | **18** | Mỗi ID chỉ tính một nhóm chính |

Đủ mọi loại ô và cơ chế trong đề mục 2.5/3.1 của đề bài và contract ở **mức dữ liệu và hồ sơ phân tích tay**. Không đồng nghĩa các witness hoặc engine đã đạt. Ba map +3 thêm tình huống khác biệt cụ thể; không cần thêm basic hoặc nhiều bản cùng một level chỉ để đủ 18.

### Kịch bản tham chiếu và xác minh tiếp theo

- `soft_toggle_01`: từ start [3,1], dự kiến `RIGHT, UP` tới H [[2,2],[2,3]] nhấn A; `RIGHT` rời A và `LEFT` nhấn lại. Phải đối chiếu bridge bits và trạng thái sau từng action bằng luật nhóm khi kiểm chứng map.
- Khối nguyên lăn rời các ô cũ, nên ca **giữ đè** dành cho khối SPLIT: trong `combined_02`, sau tách, SWITCH sang khối [7,13], `LEFT, UP` tới soft [6,12] (toggle cầu [6,10],[6,11]); SWITCH sang khối [1,13] rồi LEFT. Soft vẫn bị khối không active đè, không được toggle lần hai. Sau đó SWITCH, DOWN, UP để rời/nhấn lại. Đây là kịch bản sau tách dự kiến, còn phải ghi đường từ initial tới split và kiểm full key.
- `combined_01`: sau split, khối active ở [1,13], LEFT tới heavy [1,12] không được kích hoạt. Khối còn lại ở [8,1], SWITCH rồi RIGHT ×10, UP tới soft [7,11] phải đặt đóng cầu [8,9],[8,10]; khối nhỏ không thắng khi đi qua goal. Các chuỗi này phải được kiểm theo snapshot/bridge bits thực tế, không thay nghiệm thu bằng metadata.
- `permanent_open_01`/`permanent_close_01`: chỉ rõ switch và nhóm cầu trong bảng, thu lần nhấn đầu/lần nhấn lại, trạng thái trước/sau. `split_merge_01`/`02`: thu đủ tách, SWITCH, đổi active sau sort và nhập; không chỉ chụp đích teleport. Khác thứ tự xử lý của app nguồn được giải theo contract nhóm.
- 13 map adapted mới không có nhãn `expected_solvable`; không suy khả giải từ level được phát hành. Map original vô nghiệm có phân tích tay bên dưới cho nhãn kỳ vọng false; chỉ xác nhận engine sau duyệt cạn thật.

### Blueprint original cho khoảng trống vô nghiệm nâng cao

Khảo sát chưa tìm thấy nguồn ngoài có hồ sơ vô nghiệm nâng cao đủ căn cứ; các nguồn A/F chủ yếu là màn chơi không có chứng minh vô nghiệm theo luật nhóm. Chọn một fixture original nhỏ, không sửa goal/layout của màn tiếp nhận hoặc tạo biến thể từ map basic. Lý do tự tạo và nguồn đã loại được giữ ở [khảo sát nguồn](../references/advanced-map-source-survey.md#6-kết-luận-khảo-sát-và-khoảng-trống).

Blueprint 5 × 10, tọa độ từ 0. `.`=void, F=floor, S=floor+start, G=goal, b=bridge, s=soft:

```text
..........
.SFFbbFGF.
.FFs..FFF.
.FFF..FFF.
..........
```

Start [1,1], goal [1,7]; b01=[[1,4],[1,5]], initial_open=false; s01 tại [2,3], effect permanent, targets=[b01], open=false. Không fragile, heavy, split hoặc switch khác. `RIGHT, DOWN` dự kiến nhấn soft bằng khối nằm; cầu vẫn đóng.

**Lập luận tay:** b01 ban đầu false và mọi kích hoạt chỉ đặt false, nên luôn là void. Không có teleport. Tập ô đỡ có hai thành phần không nối cạnh: trái (hàng 1–3, cột 1–3) chứa start, phải (hàng 1–3, cột 6–8) chứa goal; mọi nước lăn hợp lệ từ bên trái vẫn ở bên trái. Goal không tới được. Đã hiện thực thành [advanced_unsolvable_01.json](prepared/advanced_unsolvable_01.json) và kiểm dữ liệu. [Hồ sơ bất biến và witness](../references/map-bundle-evidence.md#advanced_unsolvable_01) giữ mức tin cậy manual_invariant; engine/replay/solver đều chưa chạy.

### Loại trùng, dự phòng và bằng chứng kiểm tra

- Đã đọc lại raw ở commit ghim và chuẩn hóa 4 JSON cũ + 13 layout/metadata nguồn + blueprint original. Bỏ viền void/padding, chuẩn hóa tịnh tiến và cả 8 phép quay/đối xứng; so layout/start/goal, loại ô, trạng thái đầu cầu, liên kết và effect switch, đích split cùng khối active. ID/format/newline không dùng để quyết định khác map. **153 cặp của 18 ứng viên không trùng**; kiểm thêm hình học/start/goal khi bỏ phân biệt loại ô cũng không thấy cặp trùng. Đây là rà lựa chọn, không thay kiểm chống trùng JSON sau chuyển đổi.
- Loại các bản GBA cùng level với F: `ub`, `dw`, `sc`, `ss`, `re`, `ht`, `tb`; cả `kn`, `hg` dự phòng cũng trùng. Đã đối chiếu layout, spawn, switch effect và split destinations; không đếm thành nguồn map mới. Các basic A `level0`–`2` và ba ma trận Matías còn lại không chọn vì basic đã đủ.
- Không chọn F `levelpp` nguyên trạng (đích split trỏ vào split, trái yêu cầu floor); `leveltw`, `leveldd`, `levelmp`, `levelgv` có effect hỗn hợp trên cùng switch, không biểu diễn trực tiếp. Không bỏ effect để lách schema. Các nguồn thiếu quyền tiếp nhận rõ vẫn bị loại theo hồ sơ khảo sát.
- **Tối đa hai mở rộng, chưa tính vào 18:** `combined_03` từ F 24 `levelkn` (088198), hard, permanent mở + split; `combined_04` từ F 26 `levelhg` (426329), hard, soft đóng/heavy mở + split. Đã kiểm metadata/đích floor và khác 18 ứng viên. Chỉ triển khai sau bộ 18 đạt dữ liệu; không dùng để lấp một nhóm bắt buộc bị thiếu. Nếu cần thay ứng viên khi chuyển đổi phát hiện lỗi, giữ đúng nhóm và cập nhật lựa chọn, không cộng cả bản cũ lẫn bản thay.
- Không còn nhóm **chưa chọn ứng viên**; 13 map adapted đã chuyển và kiểm dữ liệu, xem [hash/trạng thái](#dữ-liệu-đã-chuyển-đổi). Fixture vô nghiệm nâng cao đã có; manifest khóa đủ 18 map và hồ sơ từng ID. Các snapshot cục bộ chưa chứng minh đường đi từ start, không thay bằng chứng engine.
- Kiểm tra lựa chọn dùng script tạm đọc literal bằng AST/JSON, không chạy code nguồn ngoài hoặc thêm converter/validator game vào repo. Hai notice khớp raw từng byte. Lệnh test và kết quả được ghi ở nhật ký nguồn.

AI hỗ trợ đối chiếu đề bài/contract, chọn map, rà trùng và viết blueprint/lập luận tay; chưa chạy game hoặc đo hiệu năng.

## Phần chờ nghiệm thu engine/replay

1. TV1 cung cấp đường import thật cho `load_map`, `initial_state`, `transition`, `state_key`, `is_goal`, `successors`, `step_cost`; loader chấp nhận đủ 4 map.
2. Replay các chuỗi trên, kiểm tra OK/WON, goal khi nằm, full key của chu trình và tổng step_cost; map/state đầu vào không bị sửa. Bộ này chỉ có floor/goal nên mỗi bước hợp lệ có cost 1.
3. Duyệt cạn fixture goal cô lập, xác nhận tập 3 state và không nhầm TIMEOUT với UNSOLVABLE.
4. Sau khi API solver hoàn chỉnh, kiểm tra 3 kết quả SOLVED và 1 UNSOLVABLE, rồi ghi ngày/commit/số test của lần nghiệm thu. GUI và benchmark dùng cùng dữ liệu sau đó.

Lượt chuẩn bị có AI hỗ trợ khảo sát nguồn, chuyển dữ liệu, viết test và tài liệu. Chưa chạy benchmark hoặc tạo số liệu hiệu năng; nhóm có thể dùng ghi nhận này khi tổng hợp phụ lục AI.

## Dữ liệu đã chuyển đổi

Ngày 17/10/2026, chuyển từng lô nhỏ, kiểm dữ liệu draft rồi mới đưa vào `prepared/`. Chỉ là kiểm tra schema/liên kết/đối chiếu nguồn; engine, replay và solver thật **chưa chạy**. Không dùng nhãn khả giải cho các map adapted mới. Bốn basic ở root giữ nguyên.

| Lô | ID / JSON | Nguồn | Kích thước | SHA256 byte | Dữ liệu | Engine | Replay/solver thật |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [`fragile_01`](prepared/fragile_01.json) | achraf `level3` | 9 × 17 | `f0c9f597865d873be0dfdb637b233e6f5864d173c0e6142cd1fa2d5910880065` | Đạt | Chưa chạy | Chưa chạy |
| 1 | [`fragile_02`](prepared/fragile_02.json) | achraf `level7` | 12 × 17 | `52a1d57f1ff29d43b9c192b394da1b4a34600c615faa289a5f57bd927af11c22` | Đạt | Chưa chạy | Chưa chạy |
| 1 | [`soft_toggle_01`](prepared/soft_toggle_01.json) | achraf `level4` | 6 × 17 | `2477fa5f52803460ff8312c48cb6e7cde0f9f450a35bc1c8b2edf5760cba8724` | Đạt | Chưa chạy | Chưa chạy |
| 2 | [`soft_toggle_02`](prepared/soft_toggle_02.json) | achraf `level6` | 10 × 17 | `6df8ab61461472229b9b67103b9a67023b596fdea2122549668c5855b7edae52` | Đạt | Chưa chạy | Chưa chạy |
| 2 | [`heavy_01`](prepared/heavy_01.json) | achraf `level5` | 9 × 17 | `ed524df786d5a45de4327eb547efd3bc1b82d27aaa5c486942cd0ec368f71301` | Đạt | Chưa chạy | Chưa chạy |
| 2 | [`heavy_02`](prepared/heavy_02.json) | achraf `level10` | 10 × 17 | `bf316e8d374073a2db4680b78fd4727b15a9c38ead94241c167ac10125dabae7` | Đạt | Chưa chạy | Chưa chạy |
| 3 | [`bridge_01`](prepared/bridge_01.json) | frank `levelub` | 10 × 15 | `5193bb461a7428daa4f80e75feaff6d81d77ad2357f0cf220d06f5cfa7d2f2d0` | Đạt | Chưa chạy | Chưa chạy |
| 3 | [`permanent_open_01`](prepared/permanent_open_01.json) | frank `levelsc` | 10 × 15 | `ec414b321005d459073f0c17e3e9d3aaa2ca33ced426a698bc72dd5e6745312d` | Đạt | Chưa chạy | Chưa chạy |
| 3 | [`permanent_close_01`](prepared/permanent_close_01.json) | frank `leveldw` | 10 × 15 | `061efc9ed735a294918e9fc7556cad82a2048d61fe22b415cbfb40cc3425ec47` | Đạt | Chưa chạy | Chưa chạy |
| 4 | [`split_merge_01`](prepared/split_merge_01.json) | frank `levelss` | 10 × 15 | `d32867d120508c26d643b8395f7aafcbe5d08441ce8b6c4a752875e0eb3fb0b2` | Đạt | Chưa chạy | Chưa chạy |
| 4 | [`split_merge_02`](prepared/split_merge_02.json) | frank `levelre` | 10 × 15 | `d3c32d97f35785bf096c7c2030bdd2acb807631e318b5dd3623b8dae98bc2304` | Đạt | Chưa chạy | Chưa chạy |
| 5 | [`combined_01`](prepared/combined_01.json) | frank `levelht` | 10 × 15 | `4be3878b39afcf4b0f6543cb6a19a1ab87a5a2205dfdeb85b0d364d73ff7152a` | Đạt | Chưa chạy | Chưa chạy |
| 5 | [`combined_02`](prepared/combined_02.json) | frank `leveltb` | 10 × 15 | `6b8db0b63676c886b8f0021a8d24dc4fe5f35058bf7e63b50a0939b569b69b41` | Đạt | Chưa chạy | Chưa chạy |

Đã đối chiếu dữ liệu **trước khi chuyển từng lô**: lô 1 gồm 3 map (đại diện `fragile_01` được kiểm trước), lô 2 gồm 3 map, lô 3 gồm 3 map (đại diện `bridge_01` được kiểm trước), lô 4 và 5 mỗi lô 2 map. Mỗi lần kiểm theo lô chạy **9/9 test chuyển đổi đạt**; sau cùng bổ sung kiểm toàn bộ ánh xạ Achraf, hash/catalog/notes/notice. Không giữ JSON draft chưa đạt trong inventory.

Kiểm tra cuối ngày 17/10/2026, Python 3.12.10, HEAD nền `19d13998cd3d477a9f7cd66e7bf4354d75e0b607`:

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

**115/115 test đạt, không skip**, gồm 11 test chuyển đổi mới và 104 test cũ (trong đó có 7 test bốn map basic). Kiểm tra mới bao gồm schema v1, integer/bool/tọa độ/ID, toàn bộ ô/liên kết cầu/công tắc, permanent/split, đối chiếu nguồn độc lập, source SHA256, notice nguyên byte, hash JSON/catalog, notes/link, input sai và CLI không ghi đè. Không chạy engine/GUI/replay/benchmark hoặc solver ngoài.

Bộ cuối đã bổ sung map vô nghiệm nâng cao và khóa manifest/độ phủ ở mục dưới; chưa thu witness qua engine. Không gắn kết quả tìm kiếm hoặc lời giải vào JSON. AI hỗ trợ chuyển dữ liệu, viết converter/test và tài liệu; không có số đo hiệu năng trong lượt chuẩn bị này.

## Bộ dữ liệu đã khóa

Ngày 17/10/2026, tại HEAD nền `c85494fcac8fa0836e914f0cc7d9f39a4565e78c`, giữ nguyên byte bốn basic và 13 bản chuyển đổi, bổ sung duy nhất fixture original. Tổng 18 map đủ chín nhóm chính theo bảng độ phủ; draft và bản trùng không được tính. [Manifest](../map_bundle.json) chứa đường dẫn từ repo root, source, notice, nhóm, difficulty dự kiến, SHA256, hồ sơ/mức tin cậy và trạng thái riêng từng map. Manifest nằm ngoài thư mục maps để GUI quét JSON root không nhầm thành màn chơi.

| ID / JSON | Nguồn | Kích thước | SHA256 byte | Dữ liệu | Engine | Replay/solver thật |
| --- | --- | --- | --- | --- | --- | --- |
| [`advanced_unsolvable_01`](prepared/advanced_unsolvable_01.json) | original, Team-created | 5 × 10 | `4694347ec1e0ef173df856b2f559df26ec59d963b25847475c5ce6d0682c9de9` | Đạt | Chưa chạy | Chưa chạy |

[Hồ sơ kiểm tra](../references/map-bundle-evidence.md) ghi nguồn đã xem/lý do tự tạo, witness hoặc phân tích theo từng ID và giới hạn reachability. Nhãn false của fixture mới dựa trên bất biến cầu luôn đóng, chưa phải kết quả solver. Chống trùng kiểm cả tám phép quay/đối xứng, tịnh tiến và padding, giữ hình học/start/goal kể cả khi bỏ khác biệt loại ô phụ.

```powershell
python -m unittest discover -s tests/solvers -p 'test_TV4_map_bundle.py' -v
python -m unittest discover -s tests/solvers -p 'test_TV4_*.py' -v
```

Kiểm tra bằng Python 3.12.10: **123/123 test thành phần đạt, không skip**, gồm 8 test bundle mới và 115 test hiện có. Giữ nguyên bảy test bốn map basic; dùng chung assertion schema mà vẫn yêu cầu đúng source adapted và không có nhãn khả giải cho 13 bản chuyển đổi. Không chạy engine, GUI, replay hoặc benchmark; dữ liệu đã khóa không đồng nghĩa luật nâng cao đã được nghiệm thu.
