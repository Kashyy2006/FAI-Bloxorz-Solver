# data

**Nội dung:** Dữ liệu màn chơi và nguồn tham khảo dùng trong dự án.

**Phụ trách:** Thành viên 4.

- `maps/`: bốn map basic dùng cho luồng game hiện tại; [catalog](maps/README.md) ghi nguồn/hash và oracle tham chiếu.
- `maps/`: 14 map nâng cao đã kiểm dữ liệu, chưa xác nhận engine/replay/solver.
- [map_bundle.json](map_bundle.json): manifest khóa 18 map, đường dẫn từ repo root, nguồn/hash/nhóm và trạng thái riêng từng map; không bao gồm draft.
- [Hồ sơ kiểm tra](references/map-bundle-evidence.md): mục đích, witness/phân tích tay, mức tin cậy và giới hạn xác minh của từng map.
- `maps/drafts/`: đầu ra mặc định của converter trước kiểm tra; draft không tính vào inventory đã đạt.
- `references/`: dữ liệu nguồn, notice, converter và ghi chú chuyển đổi theo nguồn.
