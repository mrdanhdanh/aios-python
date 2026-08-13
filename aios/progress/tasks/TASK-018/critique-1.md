# Critique vòng 1 — TASK-018 (Dashboard SPA)

> 2026-08-13 | critic subagent | Spec: spec.md

## Đánh giá: 2.5/5 — cần sửa (2 P1 + 4 P2 + P3)

## Vấn đề + resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | P1 | /conversations không session_id → luôn rỗng | MemoryView gọi `?session_id=api` (khớp chat hardcode) |
| C1-02 | P1 | 3 dạng error envelope | api.ts: parse body.error (dù status) → body.detail → statusText; thiếu data → format error; AC3 cover 3 dạng |
| C1-03 | P2 | WS frame = raw event dict (không wrapper) | Pin: frame = `{id,type,timestamp,source,payload}` |
| C1-04 | P2 | Proxy cần ws:true; chiến lược URL | Dev: relative `/api` + proxy `ws:true`; VITE_API_BASE chỉ production |
| C1-05 | P2 | Test plan thiếu deps + WebSocket stub | Thêm @testing-library/react, jest-dom, jsdom; setup.ts stub global WebSocket + fetch |
| C1-06 | P2 | ArtifactBrowser không có detail endpoint | View chỉ list (không detail) — ghi Out |

## Kết luận
- [x] Resolved 6/6 — spec đã cập nhật; vòng 2 tự verify qua implement + test thật (vitest).
