# TASK-067 — Evaluation

## Đối chiếu AC — 9/9 ĐẠT (xem test.md)

## Giá trị
- Autonomy Safety = lớp bắt buộc giữa Autonomous Loop và execution — biến INV-030 thành runtime enforcement thật.
- Risk classifier + ASK_HUMAN mặc định cho hành động cao rủi ro — nền cho Gate E.

## Bài học
1. Class-scope trong lambda/closure dễ gây NameError (test) — dùng SimpleNamespace/dataclass.
2. Chain fail sớm vẫn phải để evidence (risk/governor) — audit cần dấu vết đầy đủ.

## Đề xuất (P3)
- Wire SafetyEnforcer vào Autonomy Loop (M9) như gate mặc định trong governor.check_action.
