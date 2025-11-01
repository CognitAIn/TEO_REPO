
import asyncio, importlib, inspect, os, time, importlib.util, sys
from typing import Dict, Any, List, Callable

# ─────────────────────────────────────────────
# Event Bus
# ─────────────────────────────────────────────
class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, cb: Callable):
        self.subscribers.setdefault(topic, []).append(cb)

    async def publish(self, topic: str, data: Any):
        for cb in self.subscribers.get(topic, []):
            # Support async or sync callbacks
            if inspect.iscoroutinefunction(cb):
                await cb(data)
            else:
                res = cb(data)
                if inspect.isawaitable(res):
                    await res

# Global bus (available to loops via get_bus)
GLOBAL_BUS = None
def get_bus():
    return GLOBAL_BUS

# ─────────────────────────────────────────────
# Base Loop
# ─────────────────────────────────────────────
class BaseLoop:
    """
    Base loop with Δ+1 phase-awareness and invariant tracking.
    """
    def __init__(self, name=None, bus=None):
        self.name = name or self.__class__.__name__
        self.bus = bus
        self.phase_tag = 0
        self.depends_on = []
        self.phase_offset_ok = True
        self.latency_ewma = 0.0
        self.recovery_ms = 0.0
        self.last_tick = time.time()
        self.canary_mode = False
        self.initialized = False

    async def init(self):
        self.initialized = True
        self.last_tick = time.time()

    async def tick(self, dt):
        now = time.time()
        elapsed = now - self.last_tick
        self.last_tick = now

        self.phase_offset_ok = abs((self.phase_tag or 0) - (int(dt * 1000) % (self.phase_tag + 1))) < 1e-3
        alpha = 0.1
        self.latency_ewma = (1 - alpha) * self.latency_ewma + alpha * dt

        import random, asyncio
        if random.random() < 0.001:
            start = time.time()
            await asyncio.sleep(0.01)
            self.recovery_ms = (time.time() - start) * 1000

        await asyncio.sleep(max(0.1 - dt, 0))

        return {
            "id": self.name,
            "phase": self.phase_tag,
            "phase_ok": self.phase_offset_ok,
            "latency": dt,
            "latency_ewma": round(self.latency_ewma, 5),
            "recovery_ms": round(self.recovery_ms, 3),
            "timestamp": now
        }

    def snapshot(self) -> Dict[str, Any]:
        return {"name": self.name, "state": self.state}

    def recover(self, desc: Dict[str, Any]):
        self.state = desc.get("state", {})

# ─────────────────────────────────────────────
# Supervisor
# ─────────────────────────────────────────────
class Supervisor:
    def __init__(self, buffer_seconds: float = 0.10):
        self.buffer_seconds = buffer_seconds
        self.bus = EventBus()
        # expose global bus
        global GLOBAL_BUS
        GLOBAL_BUS = self.bus

        self.loopdir = os.path.dirname(__file__)
        self.loops: List[BaseLoop] = []
        self.state_cache: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()

        # basic console controls
        self._paused = False
        self.bus.subscribe("system.control.pause", self._on_pause)
        self.bus.subscribe("system.control.resume", self._on_resume)

    async def _on_pause(self, _):
        self._paused = True
        print("[System] Paused")

    async def _on_resume(self, _):
        self._paused = False
        print("[System] Resumed")

    async def discover_loops(self):
        loaded_names = set()
        for f in os.listdir(self.loopdir):
            if not f.endswith(".py"): 
                continue
            if f in ("Trinity_STEM.py", "__init__.py"):
                continue
            modname = f"loops.{f[:-3]}"
            try:
                mod = importlib.import_module(modname)
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, BaseLoop) and obj is not BaseLoop:
                        if obj.__name__ in loaded_names:
                            continue
                        loaded_names.add(obj.__name__)
                        inst = obj(obj.__name__)
                        self.loops.append(inst)
                        print(f"[Load] {obj.__name__}")
            except Exception as e:
                print(f"[Error loading {f}]: {e}")

    async def _tick_one(self, lp: BaseLoop):
        """
        Execute one loop tick, measuring:
          - dt_period: seconds since last tick (scheduler period)
          - work_latency_ms: actual time spent inside lp.tick
        """
        try:
            now = time.monotonic()
            dt_period = now - lp.last_tick if lp.last_tick else 0.0

            t0 = time.perf_counter()
            result = await lp.tick(dt_period)
            work_latency_ms = (time.perf_counter() - t0) * 1000.0

            lp.last_tick = now

            # Normalize result dict
            if not isinstance(result, dict):
                result = {}
            result.setdefault("id", lp.name)
            result["period"] = dt_period
            result["work_latency_ms"] = work_latency_ms
            result.setdefault("timestamp", time.time())

            self.state_cache[lp.name] = result
            await self.bus.publish("system.metrics", result)
        except Exception as e:
            print(f"[Restart] {lp.name}: {e}")
            lp.recover(lp.snapshot())

    async def _compose(self):
        # Heartbeat: compute averages over work_latency_ms if present
        n = len(self.state_cache)
        if n == 0:
            print(f"[Heartbeat] 0 loops | avg latency n/a | uptime {time.time() - self.start_time:.1f}s")
            return
        lat_vals = []
        for v in self.state_cache.values():
            if "work_latency_ms" in v:
                lat_vals.append(v["work_latency_ms"] / 1000.0)  # seconds
            elif "latency" in v:
                lat_vals.append(float(v["latency"]))
        avg_lat = sum(lat_vals) / max(len(lat_vals), 1)
        print(f"[Heartbeat] {n} loops | avg latency {avg_lat:.4f}s | uptime {time.time() - self.start_time:.1f}s")

    async def run(self):
        print("[Supervisor] Trinity_STEM node active.")
        await self.discover_loops()

        # Initialize all loops
        for lp in self.loops:
            try:
                await lp.init()
            except Exception as e:
                print(f"[InitError] {lp.name}: {e}")

        # Main scheduler loop
        while True:
            t_cycle = time.monotonic()

            # tick all loops (respect pause)
            if not self._paused:
                await asyncio.gather(*(self._tick_one(lp) for lp in self.loops))

            # compose heartbeat
            await self._compose()

            # pace the scheduler to ~buffer_seconds
            elapsed = time.monotonic() - t_cycle
            await asyncio.sleep(max(self.buffer_seconds - elapsed, 0))

# ─────────────────────────────────────────────
# Entry point convenience (if run as a script)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(Supervisor(buffer_seconds=0.10).run())
    except KeyboardInterrupt:
        print("\n[Supervisor] Graceful shutdown.")





