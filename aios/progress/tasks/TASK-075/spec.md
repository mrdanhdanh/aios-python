# TASK-075 — M10-F7: Performance & Cost + Model Independence

## Mục tiêu
PLAN §M10-35: đo `latency · throughput · LLM cost · tool cost · memory · storage · concurrency` + dashboard `Cost/Goal · Cost/Workflow · Cost/Agent · Cost/Tool · Cost/Success`. Model Provider Contract độc lập: `AIOS → OpenAI | Ollama | Mock | Other` (KHÔNG thành OpenAI wrapper).

## Phạm vi
- `observability/performance.py`:
  - `PerformanceMetrics`: từ MetricsService — latency (avg workflow/tool ms), throughput (completed/time window), concurrency (max running từ events), memory/storage (artifact dir size — đo qua du) 
  - `CostEstimator`: model cost = tokens_in/1M*input_cost + tokens_out/1M*output_cost (ModelCapability) + tool cost (counter) — aggregate: cost_per_workflow, cost_per_agent, cost_per_tool, cost_per_success (cost/success count), cost_per_goal (goal tasks)
  - `CostDashboard`: tổng hợp theo chiều Goal/Workflow/Agent/Tool/Success
- CLI: `aiagent cost` (Cost/Goal/Workflow/Agent/Tool/Success) + `aiagent performance` (latency/throughput/concurrency)
- Model independence: test ModelProviderContract — Mock/OpenAI/Ollama đều implement ModelContract (đã có) — test "AIOS không phụ thuộc provider cụ thể" qua registry swap

## Ngoài phạm vi
- Không đo token thật từ LLM (offline) — dùng estimate từ ModelCapability + token count giả lập (injectable)
- Không billing

## Input
- `observability/metrics.py`, `models/capability.py` (ModelCapability costs), `models/base.py` (ModelContract), `config.py`

## Output
- `backend/src/aios_core/observability/performance.py` + CLI + `tests/test_performance.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | PerformanceMetrics: latency avg (workflow/tool), throughput, concurrency max — từ dữ liệu thật/injectable | Test |
| AC2 | CostEstimator: model cost đúng công thức (tokens/1M × cost) + tool cost | Test |
| AC3 | Aggregate theo Workflow/Agent/Tool/Success/Goal — không crash khi DB rỗng | Test |
| AC4 | Cost/Success = total_cost / success_count (0 success → SKIPPED) | Test |
| AC5 | `aiagent cost` in 5 chiều | CLI thật |
| AC6 | `aiagent performance` in latency/throughput/concurrency | CLI thật |
| AC7 | Model independence: 3 provider (Mock/OpenAI/Ollama) đều là ModelContract + registry swap không đổi API dùng | Test |
| AC8 | Regression full suite | pytest |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- Token estimate: injectable `token_fn(request) -> (in, out)` — mặc định 0 (offline); test inject số liệu.
- ModelProviderContract test: class methods chung (chat, metadata, name, is_available) — mock/openai/ollama đều pass.
