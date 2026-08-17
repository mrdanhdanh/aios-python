# ADR-0008: Harness Trust Architecture — System Readiness ≠ Harness Trust

- **Status**: accepted
- **Date**: 2026-08-18
- **Extends**: [ADR-0004](0004-architecture-invariants.md) (architecture invariants, INV-017..021), [ADR-0007](0007-compatibility-migration-policy.md) (compatibility policy)
- **Milestone**: M13 — Harness Trust & Behavioral Conformance (Issue #8)

## Context

M13-P0 (TASK-089)建立了 Behavioral Conformance engine，M13-P1 (TASK-090)建立了 Harness Coverage model 9维度 + Readiness scoring，M13-P2 (TASK-091)建立了 Meta-Harness verify-the-verifier，M13-P3 (TASK-092)建立了 Release Gate。

但缺少一个**正式的架构决策**来定义：(1) System Readiness 和 Harness Trust 是两个独立概念；(2) Release Gate 如何组合它们；(3) 4个贯穿 Harness Track 的不变量如何实施。

本 ADR 将这些设计决策固定下来，以便后续 M14 (Controlled Self-Healing) 和 M15 (Autonomous Harness) 可以在此基础上构建。

## Decision

### 1. 两个独立分数

**System Readiness** 和 **Harness Trust** 是两个**独立的、不可互换的**概念：

| 概念 | 来源 | 测量什么 | 状态枚举 |
|------|------|----------|----------|
| System Readiness | `HarnessReadinessReport` (CoverageHarness) | 系统覆盖度和就绪程度 | `READY` / `NOT_READY` |
| Harness Trust | `MetaReport` (MetaHarness) | 验证器本身是否可信 | `PASS` / `FAIL` |

**关键设计原则**：Release Gate 是 pure combiner — 它**不知道**如何计算 readiness 或 trust，只组合两个已计算的报告。这确保了真正的分离。

### 2. Release Gate (fail-closed)

```
Release Gate = PASS  iff  (System Readiness == READY)  AND  (Harness Trust == PASS)
             = BLOCKED  otherwise
```

- **fail-closed**: 任何异常 → BLOCKED（不 crash，不返回 PASS）
- **子 harness 失败** → try/except → BLOCKED（永远有 verdict）
- **CLI**: `aiagent harness release` → JSON document + exit 0 (PASS) / 1 (BLOCKED)

### 3. 4个贯穿不变量

M13 建立了 Harness Track 的 4 个贯穿不变量：

| 不变量 | 状态 | 实施位置 |
|--------|------|----------|
| **FAIL-CLOSED** | ✅ M13 已建立 | INV-035 + Release Gate + Meta-Harness |
| **INDEPENDENT VERIFICATION** | ✅ M13 已建立 | Meta-Harness 独立 oracle (hardcode) + Release Gate combiner |
| **PERMISSION BOUNDARY** | 📋 M14 | Permission Broker + Human Approval |
| **CERTIFIED BASELINE/ROLLBACK** | 📋 M14 | Certified Baseline + Rollback |

### 4. 反循环设计

Meta-Harness 使用**硬编码 oracle**（MetaOracle enum）来计算 expected_state — 它**不调用**生产验证器来确定预期结果。这确保了验证路径的独立性。

```
Production verifier → Meta test oracle → Expected invariant (hardcoded)
```

剩余的循环性（oracle 与 spec 来源相同）已记录；M16 (dsh) 是真正的独立路径。

### 5. Pipeline

```
Execute → Verify → Behavioral Conformance → Meta-Verify →
Measure Coverage → Establish Harness Trust → Release Gate
```

## Consequences

- **Positive**: 
  - 真正的分离 — readiness 和 trust 是独立计算的，不能互相替代
  - Release Gate 是 pure combiner — 容易测试、容易替换、容易推理正确性
  - Fail-closed — 任何异常都导致 BLOCKED，永远不会误报 PASS
  - 4 个贯穿不变量提供了清晰的安全框架
- **Negative**:
  - 需要维护两套独立的评分系统（readiness + trust）
  - Release Gate 本身不添加新的验证逻辑 — 它只是组合器
- **Known limitation**: Oracle 硬编码意味着 Meta-Harness 的"独立性"是逻辑上的（不同代码路径），而不是真正的独立来源。M16 (dsh) 将提供真正的独立验证路径。
