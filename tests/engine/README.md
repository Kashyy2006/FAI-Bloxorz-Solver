# Kiểm thử engine — TV1

- test_basic_engine.py: 12 chuyển động nguyên khối, goal/void/fragile và validator cơ bản.
- test_advanced_engine.py: cầu/công tắc, toggle/permanent, split/merge, active, events,
  chi phí, tính bất biến và validator nâng cao.
- Kiểm thử tích hợp với GUI và cả 4 solver: tests/integration/test_advanced_shared_engine.py.

Chạy từ gốc repo: `python -m unittest discover -s tests -t . -v`.
