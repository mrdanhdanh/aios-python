# Review M0 — Development Foundation

> **Bản review độc lập từ `REVIEW-BRIEF-TEMPLATE.md`.**
>
> File này được đưa cho một reviewer/model độc lập. Reviewer phải **đọc repository thực tế và tự kết luận**, không dựa vào `M0-review.md`, claim của agent, hoặc mô tả trong file khác nếu không có bằng chứng đối chiếu.
>
> **Mục tiêu:** xác định M0 có đủ điều kiện chuyển sang milestone tiếp theo hay chưa.

---

# 1. Bối cảnh dự án

Dự án **AIOS (AI Operating System)** — hệ điều hành agent chạy local desktop, phát triển theo milestone M0–M4.

Quy trình phát triển bắt buộc:

```text
Plan
  ↓
Spec
  ↓
Critique ×2
  ↓
Tasks
  ↓
Review
  ↓
Implement
  ↓
Test
  ↓
Evaluate
  ↓
Hard Gate
  ↓
Complete
```

**Hard Gate:** Không được coi task/milestone hoàn thành nếu thiếu artifact bắt buộc hoặc thiếu bằng chứng kiểm chứng.

## Tài liệu bắt buộc đọc trước khi review

1. `docs/PLAN.md`

   * Đặc biệt mục **M0 – Development Foundation**
   * Mục **Verification (theo milestone)**
2. `AGENTS.md`
3. Các file thực tế được liệt kê trong mục 3.
4. Git history thực tế.

> Reviewer **không được sử dụng `M0-review.md` làm nguồn bằng chứng** vì đây là review nội bộ cần được kiểm chứng độc lập.

---

# 2. Nhiệm vụ review

Review độc lập milestone **M0 — Development Foundation** trên 4 chiều:

### R1 — Scope Compliance

M0 có thực hiện đúng những gì `PLAN.md` cam kết không?

### R2 — Process Compliance

TASK-001 có tuân thủ đầy đủ workflow:

```text
spec
→ critique-1
→ critique-2
→ tasks
→ review
→ implementation
→ test
→ evaluation
```

không?

### R3 — Evidence Integrity

Mọi claim "đã hoàn thành" có artifact hoặc evidence thực tế chứng minh không?

### R4 — Repository Consistency

Các nguồn sau có nhất quán không?

```text
PLAN
   ↕
Task artifacts
   ↕
PROGRESS
   ↕
LOG
   ↕
STATS
   ↕
Git history
   ↕
Actual files
```

---

# 3. Deliverables bắt buộc

| #  | Path                                        | Kiểm tra                                                                   |
| -- | ------------------------------------------- | -------------------------------------------------------------------------- |
| 1  | `docs/PLAN.md`                              | Tồn tại; đúng master plan; M0 rõ ràng; verification có tiêu chí nghiệm thu |
| 2  | `AGENTS.md`                                 | Có quy tắc đọc PROGRESS đầu phiên + ghi LOG sau hành động                  |
| 3  | `.gitignore`                                | Tồn tại; hợp lý; không ignore nhầm artifact cần commit                     |
| 4  | `.github/agents/aios-orchestrator.agent.md` | Frontmatter + body đúng contract                                           |
| 5  | `.github/agents/spec-writer.agent.md`       | Tồn tại; `user-invocable: false`                                           |
| 6  | `.github/agents/critic.agent.md`            | Tồn tại; `user-invocable: false`; critique ×2                              |
| 7  | `.github/agents/reviewer.agent.md`          | Tồn tại; `user-invocable: false`                                           |
| 8  | `aios/progress/PROGRESS.md`                 | Có M0 + B0–B4 + trạng thái                                                 |
| 9  | `aios/progress/LOG.md`                      | Có entry cho B0→B4 đúng format                                             |
| 10 | `aios/progress/STATS.md`                    | Có M0: task, critique resolve, bypass, commit                              |
| 11 | `aios/progress/tasks/TASK-001/`             | Đủ artifact bắt buộc                                                       |
| 12 | Git history                                 | Có ≥5 commit M0, tương ứng B0→B4                                           |

---

# 4. TASK-001 Artifact Contract

Reviewer **không được chỉ đếm file**.

Thư mục:

```text
aios/progress/tasks/TASK-001/
```

phải có:

```text
spec.md
critique-1.md
critique-2.md
tasks.md
review.md
test.md
evaluation.md
implementation/
```

## Điều kiện hợp lệ

### `spec.md`

Phải chứa:

