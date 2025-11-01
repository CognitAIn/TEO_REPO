from typing import Optional
try:
    import psutil, os
except Exception:
    psutil = None; os = None
class OSAdapter:
    def __init__(self, cfg: dict): self.cfg = cfg
    def process_info(self, pid: Optional[int] = None):
        if psutil is None: return None
        if pid is None: pid = psutil.Process().pid
        p = psutil.Process(pid)
        return {'pid': pid, 'name': p.name(), 'cpu_percent': p.cpu_percent(interval=None),
                'mem_mb': p.memory_info().rss // (1024*1024)}
    def set_priority_soft(self, pid: Optional[int], delta_levels: int):
        return
