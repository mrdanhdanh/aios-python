"""Trajectory evaluation (TASK-032, H4): Final Correct / Trajectory Warning."""

from __future__ import annotations

from .contracts import Trajectory, TrajectoryStep


class TrajectoryEvaluator:
    """Phân tích trajectory: decision → tool → recovery → output."""

    def analyze(self, steps: list[TrajectoryStep]) -> Trajectory:
        if not steps:
            return Trajectory(steps=[], marks={
                "final_correct": False, "trajectory_warning": False,
                "had_recovery": False, "had_denied": False,
                "had_failed_tool": False})
        output_steps = [s for s in steps if s.kind == "output"]
        final_correct = None
        if output_steps:
            last = output_steps[-1]
            final_correct = last.ok is True  # C2-05: step cuối output
        had_denied = any(s.denied for s in steps)
        had_failed_tool = any(s.kind == "tool" and s.ok is False for s in steps)
        had_recovery = any(s.kind == "recovery" for s in steps)
        warning = bool(final_correct and (had_denied or had_failed_tool or had_recovery))
        return Trajectory(
            steps=steps,
            final_correct=final_correct,
            warning=warning,
            marks={"final_correct": bool(final_correct),
                   "trajectory_warning": warning,
                   "had_recovery": had_recovery,
                   "had_denied": had_denied,
                   "had_failed_tool": had_failed_tool},
        )
