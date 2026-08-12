# Milestone Review Brief — TEMPLATE (v2)

> **Mục đích**: tài liệu tự chứa (self-contained) để đem cho một model/người review ĐỘC LẬP đánh giá một milestone.
> **Cách dùng**: copy toàn bộ file này (bản đã điền `{{MILESTONE}}`) sang model review. Model review tự đọc file trong repo và đưa kết luận riêng — KHÔNG xem kết quả review trước đó.
> **Quy tắc**: model review KHÔNG sửa file, chỉ trả về báo cáo theo format mục 7.
>
> **Template v2**: chuyển trọng tâm từ *existence review* (file có tồn tại không) sang **runtime correctness & architecture review** (kiến trúc có đúng không, runtime có hoạt động đúng không). Bắt buộc áp dụng mục 4 (Architecture & Runtime Deep Review) cho mọi milestone.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "{{MILESTONE}}" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/adr/` (nếu có) — các quyết định kiến trúc đã ghi nhận (xem mục 4.11)

## 2. Nhiệm vụ

Review milestone **{{MILESTONE}}** — {{MILESTONE_DESCRIPTION}}.

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho milestone này không
2. **Đúng quy trình**: hard gate (spec/critique ×2/tasks/review/test/evaluate) có được tuân thủ cho từng task không
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế có khớp nhau không
4. **Đúng kiến trúc & runtime correctness**: kiến trúc có tuân thủ nguyên tắc AIOS không, runtime có hoạt động đúng không (xem mục 4)

## 3. Deliverable cần kiểm tra

{{DELIVERABLE_LIST — đường dẫn cụ thể từng file/task, đủ để model tự đọc. Phải bao gồm cả code, tests (chạy thật), và hồ sơ quy trình (spec/critique/tasks/review/test/evaluation mỗi task)}}

## 4. Architecture & Runtime Deep Review (TRỌNG TÂM — áp dụng mọi milestone)

Reviewer phải xác minh kiến trúc AIOS tuân thủ các nguyên tắc cốt lõi — **KHÔNG chỉ xem file tồn tại**. Phải xác minh dependency graph (dùng `grep` import hoặc đọc `from/import`).

### 4.1 Architecture Compliance (8 nguyên tắc)
- **Runtime-first**: logic nghiệp vụ chạy trong Runtime Kernel, không rải rác ở CLI/agent.
- **Contract-first**: giao tiếp qua contract, không qua kiểu dữ liệu nội bộ.
- **Plugin-first**: capability/tool/model có thể cắm thêm mà không sửa core.
- **Engine-independent**: declarative definition độc lập engine (vd: workflow không import engine cụ thể).
- **Capability-first**: agent gọi capability, không gọi tool trực tiếp.
- **Policy-first**: mọi request bị policy pre-check trước execution.
- **Dependency Injection**: service được resolve qua container, không khởi tạo trực tiếp rải rác.
- **Event-driven**: runtime phát event qua Event Bus.

Ví dụ đúng: `Workflow → Capability → Tool`. Sai (FAIL): `Workflow → Docker`.

### 4.2 Dependency Rules
- **import graph**: layer trên không import ngược layer dưới sai nguyên tắc.
- **circular dependency**: không có vòng lặp import.
- **layer violation**: layer thấp (Tool/infra) không import layer cao (Runtime Kernel).

### 4.3 Runtime Wiring
Xác minh: service registration, lifecycle (init/start/stop), Singleton/Scoped đúng scope, DI resolve.
Đúng: `Runtime → Container → Service (resolve)`. Sai: `Service()` tạo trực tiếp rải rác khắp code.

### 4.4 Contract Evolution
Old Contract → Compatibility Checker → New Contract. Các case:
| Case | Kết quả |
|------|---------|
| add field | PASS (backward-compatible) |
| remove required field | FAIL (breaking) |
| rename field | FAIL (breaking) |
| optional → required | FAIL (breaking) |

### 4.5 Layer Isolation
Acceptance: `Agent → Capability → Tool` (hoặc tương đương theo milestone). Reviewer phải **TÌM** tool cụ thể (`DockerTool(...)`) bên trong Agent. Nếu Agent khởi tạo Tool trực tiếp → **FAIL**.

### 4.6 Policy Engine
Policy pre-check phải cover TẤT CẢ scope liên quan (vd: internet/filesystem/shell/docker/network/clipboard) và reject **TRƯỚC execution**.

### 4.7 Event Review
Event Bus phải **emit** các event liên quan (vd: Execution/Tool Started/Finished, Policy Denied, Snapshot Saved). Xác minh emit thực sự được gọi trong code path.

### 4.8 Resource Review
Resource Service phải có test cho: allocate / queue / reject / release.

### 4.9 Context Review
Các context (theo milestone). Kiểm tra: isolation / TTL / cleanup / inheritance.

### 4.10 Performance
Milestone runtime phải có benchmark tối thiểu (vd: catalog search < 5 ms, workflow compile < 50 ms, capability lookup O(1)). Điều chỉnh ngưỡng theo milestone.

### 4.11 Architecture Decision Record
Đọc `docs/adr/` (nếu có) để xem implementation có đúng quyết định kiến trúc không.

### 4.12 Anti Fake Test (RẤT QUAN TRỌNG)
Không chỉ "N tests pass". Reviewer phải kiểm tra coverage thật sự cover Acceptance Criteria. Phải **đọc body test**, không chỉ đếm số pass. Test chỉ `assert True` vẫn pass nhưng không test đúng → phải bị bắt.

## 5. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification)

{{AC_TABLE — mỗi dòng: tiêu chí | cách kiểm chứng | bằng chứng mong đợi. Phải map mỗi tiêu chí với các mục 4.1–4.12 liên quan (vd: "Vx — ... + mục 4.3 Runtime Wiring")}}

## 6. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 5: tìm bằng chứng → kết luận **PASS/FAIL/INCONCLUSIVE** kèm trích dẫn `file:đường dẫn`
3. Áp dụng Architecture & Runtime Deep Review (mục 4.1–4.12) — mỗi mục phải có kết luận rõ
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
5. Tìm lỗ hổng chủ động: file thiếu, stub không logic, mâu thuẫn, checkbox chưa tick, claim không có bằng chứng, **test pass nhưng không test đúng thứ cần test** (mục 4.12)
6. Với mỗi task: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 7. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review {{MILESTONE}} — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả (PASS/FAIL/INCONCLUSIVE) | Bằng chứng (file + trích dẫn) |

## 2. Architecture Compliance
(đối chiếu mục 4.1–4.12: Runtime-first / Contract-first / Plugin-first / Engine-independent /
Capability-first / Policy-first / DI / Event-driven / Dependency / Wiring / Security /
Performance / Event Bus / Anti-fake-test — mỗi nguyên tắc ghi PASS/FAIL/INCONCLUSIVE + trích dẫn)

## 3. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 4. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 5. Điểm mạnh (nếu có)
## 6. Gợi ý cải thiện (không bắt buộc)
```

