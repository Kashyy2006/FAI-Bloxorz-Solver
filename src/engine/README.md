# Engine cơ bản — Thành viên 1

Engine dùng chung cho GUI và solver, viết bằng Python thuần và không phụ thuộc Pygame.

- `models.py`: State bất biến, enum hành động/trạng thái và kiểu kết quả.
- `map_loader.py`: nạp và kiểm tra map JSON phiên bản 1.
- `rules.py`: trạng thái đầu, chuyển trạng thái, successors, kiểm tra đích và chi phí.
- `__init__.py`: API công khai, import từ `src.engine`.

Mốc 18/10 hỗ trợ `void`, `floor`, `goal`, `fragile` và khối nguyên. Validator từ chối map có cầu/công tắc/tách khối để tránh engine chạy sai luật; cơ chế nâng cao được triển khai ở mốc sau.

Ví dụ dùng từ thư mục gốc project:

```python
from src.engine import load_map, initial_state, transition

game_map = load_map("data/maps/basic_01.json")
state = initial_state(game_map)
result = transition(game_map, state, "RIGHT")
```
