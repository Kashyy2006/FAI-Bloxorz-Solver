# Bộ map cơ bản

**Phụ trách:** Thành viên 4, phối hợp thành viên 1 về schema/engine. Chuẩn bị ngày 15/10/2026 theo [schema v1](../../docs/contracts/map-format.md).

Bộ khởi tạo có 4 map dùng chung cho GUI và các solver. Chỉ có `floor`, `void`, `goal`; tất cả ở mức `easy`, `bridges=[]`, `switches=[]`. Đây chưa phải bộ benchmark cuối kỳ: còn cần map fragile, cầu/công tắc, split và nhiều mức khó.

**Trạng thái:** JSON và test dữ liệu đã được chuẩn bị. Lời giải, chu trình và tập trạng thái dưới đây là oracle đối chiếu từ contract/nguồn và rà luật bằng tay; **chưa được load/replay bằng engine thật**, vì repo chưa có loader/engine. Nhãn `expected_solvable` không phải kết quả solver và không được dùng để quyết định status.

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
python -m unittest discover -s tests/solvers -p 'test_*.py' -v
```

Test map kiểm tra danh mục, layout/start/goal, metadata và kiểu dữ liệu cơ bản, bản sao ví dụ contract, nguồn/ghi chú chuyển đổi/giấy phép và SHA256 dưới đây. Test dùng đường dẫn từ vị trí file, không phụ thuộc working directory. Không chấp nhận chạy 0 test làm bằng chứng đạt.

Đã chạy ngày 15/10/2026 với Python 3.12.10: **7/7 test dữ liệu đạt; tổng 31/31 test solver đạt** (11 BFS, 13 common, 7 map). Các test BFS hiện dùng đồ thị giả; kết quả này không bao gồm kiểm thử engine, replay hoặc benchmark.

Đây là test fixture cho bộ cơ bản, **không thay validator `load_map` của engine** và không chạy luật game. Chưa có kiểm thử engine bị skip để làm suite xanh.

## Phiên bản dữ liệu

Chuẩn bị trên code nền `b08210650ad836d47283806d35682ec92258322d`, Python 3.12.10. Hash SHA256 tính từ byte JSON ngày 15/10/2026:

| ID | SHA256 |
| --- | --- |
| `basic_01` | `40ded3e094a7ea81290c6c621da529eda59bfb6bacb9ef23d1b2afd253eec759` |
| `basic_turn_01` | `aad9c38aae3c630ac3e9d4f36cc1d8a91bf4440505e7082b94a0fda2b95bb2d3` |
| `basic_cycle_01` | `6054d54a00890ac32d90886e5125e4cd0d80b9312d72e1fd64c1b04c7428f82f` |
| `basic_unsolvable_01` | `4d515ea5ea56accfe9f4199fea96100eb8d2582df0c63187c81ca8170ab1b6ae` |

Hash khóa bản dữ liệu đã chuẩn bị; chưa tuyên bố bộ map đã nghiệm thu engine. Khi thay map, cập nhật hash và oracle liên quan, chạy lại kiểm tra trước khi thu số liệu. Mọi solver phải dùng cùng file/hash và trạng thái đầu; không gán kết quả của bản cũ cho bản mới.

## Phần chờ engine

1. TV1 cung cấp đường import thật cho `load_map`, `initial_state`, `transition`, `state_key`, `is_goal`, `successors`, `step_cost`; loader chấp nhận đủ 4 map.
2. Replay các chuỗi trên, kiểm tra OK/WON, goal khi nằm, full key của chu trình và tổng step_cost; map/state đầu vào không bị sửa. Bộ này chỉ có floor/goal nên mỗi bước hợp lệ có cost 1.
3. Duyệt cạn fixture goal cô lập, xác nhận tập 3 state và không nhầm TIMEOUT với UNSOLVABLE.
4. Sau khi API solver hoàn chỉnh, kiểm tra 3 kết quả SOLVED và 1 UNSOLVABLE, rồi ghi ngày/commit/số test của lần nghiệm thu. GUI và benchmark dùng cùng dữ liệu sau đó.

Lượt chuẩn bị có AI hỗ trợ khảo sát nguồn, chuyển dữ liệu, viết test và tài liệu. Chưa chạy benchmark hoặc tạo số liệu hiệu năng; nhóm có thể dùng ghi nhận này khi tổng hợp phụ lục AI.
