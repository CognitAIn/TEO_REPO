from dataclasses import dataclass, field
from typing import Dict, Any, List
import time

@dataclass
class EnergyToken:
    kind: str
    budget: float
    ttl: float
    meta: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    def alive(self) -> bool:
        return (time.time() - self.created_at) < self.ttl and self.budget > 0

@dataclass
class HoloFrame:
    id: int
    context: Dict[str, Any]
    predicted_load: Dict[str, float]
    sync_delta: Dict[str, float]
    tokens: List[EnergyToken] = field(default_factory=list)
    def allocate(self, kind: str, amount: float) -> float:
        need = amount; granted = 0.0
        for t in self.tokens:
            if t.kind == kind and t.alive() and t.budget > 0:
                take = min(need, t.budget)
                t.budget -= take
                granted += take
                need -= take
                if need <= 0: break
        return granted