* task objective
* scope
* acceptance criteria
* constraints
* expected artifacts

### `critique-1.md`

Phải chứa:

* findings
* severity
* resolution hoặc disposition

### `critique-2.md`

Phải là **một vòng critique độc lập thứ hai**, không chỉ copy critique-1.

Phải có:

* findings
* severity
* resolution/disposition

### `tasks.md`

Phải map implementation task với acceptance criteria.

### `review.md`

Phải có:

* review result
* evidence
* findings
* disposition

### `test.md`

Phải có:

* test case
* expected result
* actual result
* evidence
* PASS/FAIL

> Một dòng `PASS` không có evidence **không được coi là bằng chứng hợp lệ**.

### `evaluation.md`

Phải có:

* evaluation result
* quality assessment
* unresolved issues
* final recommendation

### `implementation/`

Phải:

* tồn tại
* chứa artifact implementation thực tế hoặc bằng chứng implementation hợp lệ
* artifact phải tương ứng với task scope

Thư mục rỗng **không được tính là implementation hoàn chỉnh**.

---

# 5. Orchestrator Agent Contract

File:

```text
.github/agents/aios-orchestrator.agent.md
```

## Frontmatter bắt buộc

Phải kiểm tra thực tế:

```yaml
description: ...
user-invocable: true
tools: ...
agents: ...
```

### `description`

Phải đủ keyword để agent picker có thể nhận diện các nhóm nhiệm vụ chính:

* AIOS
* orchestration
* agent
* workflow
* skill
* system
* task
* development

Không chấp nhận description quá chung như:

```yaml
description: AI assistant
```

### Body bắt buộc

Phải có:

1. Hard gate
2. Bypass rules
3. Task classification
4. Progress requirement
5. LOG requirement
6. Agent delegation rules
7. Critique ×2 requirement
8. Rule không bypass hard gate bằng cách tự tuyên bố hoàn thành

---

# 6. Verification Criteria

## V1 — Agent Picker

**Requirement**

Agent picker phải hiển thị:

```text
AIOS Orchestrator
```

và người dùng có thể chọn agent.

### Evidence

Phải có:

* `user-invocable: true`
* test evidence trong `TASK-001/test.md`
* nếu test thủ công: ghi rõ thao tác và actual result

### Không chấp nhận

```text
PASS — agent hoạt động tốt
```

nếu không có evidence.

---

## V2 — Hard Gate

Requirement:

> Request implement task chưa có `spec + critique-1 + critique-2` phải bị từ chối.

### Kiểm tra

1. Agent file có rule.
2. Có test case.
3. Có actual result.
4. Có evidence.

Expected:

```text
Request
  ↓
Missing required artifacts
  ↓
REJECT
```

---

## V3 — Bypass

Fix nhỏ có thể bypass nếu agent policy cho phép.

Nếu bypass:

```text
[bypass]
reason: ...
```

phải xuất hiện trong `LOG.md`.

### Quy tắc

Không có bypass thực tế **không phải lỗi**.

Reviewer chỉ cần xác nhận:

* bypass rule tồn tại
* điều kiện bypass rõ
* yêu cầu LOG rõ
* không cho phép bypass tùy tiện

---

## V4 — Progress / LOG / Git

Đối chiếu:

```text
PROGRESS
   ↕
LOG
   ↕
Git
   ↕
Actual files
```

Phải xác minh từng bước:

```text
B0
B1
B2
B3
B4
```

### Mỗi bước phải có

* trạng thái trong `PROGRESS.md`
* entry tương ứng trong `LOG.md`
* artifact thực tế
* commit tương ứng hoặc evidence hợp lệ

Không được coi:

```text
PROGRESS = Done
```

là bằng chứng nếu artifact/git không khớp.

---

## V5 — Critique ×2

TASK chỉ được Done khi:

```text
critique-1.md
+
critique-2.md
+
resolution
```

đều tồn tại.

Reviewer phải xác nhận:

* Hai vòng thực sự độc lập.
* Có findings hoặc explicit "no findings".
* Có resolution/disposition.
* Không phải duplicate file đổi tên.

---

# 7. Git Verification

Reviewer phải chạy lệnh thực tế nếu có quyền:

```bash
git log --oneline --decorate --all
git status --short
git diff
git diff --cached
```

Có thể sử dụng thêm:

```bash
git log --stat
git show <commit>
git log --follow -- <file>
```

## M0 requirement

Phải xác định được ≥5 commit tương ứng với:

