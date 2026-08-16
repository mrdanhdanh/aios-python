# TASK-081 — M11-P3: R9 AssetPipeline Contract + R4 Asset Registry + R11 Discovery/Routing

> **Milestone**: M11-P3 (Issue #4) — Asset Capability Architecture (1 slice)
> **Ngày**: 2026-08-16 | **Owner**: AIOS Orchestrator
> **Tham chiếu**: proposal M11 §R9 + §R4 + §R11 + §4 + §7 (M11-P3), PLAN.md §M11

## 1. Mục tiêu

Đóng gap "Capability Registry chỉ backend tools; không có AssetPipeline contract; worker
reimplement primitive thay vì route tới skill có sẵn" (bằng chứng §1b: worker viết PNG encoder
riêng dù `skills/agent-sprite-forge/` đã có). Một architectural slice:

```
AssetPipeline Contract (R9) → Capability Manifest → Asset Capability Registry (R4, kind=asset)
→ Creative Matcher (R11) → Runtime / Orchestrator
```

## 2. Phạm vi (IN)

1. **`backend/src/aios_core/rendering/asset.py`** — `AssetPipeline` contract (R9):
   - `AssetSpec` (pydantic extra=forbid): `kind` (sprite/tileset/map/audio/animation/ui_asset),
     `name`, `params: dict`, `seed: int = 0` (deterministic — worker muốn output khác → đổi seed/params),
     `expected_hash: str = ""` (golden)
   - `AssetOutput` (pydantic): `spec`, `artifact_ref: str`, `sha256: str`, `size: int`,
     `produced_at: str`, `idempotency: AssetOpClass` (tái dùng P1 classifier)
   - `AssetCapability` (pydantic): `id, name, description, kinds: list[str],
     pipeline: AssetPipeline (duck-typed Protocol), version, source` (path tương đối repo)
   - `AssetPipeline` (Protocol): `produce(spec) -> AssetOutput`; pipeline không hỗ trợ kind →
     raise `AssetError` (RuntimeError con) → caller outcome ERROR (fail-closed);
     không khai báo idempotency → at-most-once
2. **`backend/src/aios_core/rendering/registry.py`** — `AssetCapabilityRegistry` (R4, kind=asset):
   - `register(capability)` / `discover(kind) -> list` / `list()` / `get(id)`;
     thread-safe (Lock); in-memory (persist để P4/R5); counters asset_produce_count/asset_failures
   - `default_asset_capabilities()` — khảo sát `skills/` trong repo; nếu
     `skills/agent-sprite-forge/` tồn tại → register capability (kinds: sprite, animation);
     không hard-fail khi skill thiếu
3. **`backend/src/aios_core/rendering/matcher.py`** — `CreativeMatcher` (R11):
   - `match(request: str, kinds: list[str] | None = None) -> list[MatchResult]` — offline-first,
     deterministic scoring: `kind_match*10 + keyword_hit*1 + name_prefix_hit*3`; normalize
     request (lower/strip/token); trả sorted giảm dần + reason; không match → list rỗng (không raise)
   - `suggest(request)` — gợi ý capability đã đăng ký (đóng gap "reuse vs reimplement");
     quét skills/ tự động → P4/R5

## 3. OUT of scope

- R6 Creative Domain trong Decision Pipeline (TASK-082)
- R8 Vendor Integrity (TASK-082), R12 Reference-Asset (TASK-082)
- Plugin/skill thật chạy (chỉ registry + matcher + demo pipeline)
- Sửa Orchestrator chính (4 tầng) — matcher là module riêng, tích hợp sau (R6)

## 4. Input / Output

- **Input**: asset requests (kind + params) từ worker
- **Output**: AssetPipeline contract + AssetCapabilityRegistry + CreativeMatcher + CLI + tests

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | `AssetSpec`/`AssetOutput` contract (extra=forbid, kind enum 6 loại) | unit test |
| AC2 | `AssetPipeline.produce()`: output có sha256 + size + produced_at; raise → AssetError (fail-closed ERROR) | unit test |
| AC3 | `AssetCapabilityRegistry.register/discover/list/get`: discover theo kind đúng | unit test |
| AC4 | Register 2 capability cùng kind → discover trả cả 2 | unit test |
| AC5 | `CreativeMatcher.match("sprite...")` → trả capability sprite trước (điểm cao nhất) | unit test |
| AC6 | `CreativeMatcher.suggest("generate pixel art")` → gợi ý capability/skill tồn tại (offline, không LLM) | unit test |
| AC7 | Registry có capability cho `skills/agent-sprite-forge` (register từ repo nếu tồn tại) | unit test/khảo sát |
| AC8 | Produce dùng `AssetIdempotencyClassifier`: spec không khai báo → at-most-once (fail-closed) | unit test |
| AC9 | CLI `aiagent asset list/discover/match` chạy thật | chạy CLI |
| AC10 | Full suite xanh | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R9/R4/R11 + §4 (Asset Capability Architecture) + §1b (bằng chứng)
- TASK-079 `rendering/idempotency.py` (AssetOpClass)
- `skills/agent-sprite-forge/` (repo)
- M1 `capabilities/` (CapabilityRegistry pattern — mirror)
