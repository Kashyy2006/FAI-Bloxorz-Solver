# Chuyển dữ liệu Frank Buss / Damien Clarke sang schema v1

Chuyển ngày 17/10/2026 từ [Vide/levels.py](https://github.com/FrankBuss/bloxorz/blob/775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562/Vide/levels.py), commit `775d5fa64d77b5d1793ef9e5e3bc9cce56ed5562`. Credit **Frank Buss và Damien Clarke** theo [notice nguyên bản](FrankBuss-license.txt). Dữ liệu chỉ được chọn trong phạm vi bài học **phi thương mại**; không ghi nguồn này là MIT thuần. Nếu đổi phạm vi sử dụng, phải rà quyền hoặc thay dữ liệu. Notice nguồn không phải giấy phép toàn dự án.

Lưu bảy đoạn khai báo dữ liệu nguyên thứ tự trong [frank_selected.txt](map_sources/frank_selected.txt), truy xuất/hash và cách trích ở [map_sources](map_sources/README.md). Chỉ đọc AST và `ast.literal_eval`, không import/exec/eval code nguồn. Đã đối chiếu với bản text chưa xoay `Vide/bloxorzlevels.txt`; không dùng dữ liệu C đã xoay.

Giữ grid **10 hàng × 15 cột**, đổi tọa độ `[x,y]` → `[row,col]=[y,x]`, không quay/cắt/chỉnh layout. Space/b/e/f → void/floor/goal/fragile; s/h/v → soft/heavy/split; l/r/k/q → bridge, k/q mở ban đầu còn l/r đóng. Công tắc được nhận diện từ tọa độ thật trong grid bằng `swatch{x}{y}`, không cắt chuỗi số theo độ dài cố định.

Mỗi nhóm cầu có chung trạng thái ban đầu **và toàn bộ tác động từ từng công tắc**. Không gộp theo vị trí kề nhau hoặc chỉ theo ký tự nguồn. b01... theo ô đầu tiên của nhóm khi duyệt hàng/cột; s01... theo tọa độ công tắc tăng dần. `onoff` → toggle; `on`/`off` → permanent với open=true/false. Giữ mọi target/effect. Converter từ chối effect hỗn hợp trên cùng công tắc, không bỏ tác động để khớp schema.

Split `[x1,y1,x2,y2]` → `[[y1,x1],[y2,x2]]`, giữ thứ tự, `active_destination=0` tương ứng SPLIT1 được điều khiển trước. Engine phải cập nhật active sau sort; `split_merge_02` chọn [4,12], nên khi cells sort thành [[4,2],[4,12]], active phải là 1. Không đổi destinations để che ca này. Đích phải là floor, khác nhau và không kề cạnh.

Nguồn xử lý merge trước một số kiểm tile/switch, còn contract nhóm xác định cạnh nhấn trước teleport/merge. Chỉ tiếp nhận dữ liệu, không lấy lời giải hay hành vi app nguồn làm bằng chứng theo luật nhóm. Xem [khác luật](advanced-map-source-survey.md#3-ánh-xạ-frankbuss-và-sàng-lọc-theo-level).

Các file `prepared` đạt kiểm tra dữ liệu, **chưa xác nhận engine/replay/solver**. Difficulty là dự kiến; không gắn `expected_solvable`. Chuỗi trong catalog là kịch bản cần kiểm sau này, không phải kết quả chạy. Hash byte đầu ra và các lô ở [catalog](../maps/README.md#dữ-liệu-đã-chuyển-đổi).

## Tái tạo và kiểm tra

```powershell
python data/references/convert_maps.py bridge_01 --output-dir "$env:TEMP/fai-map-check-frank"
python -m unittest discover -s tests/solvers -p 'test_TV4_map_conversion.py' -v
```

Chạy từ repo root, chọn thư mục đầu ra trống để tái tạo và đối chiếu JSON prepared; converter từ chối ghi đè. Khi tiếp nhận lần đầu, bỏ `--output-dir` để xuất draft. Test kiểm draft/prepared và từ chối ID xuất hiện ở cả hai nơi. Kiểm dữ liệu trước khi chuyển vào `prepared`; chưa đưa vào menu game.

## Chi tiết từng map

### `bridge_01` — `levelub`

JSON: [`bridge_01.json`](../maps/bridge_01.json), 10 × 15, start=[2, 4], goal=[8, 3]; difficulty dự kiến `medium`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[2, 1], [2, 2]]` | `false` |
| `b02` | `[[3, 1], [3, 2]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[3, 12]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b01"]}}` |
| `s02` | `[9, 13]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b02"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `permanent_open_01` — `levelsc`

JSON: [`permanent_open_01.json`](../maps/permanent_open_01.json), 10 × 15, start=[4, 2], goal=[8, 12]; difficulty dự kiến `hard`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[4, 8], [4, 9]]` | `false` |
| `b02` | `[[4, 12], [4, 13], [9, 1], [9, 2]]` | `false` |
| `b03` | `[[5, 5]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[1, 7]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": true}}` |
| `s02` | `[2, 2]` / soft | `{"effect": {"mode": "permanent", "targets": ["b02"], "open": false}}` |
| `s03` | `[4, 1]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": false}}` |
| `s04` | `[6, 2]` / soft | `{"effect": {"mode": "permanent", "targets": ["b02"], "open": false}}` |
| `s05` | `[7, 8]` / soft | `{"effect": {"mode": "permanent", "targets": ["b02"], "open": true}}` |
| `s06` | `[9, 3]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b03"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `permanent_close_01` — `leveldw`

JSON: [`permanent_close_01.json`](../maps/permanent_close_01.json), 10 × 15, start=[5, 2], goal=[1, 4]; difficulty dự kiến `medium`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[0, 6], [1, 6]]` | `true` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[6, 8]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": false}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `split_merge_01` — `levelss`

JSON: [`split_merge_01.json`](../maps/split_merge_01.json), 10 × 15, start=[4, 1], goal=[4, 13]; difficulty dự kiến `medium`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| Không có | — | — |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[4, 4]` / split | `{"destinations": [[1, 10], [7, 10]], "active_destination": 0}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `split_merge_02` — `levelre`

JSON: [`split_merge_02.json`](../maps/split_merge_02.json), 10 × 15, start=[4, 1], goal=[6, 7]; difficulty dự kiến `hard`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| Không có | — | — |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[4, 13]` / split | `{"destinations": [[4, 12], [4, 2]], "active_destination": 0}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `combined_01` — `levelht`

JSON: [`combined_01.json`](../maps/combined_01.json), 10 × 15, start=[8, 1], goal=[8, 12]; difficulty dự kiến `hard`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[1, 5], [1, 6]]` | `true` |
| `b02` | `[[1, 10], [1, 11]]` | `false` |
| `b03` | `[[2, 2], [2, 3]]` | `false` |
| `b04` | `[[8, 9], [8, 10]]` | `true` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[1, 12]` / heavy | `{"effect": {"mode": "toggle", "targets": ["b01", "b03"]}}` |
| `s02` | `[3, 8]` / soft | `{"effect": {"mode": "toggle", "targets": ["b01", "b02"]}}` |
| `s03` | `[5, 7]` / split | `{"destinations": [[1, 13], [8, 1]], "active_destination": 0}` |
| `s04` | `[7, 11]` / soft | `{"effect": {"mode": "permanent", "targets": ["b04"], "open": false}}` |
| `s05` | `[9, 11]` / soft | `{"effect": {"mode": "permanent", "targets": ["b04"], "open": false}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.

### `combined_02` — `leveltb`

JSON: [`combined_02.json`](../maps/combined_02.json), 10 × 15, start=[2, 8], goal=[8, 13]; difficulty dự kiến `hard`. Nguồn: [`frank_selected.txt`](map_sources/frank_selected.txt), SHA256 `9fb8af459e8d694ea2f725bd6162f4403a4ef1d0ca9c52667fd88fc53f510cb0`.

| Cầu | Ô [row,col] | Mở ban đầu |
| --- | --- | --- |
| `b01` | `[[1, 5], [1, 6]]` | `true` |
| `b02` | `[[1, 10], [1, 11]]` | `false` |
| `b03` | `[[6, 10], [6, 11]]` | `false` |

| Công tắc | Vị trí / loại | Tác động hoặc đích tách |
| --- | --- | --- |
| `s01` | `[2, 7]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": false}}` |
| `s02` | `[4, 3]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": false}}` |
| `s03` | `[4, 7]` / split | `{"destinations": [[1, 13], [7, 13]], "active_destination": 0}` |
| `s04` | `[4, 9]` / soft | `{"effect": {"mode": "permanent", "targets": ["b01"], "open": false}}` |
| `s05` | `[6, 12]` / soft | `{"effect": {"mode": "toggle", "targets": ["b03"]}}` |
| `s06` | `[7, 1]` / soft | `{"effect": {"mode": "toggle", "targets": ["b02"]}}` |

Mức bằng chứng: dữ liệu đạt kiểm tra; chưa xác nhận luật/khả giải/replay bằng engine.