```text
B0
B1
B2
B3
B4
```

Reviewer không được chỉ dựa vào commit message.

Phải đối chiếu:

```text
Commit
  ↓
Changed files
  ↓
Expected milestone artifact
```

---

# 8. Consistency Matrix

Reviewer phải tạo bảng đối chiếu:

| Step | PROGRESS | LOG | Git | Artifact | Result    |
| ---- | -------- | --- | --- | -------- | --------- |
| B0   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B1   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B2   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B3   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B4   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |

---

# 9. Evidence Rules

Reviewer phải phân loại evidence:

### E1 — Direct Evidence

Artifact/file/git output thực tế.

→ Evidence mạnh nhất.

### E2 — Test Evidence

Test case + actual result + evidence.

→ Hợp lệ.

### E3 — Self Claim

Ví dụ:

```text
Agent nói: "đã hoàn thành"
```

→ Không đủ để PASS.

### E4 — Derived Evidence

Suy luận từ nhiều artifact.

→ Có thể sử dụng nhưng phải chỉ rõ cách suy luận.

## Rule

> **Claim không có evidence = chưa được chứng minh.**

Không được biến:

```text
UNKNOWN
```

thành:

```text
PASS
```

chỉ vì reviewer không tìm thấy lỗi.

---

# 10. Finding Severity

## P1 — Blocking

Sai mục tiêu hoặc vi phạm acceptance criteria.

Ví dụ:

* thiếu hard gate
* thiếu critique-2
* test claim không có evidence
* artifact bắt buộc thiếu
* PROGRESS nói Done nhưng implementation không tồn tại
* worker có thể bypass permission enforcement

**P1 phải sửa trước khi M0 được ACCEPTED.**

## P2 — Significant

Thiếu sót đáng kể nhưng không phá acceptance criteria chính.

Ví dụ:

* LOG thiếu một số metadata
* documentation chưa đầy đủ
* naming không thống nhất

## P3 — Minor

Cải thiện nhỏ:

* wording
* formatting
* documentation clarity
* developer experience

---

# 11. Anti-False-Positive Checks

Reviewer phải chủ động kiểm tra:

* File có tồn tại nhưng rỗng không?
* Checkbox đã tick nhưng artifact chưa tồn tại không?
* `test.md` ghi PASS nhưng không có actual result không?
* `PROGRESS.md` ghi Done nhưng git chưa có commit không?
* Commit message nói "complete" nhưng thiếu artifact không?
* `critique-2.md` có thực sự khác critique-1 không?
* `review.md` có bằng chứng hay chỉ kết luận?
* `implementation/` có thực sự chứa implementation không?
* Có untracked file chứa artifact nhưng chưa commit không?
* `.gitignore` có vô tình che artifact không?
* Có artifact được tạo sau commit nhưng PROGRESS đã ghi Done trước đó không?

---

# 12. Review Decision Matrix

| Điều kiện                                 | Kết quả                     |
| ----------------------------------------- | --------------------------- |
| Có P1                                     | **CHƯA ĐẠT**                |
| V1–V5 có bất kỳ FAIL                      | **CHƯA ĐẠT**                |
| Có INCONCLUSIVE trên acceptance criterion | **CHƯA ĐẠT**                |
| Không P1, nhưng có P2                     | Có thể **ĐẠT CÓ ĐIỀU KIỆN** |
| Chỉ có P3                                 | **ĐẠT**                     |
| V1–V5 PASS + không P1/P2                  | **ĐẠT**                     |

### Hard Gate cuối

M0 chỉ được:

```text
ACCEPTED
```

khi:

```text
V1 PASS
AND V2 PASS
AND V3 PASS
AND V4 PASS
AND V5 PASS
AND P1 = 0
```

Nếu thiếu evidence cho bất kỳ acceptance criterion nào:

```text
NOT ACCEPTED
```

---

# 13. Phương pháp review bắt buộc

Reviewer phải thực hiện theo thứ tự:

### Step 1 — Read Plan

Đọc `docs/PLAN.md`.

Trích xuất:

* M0 scope
* M0 deliverables
* M0 verification
* dependencies

### Step 2 — Read Governance

Đọc `AGENTS.md`.

Xác định:

* progress rules
* logging rules
* hard gate
* bypass rules

### Step 3 — Inspect Files

Đọc từng deliverable thực tế.

Không dựa vào mô tả.

### Step 4 — Inspect TASK-001

Đếm và đọc toàn bộ artifact.

### Step 5 — Inspect Git

