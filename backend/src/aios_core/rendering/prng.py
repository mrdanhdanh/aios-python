"""SeededPrng — mulberry32 (M11-P1, TASK-079).

Deterministic PRNG: cùng seed → cùng chuỗi số (cross-version ổn định,
tự implement, không dependency). Dùng cho particles/fx trong render
thuần — bắt buộc cho pixel-stable replay.
"""

from __future__ import annotations


def _mulberry32_next(state: list[int]) -> float:
    """Một bước mulberry32 — trả float [0, 1).

    Đúng chuẩn JS reference: `t = t + imul(t ^ t>>>7, 61|t) ^ t` —
    XOR với t CŨ (trước khi cộng).
    """
    state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
    t = state[0]
    t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
    t_old = t
    t_new = (t_old + ((t_old ^ (t_old >> 7)) * (t_old | 61))) & 0xFFFFFFFF
    t = t_new ^ t_old
    return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


class SeededPrng:
    """PRNG seeded — mulberry32, thuần (không IO), deterministic."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed) & 0xFFFFFFFF
        self._state = [self.seed]

    def next(self) -> float:
        """Số tiếp theo trong [0, 1)."""
        return _mulberry32_next(self._state)

    def next_int(self, low: int, high: int) -> int:
        """Số nguyên trong [low, high] (inclusive)."""
        if high < low:
            raise ValueError("high must be >= low")
        return low + int(self.next() * (high - low + 1))

    def sequence(self, n: int) -> list[float]:
        """n số liên tiếp — deterministic theo seed."""
        return [self.next() for _ in range(n)]


#: Test vector cố định (C2-04): seed=1 → dãy đầu phải khớp (cross-version).
KNOWN_VECTOR: dict[int, list[float]] = {
    1: [
        0.6270739405881613,
        0.002735721180215478,
        0.5274470399599522,
        0.9810509674716741,
        0.9683778982143849,
    ],
}
