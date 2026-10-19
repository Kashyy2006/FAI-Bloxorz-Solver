# Hồ sơ kiểm tra bộ 18 map

Khóa dữ liệu ngày **17/10/2026**, theo [schema map](../../docs/contracts/map-format.md) và [luật engine](../../docs/contracts/engine.md). [Manifest](../map_bundle.json) là inventory tường minh: đường dẫn tính từ repo root, SHA256 byte, nhóm chính, nguồn, notice, mức tin cậy và trạng thái từng map. Bốn basic giữ nguyên byte; 14 map nâng cao nằm trong `prepared/`. Draft không được tính. Không dùng glob root để đại diện toàn bộ bộ dữ liệu.

`data=passed` chỉ xác nhận cấu trúc/liên kết/nguồn/hash. `engine`, `replay`, `solver` đều `not_run`: đây là tình trạng bằng chứng của bộ dữ liệu, không phải status kết quả solver. Difficulty là dự kiến. Chỉ bốn basic và fixture vô nghiệm có `expected_solvable`; nhãn không thay cho việc tìm kiếm.

Mức tin cậy: `manual_reference` = chuỗi/bảng tham chiếu đã ghi trong catalog; `manual_local` = phân tích metadata hoặc bước cục bộ theo contract; `manual_invariant` = lập luận bất biến vô nghiệm. Các mức này **chưa xác nhận bằng engine**. Snapshot cục bộ có thể mô tả vị trí chưa chứng minh đạt được từ start; không được dùng làm lời giải toàn màn. Các test chỉ kiểm dữ liệu, không cài lại luật cầu/split hoặc validator ngữ nghĩa.

Tọa độ `[row,col]` từ 0; U/H/V là UPRIGHT/HORIZONTAL/VERTICAL. Khối nguyên có active=null; bridge bits theo ID tăng dần. Các chuỗi độc lập bắt đầu lại tại điểm được nêu; dừng sau WON/LOST.

## Phần cơ bản

<a id="basic_01"></a>
### `basic_01`

