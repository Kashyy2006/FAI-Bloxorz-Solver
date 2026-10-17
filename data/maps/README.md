# Bộ map cơ bản

**Phụ trách:** Thành viên 4, phối hợp thành viên 1 về schema/engine. Chuẩn bị ngày 15/10/2026 theo [schema v1](../../docs/contracts/map-format.md).

Bộ khởi tạo có 4 map dùng chung cho GUI và các solver. Chỉ có `floor`, `void`, `goal`; tất cả ở mức `easy`, `bridges=[]`, `switches=[]`. Đây chưa phải bộ benchmark cuối kỳ: còn cần map fragile, cầu/công tắc, split và nhiều mức khó.

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

**Chốt ngày 17/10/2026, tại HEAD nền `53623791166261f234ceeae5b05c463ded9c397e`.** Chọn **18 map = 4 map hiện có + 13 map sẽ chuyển từ nguồn ngoài + 1 map original bù vô nghiệm nâng cao**. Bộ tối thiểu là 15 dòng đánh dấu **15**; ba dòng **+3** nâng lên 18. Không đổi tên/xoay/đối xứng một màn để tăng số lượng. **Inventory dữ liệu thực tế vẫn chỉ có bốn JSON basic**; các map mới còn phải chuyển đổi, bổ sung witness, hash JSON và kiểm tra dữ liệu.

