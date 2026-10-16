# Chuyển đổi map đổi hướng

Ngày chuyển đổi: **15/10/2026**. Map đích: [basic_turn_01.json](../maps/basic_turn_01.json). Người phụ trách dữ liệu: TV4.

## Định danh nguồn

- Tác giả: Matías, tài khoản GitHub `matuneville`.
- Repo: `matuneville/bloxorz-pathfinding`.
- Commit: `6af854a88ac3983ffed2ee12a9e26c4cc338aa76`.
- File gốc: https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/bloxorz-solver/tests/levels_testing.rs
- Chỉ tiếp nhận ma trận của test **`level_2_2`** và kỳ vọng độ dài 7; không lấy hàm giải/đồ thị của nguồn.
- Giấy phép MIT: [notice nguyên gốc](matuneville-LICENSE.txt), Copyright (c) 2023 Matías. [File giấy phép nguồn](https://github.com/matuneville/bloxorz-pathfinding/blob/6af854a88ac3983ffed2ee12a9e26c4cc338aa76/LICENSE).

SHA256 byte file test gốc: `2cf75d1a268d1694bf73fa0227ff162974ccafb31ccdd4d9527e59616c822aef` (2279 byte). SHA256 byte giấy phép đã lưu: `974a383c1d72bcc03ad9a197d4357f0e59dc5347d60a29a59d7d3793e04ae42e` (1064 byte). Không lưu toàn bộ code test/solver ngoài repo; ma trận dưới đây đủ đối chiếu dữ liệu đã tiếp nhận.

## Ma trận gốc và ánh xạ

```json
[
  [0, 1, 2, 1],
  [0, 1, 1, 1],
  [1, 1, 1, 3],
  [1, 1, 1, 0]
]
```

| Nguồn | Schema nhóm |
| --- | --- |
| Giá trị 0 | `void` |
| Giá trị 1 | `floor` |
| Giá trị 2 tại [0,2] | `floor`, đồng thời đặt `start=[0,2]` |
| Giá trị 3 tại [2,3] | `goal` |

Giữ chỉ số từ 0, hàng/cột theo thứ tự ma trận; không đổi trục, quay, cắt hay thêm viền. Rows=4, cols=4. Không thay bất kỳ ô nào ngoài ánh xạ ký hiệu. Ma trận không có fragile, cầu, công tắc hoặc split; thêm danh sách bridges/switches rỗng theo schema nhóm. Khối bắt đầu UPRIGHT trên floor; chỉ UPRIGHT trên goal mới thắng theo contract nhóm.

Thêm metadata schema_version=1, ID/name, difficulty=easy, expected_solvable=true và source adapted. Difficulty là phân loại nội bộ cho fixture nhỏ, không phải xếp hạng từ nguồn. Expected_solvable là kỳ vọng; nguồn có test đặt độ dài 7 nhưng lượt này không chạy test/solver của nguồn hoặc engine nhóm.

## Chứng cứ đề xuất để nghiệm thu

Chuỗi rà bằng bảng luật: `DOWN, RIGHT, UP, LEFT, DOWN, DOWN, RIGHT` (7 bước). Sau hai bước đầu, khối VERTICAL ở [[1,3],[2,3]], có chiếm goal nhưng chưa thắng. Bước cuối đứng tại [2,3]. Bảng trạng thái từng bước và phần chờ engine ở [danh mục map](../maps/README.md).

Test dữ liệu đối chiếu lại ma trận trong ghi chú này với grid/start trong JSON để phát hiện sai chuyển đổi. Test đó không thực hiện di chuyển; chỉ báo nghiệm thu lời giải sau khi replay bằng `transition` thật và đối chiếu `step_cost` của engine nhóm.
