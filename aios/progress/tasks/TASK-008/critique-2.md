# Critique vòng 2 — TASK-008

## Đánh giá chung
Resolution v1 áp đúng ~90% (verify code thật: PyYAML ✓, register mới tinh ✓, AC4 policy ✓, refactor dag an toàn — không test assert message). **Không P1** — 5 P2 nhỏ + 5 P3.

## Vấn đề + Resolution

### P2-A — "retries: 0 = vô hạn" SAI với engine
- **Resolution**: sửa: `retries=0` → giữ 0 (engine: 1 attempt — đúng PlanNode default); `timeout_s=0` → giữ 0 (engine: không timeout).

### P2-B — WorkflowNode.type chưa pin kiểu
- **Resolution**: pin `type: PlanNodeType` (str Enum — YAML "task"/"tool" tự convert, fail-fast ở definition).

### P2-C — extra="forbid" cho Definition/Node
- **Resolution**: `model_config = ConfigDict(extra="forbid")` cho cả WorkflowDefinition lẫn WorkflowNode; AC1 thêm case: YAML key lạ → ValidationError.

### P2-D — CLI test: chọn cách gọi + db_path
- **Resolution**: AC9: test gọi `main()` trực tiếp + monkeypatch sys.argv (offline, deterministic — subprocess sẽ fail vì src layout chưa cài); CLI thật dùng `tempfile.TemporaryDirectory()` cho audit db (simulate = không ghi file dài hạn).

### P2-E — run không có --simulate
- **Resolution**: v1 `--simulate` BẮT BUỘC (thiếu → argparse error + hint "M2 sẽ chạy thật").

### P3 — (áp)
1. `depends_on` dùng `Field(default_factory=list)` (nhất quán PlanNode)
2. dag.py helper: duck-type (`.id`/`.depends_on`), raise ValueError (pydantic wrap), thứ tự unique → unknown → cycle
3. register overwrite: v1 key = name chỉ; version-aware M2 (ghi chú)
4. from_yaml: không wrap FileNotFoundError/yaml.YAMLError (exception tự nhiên — CLI in lỗi)
5. plan.id name chứa space — chấp nhận v1, không validate charset (note)

## Kết luận
- [x] **Resolve toàn bộ (5 P2 + 5 P3)** — spec cập nhật, sẵn sàng implement.