Chạy git commands thực tế.

### Step 6 — Cross-check

Đối chiếu:

```text
PLAN
↕
AGENTS
↕
TASK
↕
PROGRESS
↕
LOG
↕
STATS
↕
GIT
↕
FILESYSTEM
```

### Step 7 — Verify V1–V5

Mỗi criterion:

```text
Requirement
→ Evidence
→ Analysis
→ PASS/FAIL
```

### Step 8 — Search Contradictions

Chủ động tìm:

* stale status
* missing artifact
* contradictory dates
* contradictory commit claims
* unchecked checkbox
* duplicate critique
* fake test evidence
* untracked files
* ignored required files

### Step 9 — Assign Findings

P1/P2/P3.

### Step 10 — Final Gate

Áp dụng Decision Matrix.

---

# 14. Output Format — BẮT BUỘC

Reviewer phải trả về **đúng cấu trúc sau**:

# Review M0 — bởi `<tên model / reviewer>`

## 1. Executive Summary

* **Decision:** ĐẠT / ĐẠT CÓ ĐIỀU KIỆN / CHƯA ĐẠT
* **P1:** `<số lượng>`
* **P2:** `<số lượng>`
* **P3:** `<số lượng>`
* **V1–V5:** `<PASS/FAIL/INCONCLUSIVE>`
* **Overall:** `<1–10>`

Một đoạn ngắn giải thích lý do.

## 2. Bảng đối chiếu tiêu chí

| #  | Tiêu chí         | Kết quả   | Evidence    | Kết luận |
| -- | ---------------- | --------- | ----------- | -------- |
| V1 | Agent picker     | PASS/FAIL | `file:line` | ...      |
| V2 | Hard gate        | PASS/FAIL | `file:line` | ...      |
| V3 | Bypass           | PASS/FAIL | `file:line` | ...      |
| V4 | Progress/LOG/Git | PASS/FAIL | `file:line` | ...      |
| V5 | Critique ×2      | PASS/FAIL | `file:line` | ...      |

**Mỗi kết luận phải có evidence cụ thể.**

## 3. Consistency Matrix

| Step | PROGRESS | LOG | Git | Artifact | Result    |
| ---- | -------- | --- | --- | -------- | --------- |
| B0   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B1   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B2   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B3   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |
| B4   | ✓/✗      | ✓/✗ | ✓/✗ | ✓/✗      | PASS/FAIL |

## 4. TASK-001 Artifact Audit

| Artifact        | Exists | Non-empty | Valid | Evidence | Result |
| --------------- | ------ | --------- | ----- | -------- | ------ |
| spec.md         |        |           |       |          |        |
| critique-1.md   |        |           |       |          |        |
| critique-2.md   |        |           |       |          |        |
| tasks.md        |        |           |       |          |        |
| review.md       |        |           |       |          |        |
| test.md         |        |           |       |          |        |
| evaluation.md   |        |           |       |          |        |
| implementation/ |        |           |       |          |        |

## 5. Findings

| ID    | Severity | Description | Evidence    | File | Required Action |
| ----- | -------- | ----------- | ----------- | ---- | --------------- |
| F-001 | P1/P2/P3 | ...         | `path:line` | ...  | ...             |

Nếu không có finding:

```text
No findings.
```

## 6. Evidence Gaps

Liệt kê riêng những claim chưa chứng minh được.

| Claim | Expected Evidence | Actual Evidence | Impact |
| ----- | ----------------- | --------------- | ------ |
| ...   | ...               | ...             | ...    |

Nếu không có:

```text
No evidence gaps.
```

## 7. Strengths

Liệt kê các điểm làm tốt, chỉ khi có evidence.

## 8. Final Gate

```text
V1: PASS/FAIL
V2: PASS/FAIL
V3: PASS/FAIL
V4: PASS/FAIL
V5: PASS/FAIL

P1 = N
P2 = N
P3 = N

FINAL: ACCEPTED / CONDITIONALLY_ACCEPTED / NOT_ACCEPTED
```

### Quy tắc cuối cùng

Reviewer **không được tự sửa repository** trong quá trình review.

Reviewer chỉ:

* đọc
* kiểm tra
* chạy test/read-only commands
* thu thập evidence
* kết luận
* đề xuất remediation

Không được:

* edit file
* tạo artifact
* sửa LOG
* sửa PROGRESS
* commit
* tự fix finding

Mục đích của review là **đánh giá độc lập**, không phải vừa review vừa sửa.

---
