# Chuyển dữ liệu AchrafMez sang schema v1

Chuyển ngày 17/10/2026 từ [AchrafMez/bloxorz](https://github.com/AchrafMez/bloxorz/tree/898188ed31cf31d4ce4c39fec3e3846ed037eee9/levels), commit `898188ed31cf31d4ce4c39fec3e3846ed037eee9`. Giữ [notice MIT](AchrafMez-LICENSE.txt), Copyright 2026 AchrafMez. Bản text nguồn giữ nguyên byte trong [map_sources](map_sources/README.md).

Tọa độ là `[row,col]` từ 0. Giữ toàn bộ layout, start và goal, không quay/cắt/chỉnh ô. Giữ số hàng, chỉ pad **cuối hàng** bằng void đến chiều rộng lớn nhất. `.`/`-` → void, F/S → floor (S là start), T → goal, O → fragile; chữ thường → bridge ban đầu đóng. A–Z trừ mã đặc biệt F/S/T/O → soft; 0–9 → heavy. Soft nối chữ thường tương ứng; heavy 0→a, 1→b, ...; effect là toggle. Nhóm cầu có ID b01... theo chữ nguồn tăng dần, công tắc có ID s01... theo hàng/cột tăng dần. ID không mang luật xử lý của ứng dụng nguồn.

`level7.txt` kết thúc bằng hai newline: hàng rỗng cuối vẫn được giữ, pad thành 17 void, nên JSON có **12 × 17** ô. Điều này khớp việc [parser nguồn](https://github.com/AchrafMez/bloxorz/blob/898188ed31cf31d4ce4c39fec3e3846ed037eee9/src/map.c) tăng row cho mỗi lần fgets; không âm thầm bỏ hàng trống.

Chỉ chuyển dữ liệu, không tiếp nhận code game/solver. Giới hạn thời gian/số bước của ứng dụng nguồn không thuộc schema v1. Engine nhóm quyết định cạnh nhấn, trọng lượng, goal và kiểm hỗ trợ sau công tắc; khác thứ tự xử lý của nguồn được ghi ở [khảo sát nguồn](advanced-map-source-survey.md#2-ánh-xạ-achrafmez-và-ứng-viên). Không dùng app/solver nguồn làm oracle.

Các JSON trong `data/maps/prepared/` đạt kiểm tra dữ liệu cấu trúc/liên kết và đối chiếu text nguồn. Difficulty là dự kiến; bỏ `expected_solvable` vì chưa kiểm khả giải. Chưa chạy engine/replay hoặc đo solver. Hash byte đầu ra và tiến độ từng lô ở [catalog](../maps/README.md#dữ-liệu-đã-chuyển-đổi).

## Tái tạo và kiểm tra

Từ repo root, tái tạo một map vào thư mục trống để đối chiếu với JSON prepared:

```powershell
python data/references/convert_maps.py fragile_01 --output-dir "$env:TEMP/fai-map-check-achraf"
python -m unittest discover -s tests/solvers -p 'test_TV4_map_conversion.py' -v
```

Converter dùng thư viện chuẩn, không ghi đè file đã tồn tại. Khi tiếp nhận lần đầu, bỏ `--output-dir` để xuất vào `data/maps/drafts/`; test kiểm cả draft và prepared, từ chối cùng ID ở cả hai nơi. Kiểm xong mới đưa file vào `prepared`; không đặt map nâng cao trực tiếp ở root `data/maps/` khi engine/GUI chưa xác nhận.

## Chi tiết từng map

### `fragile_01` — `level3`

JSON: [`fragile_01.json`](../maps/prepared/fragile_01.json), 9 × 17, start=[5, 2], goal=[6, 7]; difficulty dự kiến `medium`. Nguồn: [`achraf_level3.txt`](map_sources/achraf_level3.txt), SHA256 `7a36a4589fc483222920db929c00d86f1f80ed69a4afe353e1842899b97024e8`.

Pad void cuối hàng (row: số ô thêm): `{}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| Không có | — | — |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| Không có | — | — |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `fragile_02` — `level7`

JSON: [`fragile_02.json`](../maps/prepared/fragile_02.json), 12 × 17, start=[4, 14], goal=[5, 9]; difficulty dự kiến `hard`. Nguồn: [`achraf_level7.txt`](map_sources/achraf_level7.txt), SHA256 `86e5db7b81ce39d4f6d3973e86a1b95d3190b1adc2f5c0e26cbb0dd4daf75293`.

Pad void cuối hàng (row: số ô thêm): `{11: 17}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| Không có | — | — |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| Không có | — | — |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `soft_toggle_01` — `level4`

JSON: [`soft_toggle_01.json`](../maps/prepared/soft_toggle_01.json), 6 × 17, start=[3, 1], goal=[1, 14]; difficulty dự kiến `medium`. Nguồn: [`achraf_level4.txt`](map_sources/achraf_level4.txt), SHA256 `75687be941975108e25639cf906cba6a4f3adfc8ec3deaeaf1ed0228dcef8dad`.

Pad void cuối hàng (row: số ô thêm): `{}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[3, 5], [3, 6]]` | `false` |
| `b02` | `[[4, 11], [4, 12]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[1, 9]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b02"]}}` |
| `s02` | `[2, 3]` / soft | `{"effect": {"mode": "toggle", "targets": ["b01"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `soft_toggle_02` — `level6`

JSON: [`soft_toggle_02.json`](../maps/prepared/soft_toggle_02.json), 10 × 17, start=[0, 2], goal=[6, 2]; difficulty dự kiến `hard`. Nguồn: [`achraf_level6.txt`](map_sources/achraf_level6.txt), SHA256 `80a936bcd644fc1fe389d419c004f57e6a7452e758a87d3d094ad57fdf367413`.

Pad void cuối hàng (row: số ô thêm): `{}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[5, 8], [5, 9]]` | `false` |
| `b02` | `[[8, 5]]` | `false` |
| `b03` | `[[8, 4]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[0, 11]` / soft | `{"effect": {"mode": "toggle", "targets": ["b01"]}}` |
| `s02` | `[5, 11]` / soft | `{"effect": {"mode": "toggle", "targets": ["b02"]}}` |
| `s03` | `[9, 11]` / soft | `{"effect": {"mode": "toggle", "targets": ["b03"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `heavy_01` — `level5`

JSON: [`heavy_01.json`](../maps/prepared/heavy_01.json), 9 × 17, start=[4, 2], goal=[3, 14]; difficulty dự kiến `medium`. Nguồn: [`achraf_level5.txt`](map_sources/achraf_level5.txt), SHA256 `f896dfc1ecbee5c17348b90144800c051c469d4307f0a8efa0a3cf0e8a207414`.

Pad void cuối hàng (row: số ô thêm): `{}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[6, 4]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[4, 10]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b01"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `heavy_02` — `level10`

JSON: [`heavy_02.json`](../maps/prepared/heavy_02.json), 10 × 17, start=[1, 2], goal=[6, 2]; difficulty dự kiến `hard`. Nguồn: [`achraf_level10.txt`](map_sources/achraf_level10.txt), SHA256 `de6d0f5542ef8c06990ca8518d92fd28f49e7846d7797ec463fc9ab71918d38d`.

Pad void cuối hàng (row: số ô thêm): `{}`. Không sửa ô có sẵn.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[9, 8]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[5, 13]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b01"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.
