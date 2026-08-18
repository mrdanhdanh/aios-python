# TASK-094 — Critique vòng 1

## P1 — normalize_message quá yếu?

**Phát hiện**: normalize_message chỉ strip timestamps/uuids/paths. Nếu error message chứa dữ liệu biến động khác (số dòng code, memory address, hex values), signature sẽ thay đổi → corpus bị phân mảnh.

**Giải pháp**: Mở rộng normalize_message: strip hex patterns (0x...), line numbers (line \d+), memory addresses. Hoặc dùng regex broad hơn: `<any_numeric>` → `<N>`. Spec §3.2 đã ghi "normalized (no timestamps/uuids/paths)" — bổ sung thêm hex/addresses.

## P2 — Component localization dựa trên string matching có đủ không?

**Phát hiện**: Nếu error message không chứa module path, component sẽ là "unknown" → useless cho P1 candidate generate.

**Giải pháp**: Fallback strategy: (1) extract từ error message regex; (2) extract từ HarnessEvent messages (phase); (3) default "unknown" + severity LOW. Acceptable cho v1 — P1 sẽ improve khi có dữ liệu thật.

## P3 — FailureCorpusReport.recent = 10 — hard-coded?

**Phát hiện**: Nếu corpus < 10, recent sẽ ngắn hơn. Không có parameter để điều chỉnh.

**Giải pháp**: Acceptable cho v1. Có thể thêm `recent_limit` parameter sau. Không blocker.

## Kết luận vòng 1

2 điểm chính (P1: normalize strength, P2: localization fallback) đã resolve bằng cách mở rộng regex + fallback strategy. P3 acceptable. Spec → v1.1.
