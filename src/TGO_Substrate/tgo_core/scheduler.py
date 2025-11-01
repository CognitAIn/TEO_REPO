import asyncio, time
from typing import Dict, Any
from .tokens import HoloFrame, EnergyToken

class HoloframeScheduler:
    def __init__(self, cfg: dict, telemetry, governor):
        self.cfg = cfg; self.telemetry = telemetry; self.governor = governor
        self.frame_id = 0; self.last_burst_ts = 0.0
        self.cooldown_s = self.cfg['safety']['min_cooldown_s']
    async def run_forever(self):
        interval = self.cfg['loop']['tick_s']
        while True:
            sys = self.telemetry.read_system()
            frame = self._predict_next_frame(sys)
            self._pre_allocate(frame)
            await self._maybe_burst(frame, sys)
            await asyncio.sleep(interval)
    def _predict_next_frame(self, sys: Dict[str, Any]) -> HoloFrame:
        self.frame_id += 1
        predicted = {'cpu': 0.3 if sys.get('cpu_percent', 50) <= 60 else 0.5,
                     'gpu': 0.5 if sys.get('cpu_percent', 50) <= 60 else 0.3,
                     'io': 0.2}
        tokens = [EnergyToken('cpu', self.cfg['tokens']['cpu_budget'], self.cfg['tokens']['ttl_s']),
                  EnergyToken('gpu', self.cfg['tokens']['gpu_budget'], self.cfg['tokens']['ttl_s']),
                  EnergyToken('io',  self.cfg['tokens']['io_budget'],  self.cfg['tokens']['ttl_s'])]
        return HoloFrame(self.frame_id, {'hint':'next-holoframe'}, predicted, {'cpu':0.0,'gpu':0.0,'io':0.0}, tokens)
    def _pre_allocate(self, frame: HoloFrame):
        _ = frame.allocate('cpu', 0.05); _ = frame.allocate('gpu', 0.05); _ = frame.allocate('io', 0.02)
    async def _maybe_burst(self, frame: HoloFrame, sys: Dict[str, Any]):
        now = time.time()
        self.cooldown_s = self.governor.adaptive_cooldown()
        if (now - self.last_burst_ts) < self.cooldown_s: return
        if not self.governor.can_fire(frame, sys): return
        granted_cpu = frame.allocate('cpu', self.cfg['bursts']['cpu_grant'])
        granted_gpu = frame.allocate('gpu', self.cfg['bursts']['gpu_grant'])
        granted_io  = frame.allocate('io',  self.cfg['bursts']['io_grant'])
        await self.governor.fire_burst(granted_cpu, granted_gpu, granted_io)
        self.last_burst_ts = now