Nguồn **A** = AchrafMez, commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9`, MIT; **F** = FrankBuss/Damien Clarke, commit `775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562`, chỉ chọn trong phạm vi bài học phi thương mại và giữ notice. URL từng level, hash nguồn và quyết định loại ở [nhật ký nguồn](../references/README.md#nguồn-cho-danh-sách-18-map). Không lấy code game hoặc solver nguồn.

### Danh sách 4 + 14

Mỗi dòng tính đúng một nhóm chính, kể cả khi có cơ chế phụ. Difficulty dưới đây là **dự kiến**, chưa đo solver. ID mới là tên file dự kiến `data/maps/prepared/<id>.json`, chưa phải file tồn tại; bốn ID basic giữ đường dẫn hiện tại.

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
| 15 | `advanced_unsolvable_01` | Original, blueprint bên dưới | Vô nghiệm nâng cao | easy | Cầu luôn đóng và soft chỉ đặt đóng; chứng cứ bất biến cầu, khác goal cô lập basic |

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

Đủ mọi loại ô và cơ chế trong đề mục 2.5/3.1 của đề bài, contract và phân công 19/10 ở **mức kế hoạch chọn map**. Không đồng nghĩa các witness hoặc engine đã đạt. Ba map +3 thêm tình huống khác biệt cụ thể; không cần thêm basic hoặc nhiều bản cùng một level chỉ để đủ 18.

### Witness phải thu khi chuyển đổi

- `soft_toggle_01`: từ start [3,1], dự kiến `RIGHT, UP` tới H [[2,2],[2,3]] nhấn A; `RIGHT` rời A và `LEFT` nhấn lại. Phải đối chiếu bridge bits và trạng thái sau từng action bằng luật nhóm khi kiểm chứng map.
- Khối nguyên lăn rời các ô cũ, nên ca **giữ đè** dành cho khối SPLIT: trong `combined_02`, sau tách, SWITCH sang khối [7,13], `LEFT, UP` tới soft [6,12] (toggle cầu [6,10],[6,11]); SWITCH sang khối [1,13] rồi LEFT. Soft vẫn bị khối không active đè, không được toggle lần hai. Sau đó SWITCH, DOWN, UP để rời/nhấn lại. Đây là kịch bản sau tách dự kiến, còn phải ghi đường từ initial tới split và kiểm full key.
- `combined_01`: sau split, khối active ở [1,13], LEFT tới heavy [1,12] không được kích hoạt. Khối còn lại ở [8,1], SWITCH rồi RIGHT ×10, UP tới soft [7,11] phải đặt đóng cầu [8,9],[8,10]; khối nhỏ không thắng khi đi qua goal. Các chuỗi này phải được kiểm theo snapshot/bridge bits thực tế, không thay nghiệm thu bằng metadata.
- `permanent_open_01`/`permanent_close_01`: chỉ rõ switch và nhóm cầu trong bảng, thu lần nhấn đầu/lần nhấn lại, trạng thái trước/sau. `split_merge_01`/`02`: thu đủ tách, SWITCH, đổi active sau sort và nhập; không chỉ chụp đích teleport. Khác thứ tự xử lý của app nguồn được giải theo contract nhóm.
- Toàn bộ map mới chưa có nhãn `expected_solvable`; không suy khả giải từ level được phát hành. Riêng map vô nghiệm có phân tích tay bên dưới để dự kiến false khi triển khai; chỉ xác nhận engine sau duyệt cạn thật.

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

**Lập luận tay:** b01 ban đầu false và mọi kích hoạt chỉ đặt false, nên luôn là void. Không có teleport. Tập ô đỡ có hai thành phần không nối cạnh: trái (hàng 1–3, cột 1–3) chứa start, phải (hàng 1–3, cột 6–8) chứa goal; mọi nước lăn hợp lệ từ bên trái vẫn ở bên trái. Goal không tới được. Đây là kỳ vọng theo blueprint và contract, chưa phải JSON đạt kiểm tra hoặc chứng minh bằng engine. Bốn trạng thái dữ liệu/engine/replay/solver của map này đều chưa kiểm.

### Loại trùng, dự phòng và bằng chứng kiểm tra

- Đã đọc lại raw ở commit ghim và chuẩn hóa 4 JSON cũ + 13 layout/metadata nguồn + blueprint original. Bỏ viền void/padding, chuẩn hóa tịnh tiến và cả 8 phép quay/đối xứng; so layout/start/goal, loại ô, trạng thái đầu cầu, liên kết và effect switch, đích split cùng khối active. ID/format/newline không dùng để quyết định khác map. **153 cặp của 18 ứng viên không trùng**; kiểm thêm hình học/start/goal khi bỏ phân biệt loại ô cũng không thấy cặp trùng. Đây là rà lựa chọn, không thay kiểm chống trùng JSON sau chuyển đổi.
- Loại các bản GBA cùng level với F: `ub`, `dw`, `sc`, `ss`, `re`, `ht`, `tb`; cả `kn`, `hg` dự phòng cũng trùng. Đã đối chiếu layout, spawn, switch effect và split destinations; không đếm thành nguồn map mới. Các basic A `level0`–`2` và ba ma trận Matías còn lại không chọn vì basic đã đủ.
- Không chọn F `levelpp` nguyên trạng (đích split trỏ vào split, trái yêu cầu floor); `leveltw`, `leveldd`, `levelmp`, `levelgv` có effect hỗn hợp trên cùng switch, không biểu diễn trực tiếp. Không bỏ effect để lách schema. Các nguồn thiếu quyền tiếp nhận rõ vẫn bị loại theo hồ sơ khảo sát.
- **Tối đa hai mở rộng, chưa tính vào 18:** `combined_03` từ F 24 `levelkn` (088198), hard, permanent mở + split; `combined_04` từ F 26 `levelhg` (426329), hard, soft đóng/heavy mở + split. Đã kiểm metadata/đích floor và khác 18 ứng viên. Chỉ triển khai sau bộ 18 đạt dữ liệu; không dùng để lấp một nhóm bắt buộc bị thiếu. Nếu cần thay ứng viên khi chuyển đổi phát hiện lỗi, giữ đúng nhóm và cập nhật lựa chọn, không cộng cả bản cũ lẫn bản thay.
- Không còn nhóm **chưa chọn ứng viên**; còn phải tạo fixture vô nghiệm, chuyển 13 map, thu witness, hash và kiểm tra dữ liệu. Không tuyên bố đã có 15/18 map bàn giao.
- Kiểm tra lựa chọn dùng script tạm đọc literal bằng AST/JSON, không chạy code nguồn ngoài hoặc thêm converter/validator game vào repo. Hai notice khớp raw từng byte. Lệnh test và kết quả được ghi ở nhật ký nguồn.

AI hỗ trợ đối chiếu đề bài/contract, chọn map, rà trùng và viết blueprint/lập luận tay; chưa chạy game hoặc đo hiệu năng.

## Phần chờ nghiệm thu engine/replay

1. TV1 cung cấp đường import thật cho `load_map`, `initial_state`, `transition`, `state_key`, `is_goal`, `successors`, `step_cost`; loader chấp nhận đủ 4 map.
2. Replay các chuỗi trên, kiểm tra OK/WON, goal khi nằm, full key của chu trình và tổng step_cost; map/state đầu vào không bị sửa. Bộ này chỉ có floor/goal nên mỗi bước hợp lệ có cost 1.
3. Duyệt cạn fixture goal cô lập, xác nhận tập 3 state và không nhầm TIMEOUT với UNSOLVABLE.
4. Sau khi API solver hoàn chỉnh, kiểm tra 3 kết quả SOLVED và 1 UNSOLVABLE, rồi ghi ngày/commit/số test của lần nghiệm thu. GUI và benchmark dùng cùng dữ liệu sau đó.

Lượt chuẩn bị có AI hỗ trợ khảo sát nguồn, chuyển dữ liệu, viết test và tài liệu. Chưa chạy benchmark hoặc tạo số liệu hiệu năng; nhóm có thể dùng ghi nhận này khi tổng hợp phụ lục AI.
