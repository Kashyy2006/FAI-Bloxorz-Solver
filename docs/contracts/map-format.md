# Định dạng map JSON

- Phiên bản 1.0. Thành viên 1 chốt schema/validator; thành viên 4 chuẩn bị map.

## 5. MAP JSON — schema_version = 1


### 5.1. Cấu trúc chung

- Các trường bắt buộc: schema_version, id, name, difficulty, rows, cols, grid, start, bridges, switches, source
- schema_version: số nguyên, hiện chỉ chấp nhận 1.
- id: chuỗi không rỗng; duy nhất trong bộ map.
- name: chuỗi không rỗng.
- difficulty: "easy", "medium" hoặc "hard"; tự gán để phân loại bộ thử.
- rows, cols: số nguyên dương.
- grid: mảng hai chiều hình chữ nhật, có đúng rows hàng và cols cột.
- Mỗi ô dùng đúng một mã: "void", "floor", "goal", "fragile", "soft", "heavy", "split", "bridge".
- Có đúng một ô "goal".
- start: một tọa độ [row, col] nằm trong map, trên ô "floor". Khối bắt đầu ở UPRIGHT.
- bridges, switches: bắt buộc có; dùng [] nếu không có.
- Tọa độ và số đếm phải là số nguyên; không chấp nhận số thực hoặc bool.
- JSON dùng mảng; khi nạp, engine chuyển dữ liệu cần thiết sang tuple. Map đã nạp được giữ cố định trong một lượt chơi/tìm kiếm.

### 5.2. Nhóm cầu


```json
"bridges": [
  {
    "id": "b01",
    "cells": [[2, 4], [2, 5]],
    "initial_open": false
  }
]
```

- id: chuỗi không rỗng, không trùng ID nhóm cầu khác.
- cells: danh sách không rỗng, không có tọa độ trùng.
- Mọi tọa độ phải nằm trong map và trỏ tới ô "bridge".
- Mỗi ô "bridge" trong grid phải thuộc đúng một nhóm cầu.
- initial_open: bool, xác định trạng thái cầu lúc bắt đầu.
- Engine sắp xếp ID nhóm cầu theo thứ tự từ điển, rồi dùng thứ tự đó cho State.bridges. Không phụ thuộc thứ tự khai báo trong JSON.

### 5.3. Công tắc

- Ví dụ dưới đây là các khai báo riêng; chỉ hợp lệ khi tọa độ khớp với grid của map nâng cao tương ứng:

```json
"switches": [
  {
    "id": "s01",
    "cell": [1, 3],
    "type": "soft",
    "effect": {
      "mode": "toggle",
      "targets": ["b01"]
    }
  },
  {
    "id": "s02",
    "cell": [3, 3],
    "type": "heavy",
    "effect": {
      "mode": "permanent",
      "targets": ["b01"],
      "open": true
    }
  },
  {
    "id": "s03",
    "cell": [4, 2],
    "type": "split",
    "destinations": [[1, 1], [4, 5]],
    "active_destination": 0
  }
]
```

- Quy định chung:
- ID công tắc là chuỗi không rỗng, không trùng nhau.
- cell phải nằm trong map; loại ô trong grid phải khớp type.
- Mỗi ô "soft", "heavy" hoặc "split" có đúng một khai báo tương ứng.
- Xử lý công tắc theo ID tăng dần bằng thứ tự từ điển.
- Với soft và heavy:
- Bắt buộc có effect; không có destinations hoặc active_destination.
- targets không rỗng, không chứa ID trùng và chỉ tham chiếu nhóm cầu tồn tại.
- "toggle" không có trường open.
- "permanent" bắt buộc có open kiểu bool.
- Nhiều công tắc được phép điều khiển cùng nhóm cầu.
- Với split:
- Không có effect.
- destinations có đúng hai tọa độ khác nhau, đều nằm trên "floor" và không kề nhau theo cạnh.
- active_destination bắt buộc là số nguyên 0 hoặc 1.
- Chỉ số này trỏ vào thứ tự destinations trong JSON. Sau khi sắp xếp cells, engine cập nhật active để vẫn điều khiển đúng khối đã chọn.

### 5.4. Nguồn map

- Map tự thiết kế:

```json
"source": {
  "kind": "original",
  "reference": "Team-created"
}
```

- Map chuyển đổi từ nguồn khác:

```json
"source": {
  "kind": "adapted",
  "reference": "URL hoặc tên tài liệu nguồn",
  "conversion_notes": "data/references/map_01.md"
}
```

- source bắt buộc.
- kind chỉ nhận "original" hoặc "adapted".
- reference là chuỗi không rỗng.
- Với "adapted", bắt buộc có conversion_notes, trỏ tới tài liệu mô tả phần đã chuyển đổi: tọa độ, cầu, công tắc hoặc khác biệt luật.

### 5.5. Map dùng để thử trường hợp không có lời giải

- Chốt dùng trường tùy chọn riêng:
- "expected_solvable": false
- true: bộ thử kỳ vọng có lời giải.
- false: bộ thử kỳ vọng không có lời giải.
- Không khai báo: chưa xác định.
- Trường này phục vụ kiểm thử, không được dùng để solver quyết định kết quả. Không dùng "unsolvable" trong difficulty.

### 5.6. Kiểm tra khi nạp

- load_map kiểm tra cấu trúc, kiểu dữ liệu, tọa độ, ID và toàn bộ liên kết cầu/công tắc trước khi chơi hoặc giải. Từ chối trường không được định nghĩa trong schema để phát hiện lỗi gõ tên.
- Lỗi phải chỉ rõ vị trí và nguyên nhân, ví dụ:
- grid[1]: cần 7 ô, nhận được 6.
- start: tọa độ [1, 4] phải nằm trên floor, hiện là goal.
- switches[0].effect.targets[0]: nhóm cầu "b99" không tồn tại.
- bridges[0].cells[1]: ô [2, 5] không phải bridge.
- Map hợp lệ không đồng nghĩa có lời giải. load_map xác nhận map đúng quy cách; việc tìm lời giải thuộc solver.

## Ví dụ map đầy đủ

- Map này có lời giải `RIGHT, RIGHT`, tổng chi phí 2.

```json
{
  "schema_version": 1,
  "id": "basic_01",
  "name": "Two rolls",
  "difficulty": "easy",
  "rows": 3,
  "cols": 7,
  "grid": [
    [
      "void",
      "void",
      "void",
      "void",
      "void",
      "void",
      "void"
    ],
    [
      "void",
      "floor",
      "floor",
      "floor",
      "goal",
      "void",
      "void"
    ],
    [
      "void",
      "void",
      "void",
      "void",
      "void",
      "void",
      "void"
    ]
  ],
  "start": [
    1,
    1
  ],
  "bridges": [],
  "switches": [],
  "source": {
    "kind": "original",
    "reference": "Team-created"
  },
  "expected_solvable": true
}
```

## Thứ tự ID

- So sánh ID theo thứ tự từ điển, có phân biệt hoa/thường. Nên dùng ID có số đệm như `b01`, `b02`, `s01` để dễ đọc. ID cầu và ID công tắc nằm trong hai không gian tên riêng.
