# TASK-075 — Review (trước implement)

> Reviewer (tự). Review spec v2.

## Đánh giá
- 6 metric + 5 chiều cost đúng PLAN §M10-35. ✅
- Injectable tokens (offline-first) + không du (C1-02). ✅
- Model independence test cụ thể. ✅

## Yêu cầu
1. **R1**: Mọi nguồn dữ liệu bọc try/except → 0/SKIPPED khi DB rỗng.
2. **R2**: Cost công thức chuẩn (tokens/1M × cost) — test số cụ thể (C2-01).
3. **R3**: KHÔNG sửa providers (Mock/OpenAI/Ollama) — chỉ test contract chung.
4. **R4**: CLI 2 lệnh (`cost`, `performance`) ổn định.

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
