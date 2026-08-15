# TASK-047 — Critique v2 (đầy đủ)

## Phản biện độc lập vòng 2
- **P1-01**: `DevKit` phải là class nhỏ với method duy nhất `create_scaffold`; không cần state.
- **P1-02**: YAML manifest phải parse lại được bằng `yaml.safe_load` (test).
- **P2-01**: out_dir không tồn tại → tạo (mkdir parents).
- **P2-02**: Trả về list file paths đã tạo (để test/CLI report).
- **P3-01**: stub plugin ghi rõ "TODO: implement run()".

## Resolution
- ✅ class stateless; ✅ yaml round-trip test; ✅ mkdir parents; ✅ return paths; ✅ TODO marker.
