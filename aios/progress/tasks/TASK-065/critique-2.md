# TASK-065 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P1) — Process chết phải chứng minh "không entire execution lost"
Mô phỏng crash-point raise → resume từ checkpoint — nhưng resume phải qua state service thật (ExecutionService resume/snapshot) không phải mock.
→ **Resolve**: Scenario process_chết dùng `ExecutionService` thật (2-node workflow): chạy node1 → crash (raise) → `resume()` từ state → node2 chạy; assert node1 KHÔNG chạy lại (event count).

### C2-02 (P2) — Worker timeout vs Resource hết phải khác nhau
Timeout = execution chạy quá hạn → cancel; Resource hết = acquire fail → queue/reject.
→ **Resolve**: worker_timeout: fault = node runner sleep vượt timeout → assert cancel + FAILED event; resource: fault = ResourceService grant False → assert queue/reject path (acquire_slot non-blocking False → scenario outcome recovered=True khi release sau đó).

### C2-03 (P3) — Network mất mô phỏng bằng gì?
Không gọi REST thật (offline). → **Resolve**: REST tool stub `_run` raise ConnectionError khi flag network_down=True (test double qua Tool subclass) — không sửa tools/rest_tool.py.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
