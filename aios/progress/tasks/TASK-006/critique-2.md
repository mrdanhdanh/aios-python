# Critique vòng 2 — TASK-006

## Đánh giá chung
Phần lớn resolution v1 áp đúng. Nhưng 2 P1 (chat() thứ tự check với fake client; Yêu cầu #6 stale timeout 1s) + 3 P2 + 10 P3. **Sẵn sàng: 3/5 — sửa trước khi implement.**

## Vấn đề + Resolution

### P1-A — Thứ tự check chat() OpenAI với fake client chưa định nghĩa (AC6 có thể fail)
- **Resolution**: `chat()`: `client is not None` → dùng trực tiếp (bypass is_available — seam là quyền caller); ngược lại: `not is_available()` → ModelNotAvailableError, rồi lazy-build client. AC6 test độc lập openai-installed.

### P1-B — Yêu cầu #6 stale (timeout 1s hardcode) mâu thuẫn Phạm vi #4
- **Resolution**: sửa Yêu cầu #6: `__init__(..., timeout: float = 30.0)`; is_available() dùng self.timeout (bỏ hardcode 1s).

### P2-A — Ollama chat() khi server down: map URLError(ConnectionRefusedError)/gaierror → ModelNotAvailableError; HTTPError khác → ModelError; thêm nhánh test AC9.
### P2-B — Pin patch target: implementation gọi qua `import urllib.request; urllib.request.urlopen(...)`; test patch `aios_core.models.ollama_provider.urlopen`; `_is_openai_installed` patch tại `aios_core.models.openai_provider._is_openai_installed`.
### P2-C — Mock usage = `{"prompt_tokens": n, "completion_tokens": n}` (n = len(output)//4); ChatResponse là điểm enforce duy nhất (validator fill thiếu = 0, âm → ValidationError); AC2 thêm assert calls + usage.

### P3 — (áp)
1. Yêu cầu #5 đồng bộ Phạm vi #3 (client/timeout/base_url)
2. Template-method validate: base `chat()` validate → `_chat()` abstract
3. AC9 thêm nhánh URLError(reason=socket.timeout) → ModelTimeoutError
4. Mô tả shape fake client/response tối thiểu trong spec
5. Bỏ default_registry() helper — chỉ dùng Container (AC13); test registry instance mới
6. metadata() convention: id="models.mock", name="mock", version="0.1.0"
7. Registry không auto-register mock (chỉ RuntimeKernel); test AC4 tự pre-register
8. Phụ thuộc sửa: Settings pattern từ TASK-002
9. AC12 "git sạch" → yêu cầu quy trình (ghi chú)
10. Mock edge: responses=[] → raise exhausted; echo + responses cùng set → echo ưu tiên (ghi rõ)

## Kết luận
- [x] **Resolve toàn bộ (2 P1 + 3 P2 + 10 P3)** — cập nhật spec, sẵn sàng implement.