Nhóm basic, original từ ví dụ contract. `manual_reference`: từ start U [1,1], RIGHT → H [[1,2],[1,3]], RIGHT → U [1,4] trên goal; kỳ vọng WON, length/cost=2. Mục đích: hai lần lăn và goal khi đứng. Oracle chi tiết trong [catalog](../maps/README.md#hai-bước-lăn); hash phải khớp manifest và catalog.

<a id="basic_turn_01"></a>
### `basic_turn_01`

Nhóm basic, adapted từ Matías `level_2_2`, giữ [ghi chú chuyển đổi và MIT](basic_turn_01.md). `manual_reference`: từ [0,2], DOWN, RIGHT tới V [[1,3],[2,3]], nằm qua goal [2,3] nhưng chưa thắng. Chuỗi đầy đủ DOWN, RIGHT, UP, LEFT, DOWN, DOWN, RIGHT dự kiến WON sau 7 bước. Nguồn cũng có kỳ vọng length 7; chưa chạy solver nguồn hoặc engine nhóm. Mục đích: đổi hướng và phân biệt chiếm goal với thắng.

<a id="basic_cycle_01"></a>
### `basic_cycle_01`

Nhóm basic, original. `manual_reference`: RIGHT ×4, DOWN ×2 từ U [1,1] dự kiến thắng tại [4,7], chưa khẳng định tối ưu. Chu trình riêng RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, UP, UP phải về full key ban đầu; DOWN, DOWN là nhánh phụ tới U [4,1]. Mục đích: chu trình và nhánh khác đường giải; [catalog](../maps/README.md#chu-trình-và-nhánh-phụ) giữ các mốc.

<a id="basic_unsolvable_01"></a>
### `basic_unsolvable_01`

Nhóm basic, original. `manual_invariant`: hành lang chỉ cho ba state U [1,1], H [[1,2],[1,3]], U [1,4]; bảng bốn hướng trong [catalog](../maps/README.md#goal-cô-lập) không đưa tới goal [1,7]. Kỳ vọng false là phân tích tay, chưa có duyệt cạn engine. Mục đích: phân biệt vô nghiệm với timeout.

## Fragile, cầu và công tắc

Sáu map Achraf giữ [ma trận và chuyển đổi](achraf-map-conversion.md), [MIT](AchrafMez-LICENSE.txt); bảy map Frank giữ [chuyển đổi toàn bộ hiệu ứng](frank-map-conversion.md), [notice riêng](FrankBuss-license.txt), chỉ trong phạm vi bài học phi thương mại. Tất cả map adapted mới bỏ nhãn khả giải.

<a id="fragile_01"></a>
### `fragile_01`

Nhóm fragile, Achraf `level3`. `manual_local`: snapshot H [[5,8],[5,9]] trên floor, RIGHT → U [5,10] là fragile, dự kiến LOST. Snapshot H [[5,11],[5,12]] nằm hoàn toàn trên fragile được đỡ; DOWN → H [[6,11],[6,12]] vẫn được đỡ. Mục đích: trọng lượng khi đứng khác khi nằm. Hai snapshot là ca cục bộ, chưa chứng minh đường từ start [5,2] tới đó.

<a id="fragile_02"></a>
### `fragile_02`

Nhóm fragile, Achraf `level7`. `manual_local`: snapshot H [[8,9],[8,10]] gồm floor+fragile; RIGHT → U [8,11] fragile, dự kiến LOST. Snapshot H [[8,7],[8,8]] trên fragile, LEFT → U [8,6] floor, dự kiến OK. Khác map trước ở dải fragile xen floor, kiểm bước rời fragile. Chưa chứng minh reachability của snapshot; hàng cuối toàn void được giữ theo parser nguồn.

<a id="bridge_01"></a>
### `bridge_01`

Nhóm cầu, Frank `levelub`. `manual_local`: b01=[[2,1],[2,2]], b02=[[3,1],[3,2]], đầu `(false,false)`; s01 heavy [3,12] chỉ đảo b01, s02 heavy [9,13] chỉ đảo b02. Với snapshot U [2,0], RIGHT đi tới H [[2,1],[2,2]]: cầu b01 đóng dự kiến LOST, mở dự kiến OK. Đây là hai snapshot cục bộ có bridge bits khác nhau, không coi cả hai đã đạt được từ start [2,4]. Mục đích: cấu hình cầu và full key; không gộp hai hàng cầu thành một nhóm.

<a id="soft_toggle_01"></a>
### `soft_toggle_01`

Nhóm soft/toggle, Achraf `level4`. `manual_local`: từ start U [3,1], bits `(false,false)`, RIGHT → H [[3,2],[3,3]], UP → H [[2,2],[2,3]] nhấn s02, dự kiến `(true,false)`. RIGHT → U [2,4] rời s02; LEFT → H [[2,2],[2,3]] nhấn lại, dự kiến `(false,false)`. s01 heavy [1,9] điều khiển riêng b02. Mục đích: cạnh nhấn và rời/nhấn lại, chưa có lời giải tới goal.

<a id="soft_toggle_02"></a>
### `soft_toggle_02`

Nhóm soft/toggle, Achraf `level6`. `manual_local`: từ start [0,2], RIGHT ×5 dự kiến H [[0,9],[0,10]], RIGHT tới U [0,11] nhấn s01: bits `(false,false,false)` → `(true,false,false)`. LEFT rời, RIGHT nhấn lại đưa b01 về false, b02/b03 giữ nguyên. s02 [5,11] nối b02 [8,5]; s03 [9,11] nối b03 [8,4]. Mục đích: ba bits độc lập và tránh gộp hai cầu kề nhau có liên kết khác nhau. Ca giữ đè dành cho khối tách trong `combined_02`.

<a id="heavy_01"></a>
### `heavy_01`

Nhóm heavy, Achraf `level5`. `manual_local`: snapshot H [[5,9],[5,10]], b01=false, UP → H [[4,9],[4,10]] đè heavy [4,10] khi nằm, cầu phải giữ false. Snapshot U [4,10] đang nhấn: LEFT → H [[4,8],[4,9]] rời, RIGHT → U [4,10] nhấn mới, dự kiến b01 đổi false→true. Những snapshot này chưa có đường từ start [4,2]. Mục đích: heavy chỉ nhấn khi UPRIGHT và kích hoạt lại sau khi rời.

<a id="heavy_02"></a>
### `heavy_02`

Nhóm heavy, Achraf `level10`. `manual_local`: snapshot H [[6,13],[6,14]], UP → H [[5,13],[5,14]] gồm heavy+fragile, dự kiến được đỡ và không nhấn heavy. DOWN rời; từ snapshot V [[6,13],[7,13]], UP → U [5,13] trên heavy, dự kiến đảo b01. b01 là [9,8]; không thay fragile [5,14] bằng floor để dễ giải. Mục đích: kết hợp trọng lượng công tắc và fragile; snapshot chưa được xác nhận reachable từ start.

<a id="permanent_open_01"></a>
### `permanent_open_01`

Nhóm permanent, Frank `levelsc`. `manual_local`: với snapshot V [[2,7],[3,7]], bits `(false,false,false)`, UP → U [1,7] nhấn s01, dự kiến `(true,false,false)`. DOWN rời rồi UP nhấn lại vẫn `(true,false,false)`. Các ô của snapshot đều floor, s01 là soft. Phân tích chỉ áp dụng chuỗi này: s03 [4,1] có thể đặt b01 đóng khi đi đường khác, nên không tuyên bố cầu mở mãi trên toàn màn. Mục đích: permanent mở khác toggle, giữ mọi effect khác của nguồn; chưa chứng minh đường từ start.

<a id="permanent_close_01"></a>
### `permanent_close_01`

Nhóm permanent, Frank `leveldw`. `manual_local`: snapshot V [[7,8],[8,8]], b01=true, UP → U [6,8] nhấn s01, dự kiến b01=false. DOWN rời, UP nhấn lại vẫn false. Không có công tắc mở lại cầu [[0,6],[1,6]], nhưng chưa kết luận khả giải vì goal [1,4] có đường đỡ khác cần khảo sát. Mục đích: đặt đóng, không đảo lại khi nhấn lần hai; snapshot chưa có đường từ start.

## Tách, nhập và tương tác

<a id="split_merge_01"></a>
### `split_merge_01`

Nhóm split/merge, Frank `levelss`. `manual_local`: từ start U [4,1], RIGHT, RIGHT → đứng lên split [4,4], dự kiến SPLIT [[1,10],[7,10]], active=0, bridges=(). SWITCH chọn khối [7,10]; UP ×5 đưa khối này lần lượt qua [6,10]...[2,10]. Ở bước cuối nó kề [1,10], dự kiến merge thành V [[1,10],[2,10]], active=null. Chưa có lời giải tới goal [4,13]. Mục đích: teleport, SWITCH và nhập theo cạnh, không chỉ kiểm đích tách.

<a id="split_merge_02"></a>
### `split_merge_02`

Nhóm split/merge, Frank `levelre`. `manual_local`: khi đứng vào split [4,13], destinations giữ thứ tự [[4,12],[4,2]] và active_destination=0; cells sau sort là [[4,2],[4,12]], active=1. SWITCH phải chọn [4,2]. Một chuỗi cục bộ từ snapshot ngay sau tách: DOWN với khối [4,12] → [5,12]; SWITCH; DOWN với khối [4,2] → [5,2]; RIGHT ×9 đến [5,11] kề [5,12], dự kiến H [[5,11],[5,12]], active=null. Chưa có đường từ start [4,1] tới split. Mục đích: giữ đúng khối active qua sort và đường nhập khác map trước.

<a id="combined_01"></a>
### `combined_01`

Nhóm kết hợp, Frank `levelht`. `manual_local`: khi kích hoạt split [5,7], dự kiến cells [[1,13],[8,1]], active=0; LEFT tới heavy [1,12] bằng khối nhỏ không nhấn s01, bridge bits giữ nguyên. Độc lập từ snapshot ngay sau tách với b04=true: SWITCH, RIGHT ×10 đưa khối còn lại tới [8,11], UP tới soft [7,11] đặt b04=false, đóng [[8,9],[8,10]]. Vị trí sau bước đó vẫn được đỡ; cả hai khối chưa nhập. Mục đích: khối nhỏ không nhấn heavy nhưng nhấn soft; chưa có đường từ start tới split, không coi snapshot sau tách là initial state.

<a id="combined_02"></a>
### `combined_02`

Nhóm kết hợp, Frank `leveltb`. `manual_local`: từ snapshot ngay sau split [4,7], cells [[1,13],[7,13]], active=0 và b03=false, SWITCH, LEFT, UP đưa khối dưới tới soft [6,12], dự kiến b03=true. SWITCH chọn khối [1,13], LEFT tới [1,12]: soft vẫn bị khối không active đè, b03 phải giữ true. SWITCH, DOWN, UP rời/nhấn lại s05 đưa b03=false. SWITCH không kích hoạt công tắc; các ô đường cục bộ đều được đỡ và hai khối không kề nhau. Mục đích: giữ đè qua đổi điều khiển khác nhấn mới. Chưa có đường từ start [2,8] tới split hoặc lời giải tới goal.

## Fixture vô nghiệm nâng cao

<a id="advanced_unsolvable_01"></a>
### `advanced_unsolvable_01`

Nhóm vô nghiệm nâng cao, original, hiện thực thiết kế 5 × 10 đã ghi trong [catalog](../maps/README.md#blueprint-original-cho-khoảng-trống-vô-nghiệm-nâng-cao); không chuyển từ hoặc sửa layout của màn tiếp nhận. Mục đích: vô nghiệm do bất biến cầu, khác fixture goal cô lập basic. Nguồn khảo sát và lý do tự tạo được ghi [bên dưới](#khảo-sát-bổ-sung-trước-khi-tự-tạo).

`manual_invariant`: b01=[[1,4],[1,5]] ban đầu false, công tắc duy nhất s01 [2,3] chỉ đặt false, không có split/teleport. Bởi vậy b01 luôn đóng theo contract. Tập ô đỡ bên trái là hàng 1–3/cột 1–3; bên phải là hàng 1–3/cột 6–8. Hai cột 4–5 luôn không đỡ khối. Không thể vượt khoảng trống hai cột bằng một bước lăn hợp lệ: từ bên trái, UPRIGHT sang phải chiếm ít nhất một cột 4/5 hoặc HORIZONTAL sang đứng vẫn chưa tới cột 6; di chuyển dọc không đổi phía. Mọi state hợp lệ từ start vẫn bên trái, trong khi goal [1,7] bên phải. Do đó kỳ vọng `expected_solvable=false`; chưa tuyên bố engine đã duyệt cạn.

Witness tay từ start U [1,1], bits `(false)`: RIGHT → H [[1,2],[1,3]]; DOWN → H [[2,2],[2,3]] nhấn s01, b01 vẫn false; UP rời, DOWN nhấn lại vẫn false. RIGHT ngay sau RIGHT đầu tiên cố đứng tại [1,4], dự kiến LOST vì cầu đóng. Test khóa layout, cấu hình duy nhất và nhãn; không mô phỏng luật hoặc dùng nhãn để trả UNSOLVABLE.

## Khảo sát bổ sung trước khi tự tạo

Ngày 17/10/2026, rà lại [nhật ký nguồn](advanced-map-source-survey.md#6-kết-luận-khảo-sát-và-khoảng-trống) và tìm nhắm nhóm vô nghiệm nâng cao với truy vấn `Bloxorz unsolvable level bridge switch map dataset github` và `site.github.com/sublevelgames/lm-pcg bloxorz unsolvable`. Không tiếp nhận thêm dữ liệu hay code ngoài.

- Achraf/Frank đã ghim: các màn đã chọn không kèm chứng minh vô nghiệm theo luật nhóm; không sửa một màn thành vô nghiệm rồi tăng số lượng. Matías chỉ bù basic; các nguồn chưa có quyền rõ vẫn giữ quyết định loại trong hồ sơ trước.
- [Dataset card mattismegevand/bloxorz](https://huggingface.co/datasets/mattismegevand/bloxorz), đọc ngày 17/10: mô tả các level có lời giải BFS, ký hiệu start/goal/floor/void và trường shortest_path/solution_length. Không cung cấp fixture vô nghiệm cầu/công tắc trong mô tả đã đọc; không tải dataset hoặc nhận chứng nhận lời giải làm bằng chứng engine nhóm.
- [Mô tả dữ liệu Mindcraft của sublevelgames](https://sublevelgames.com/blogs/2025-10-20-generate-bloxorz-map-with-gpt-2/), bài ngày 20/10/2025, đọc ngày 17/10/2026: có glass/bridge/switch, nhưng cầu và tường có công tắc dùng một lần, khác contract toggle/permanent của nhóm. Bài không cung cấp hồ sơ vô nghiệm cầu luôn đóng cần cho fixture này; không thay đổi kết luận về quyền dataset từ khảo sát trước.

Kết luận trong phạm vi nguồn đã đọc: chưa tìm được ứng viên ngoài phù hợp có phân tích vô nghiệm rõ theo contract. Chọn một fixture original nhỏ để kiểm bất biến, giữ tổng 18 = 14 adapted + 4 original. Đây không phải khẳng định mọi nguồn ngoài đều thiếu map vô nghiệm.

## Kiểm tra và giới hạn

Test bundle đối chiếu đủ 18 đường dẫn với bốn JSON root và 14 JSON prepared, nhóm cơ chế, source, notice/conversion notes, SHA256 byte và hồ sơ từng ID. Chống trùng còn bỏ loại ô phụ, giữ hình học ô đỡ tiềm năng/start/goal; bỏ padding/tịnh tiến và thử tám phép quay/đối xứng. Quy tắc này chặt hơn so trùng metadata: cùng hình học dù đổi cách nối công tắc cũng bị từ chối. Có ca kiểm tra chính phép chuẩn hóa và dữ liệu schema sai. Không thêm validator runtime hoặc phụ thuộc mới.

Các witness cục bộ trên là đầu vào để kiểm engine về sau. Bên tích hợp cần chứng minh đường tới các snapshot, replay full key/bridge bits, kiểm mục tiêu và duyệt cạn map vô nghiệm. Bộ dữ liệu đã khóa không đồng nghĩa mọi map adapted đã được xác nhận khả giải hoặc mọi luật nâng cao đã chạy đúng.

AI hỗ trợ khảo sát nhắm khoảng trống, chuẩn bị fixture, phân tích tay và viết test/tài liệu; không tạo kết quả solver hoặc số đo benchmark.
