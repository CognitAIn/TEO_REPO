from typing import Dict, Any
import time
try:
    import psutil
except Exception:
    psutil = None

class Telemetry:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.sample = {}
    def read_system(self) -> Dict[str, Any]:
        now = time.time()
        data = {'ts': now}
        if psutil:
            vm = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=None)
            freq = psutil.cpu_freq()
            disk = psutil.disk_io_counters(perdisk=False) if hasattr(psutil, 'disk_io_counters') else None
            data.update({
                'cpu_percent': cpu,
                'cpu_freq_mhz': getattr(freq, 'current', None),
                'ram_used_mb': (vm.used // (1024*1024)),
                'ram_free_mb': (vm.available // (1024*1024)),
                'disk_read_mb': getattr(disk, 'read_bytes', 0) / (1024*1024) if disk else None,
                'disk_write_mb': getattr(disk, 'write_bytes', 0) / (1024*1024) if disk else None,
            })
        self.sample = data
        return data
