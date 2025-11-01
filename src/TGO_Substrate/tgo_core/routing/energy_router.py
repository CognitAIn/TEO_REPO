from __future__ import annotations
from typing import Callable, Dict, List
from dataclasses import dataclass

@dataclass
class Budget:
    task_id: str
    device: str
    allow_ms: float   # time window allowed now
    hint_watts: float # approximate power expectation (optional)

class EnergyRouter:
    """
    Converts ranked tokens into per-backend time budgets.
    Works even if telemetry funcs return None (estimation mode).
    """
    def __init__(self,
                 backends: Dict[str, dict],
                 get_telemetry: Dict[str, Callable[[], dict]]|None = None,
                 frame_ms: float = 100.0):
        self.backends = backends or {}
        self.get_telemetry = get_telemetry or {}
        self.frame_ms = frame_ms

    def _capacity(self, name:str) -> float:
        """
        Returns [0..1] instantaneous capacity fraction for a backend.
        Falls back to 0.5 if unknown.
        """
        fn = self.get_telemetry.get(name)
        if not fn:
            return 0.5
        try:
            t = fn() or {}
            util = float(t.get("utilization", 50.0))  # %
            # more free capacity when utilization is lower
            free = max(0.0, 100.0 - util) / 100.0
            return 0.2 + 0.8*free  # bias to avoid zero
        except Exception:
            return 0.5

    def route(self, ranked_tokens) -> List[Budget]:
        # compute weights per backend
        caps = {k: self._capacity(k) for k in self.backends.keys()}
        total_cap = sum(caps.values()) or 1.0
        shares = {k: self.frame_ms * (v/total_cap) for k,v in caps.items()}

        budgets: List[Budget] = []
        # simple round-robin by backend share
        cur = {k:0.0 for k in shares.keys()}
        order = list(self.backends.keys()) or ["cpu"]

        i = 0
        for tok in ranked_tokens:
            dev = order[i % len(order)]
            slot_left = max(0.0, shares[dev] - cur[dev])
            allow = min(max(2.0, tok.predicted_ms), slot_left if slot_left>0 else shares[dev]*0.25)
            budgets.append(Budget(task_id=tok.task_id, device=dev, allow_ms=float(allow), hint_watts=0.0))
            cur[dev] += allow
            i += 1
        return budgets
