from dataclasses import dataclass
from time import time
import math

@dataclass
class EnergyToken:
    task_id: str
    importance: float       # 0..1
    deadline_ms: float      # soft deadline in ms (0 if none)
    predicted_joules: float # forecasted energy for this microtask
    predicted_ms: float     # forecasted wall time for this microtask
    created_ts: float       # epoch seconds

class TokenAllocator:
    def __init__(self, max_quanta_j=5.0, min_quanta_ms=2.0, horizon_ms=250.0):
        self.max_quanta_j   = max_quanta_j
        self.min_quanta_ms  = min_quanta_ms
        self.horizon_ms     = horizon_ms
        self.debt = {}  # task_id -> (+/-) joules error

    def forecast_to_token(self, task_id:str, importance:float, work_units:int,
                          unit_joules:float=0.00005, unit_ms:float=0.05,
                          deadline_ms:float=0.0) -> EnergyToken:
        pj = max(1e-6, work_units * unit_joules)
        pm = max(self.min_quanta_ms, work_units * unit_ms)
        return EnergyToken(task_id, float(importance), float(deadline_ms), float(pj), float(pm), time())

    def _priority(self, tok:EnergyToken, now:float) -> float:
        age_ms = (now - tok.created_ts) * 1000.0
        deadline_term = 0.0
        if tok.deadline_ms > 0:
            slack = max(1.0, tok.deadline_ms - age_ms)
            deadline_term = 1.0 / math.sqrt(slack)  # sooner deadline -> bigger term
        need_term = min(1.0, tok.predicted_joules / self.max_quanta_j)
        imp_term  = tok.importance
        debt_term = min(0.5, max(-0.5, self.debt.get(tok.task_id, 0.0) / self.max_quanta_j))
        # priority ∈ [0, ~2.5]
        return imp_term*1.2 + deadline_term*0.9 + need_term*0.6 + debt_term*0.4

    def settle(self, tok:EnergyToken, actual_joules:float):
        err = actual_joules - tok.predicted_joules
        self.debt[tok.task_id] = self.debt.get(tok.task_id, 0.0) + err
        # light decay toward zero to avoid bias accumulation
        self.debt[tok.task_id] *= 0.9

    def rank(self, tokens:list[EnergyToken]) -> list[EnergyToken]:
        now = time()
        return sorted(tokens, key=lambda t: self._priority(t, now), reverse=True)
