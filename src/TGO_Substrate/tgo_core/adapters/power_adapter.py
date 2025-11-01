from typing import Dict, Any
class PowerAdapter:
    def __init__(self, cfg: dict): self.cfg = cfg
    def read_power(self) -> Dict[str, Any]:
        return {'cpu_watts': None, 'dram_watts': None}
    def burst_limit(self, delta_watts: float, duration_ms: int) -> None:
        return
    def rollback(self) -> None:
        return
