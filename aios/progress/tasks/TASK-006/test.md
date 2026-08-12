# Test — TASK-006

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Kết quả | **233 passed** (26 mới) |
| Coverage | **94.73%** (ngưỡng 80%) |
| Git sạch | ✅ |

Test mới: test_models.py (26 tests — contract 3, mock 8, registry 4, openai 3, ollama 6).

## Lỗi phát hiện + fix (4)
1. **Patch target**: `monkeypatch.setattr(module.urlopen, fake)` sai → phải `setattr(module, "urlopen", fake)` (2-arg vs 3-arg pattern)
2. **Ollama urlopen**: patch target phải là attribute của `ollama_provider` module → `from urllib.request import urlopen` module-level
3. **Fake OpenAI client**: cần đúng shape `client.chat.completions.create`
4. **MockModel fixed**: 1 phần tử responses = fixed (lặp vô hạn), ≥2 = sequence (exhausted sau khi hết)

## Đối chiếu AC (13 AC)
**13/13 PASS** — AC1 Literal role + usage enforce; AC2 mock 8 case + input validate; AC3 calls/metadata; AC4 registry; AC5-6 openai (delenv deterministic + fake client seam); AC7-9 ollama (ConnectionRefused/timeout/mapping/invalid JSON); AC10 settings; AC11 imports; AC12 offline; AC13 RuntimeKernel registry.

## Kết luận
- [x] **TẤT CẢ PASS (13/13 AC)** — sẵn sàng đánh giá cuối.