## 8. Final Gate (nâng cấp)

Kết quả mỗi tiêu chí thuộc một trong 3 trạng thái:
- **PASS**: Có bằng chứng trực tiếp và kiểm chứng được (đọc code + chạy test/CLI).
- **FAIL**: Có bằng chứng cho thấy không đạt.
- **INCONCLUSIVE**: Không đủ bằng chứng để kết luận (reviewer không có quyền chạy, thiếu file, hoặc mâu thuẫn không giải được).

**Milestone chỉ được ACCEPTED khi:**
- Tất cả tiêu chí mục 5 = **PASS** (không FAIL, không INCONCLUSIVE)
- Không có **P1** finding
- Không có **INCONCLUSIVE** nào trong bảng tiêu chí
- Các test bắt buộc chạy thành công trên môi trường review (hoặc có bằng chứng thực thi đáng tin cậy nếu reviewer không có quyền chạy)

> Nếu có bất kỳ **INCONCLUSIVE** nào, milestone không được ACCEPTED cho đến khi reviewer có đủ bằng chứng nâng lên PASS hoặc FAIL.

---

## Cách tạo bản điền sẵn cho milestone mới

Copy template này → đổi tên `{{MILESTONE}}-review-brief.md` → điền 4 placeholder: `{{MILESTONE}}`, `{{MILESTONE_DESCRIPTION}}`, `{{DELIVERABLE_LIST}}`, `{{AC_TABLE}}` (lấy AC từ PLAN.md mục Verification). Khi điền `{{AC_TABLE}}`, nhớ map mỗi tiêu chí với mục 4.1–4.12 tương ứng.
