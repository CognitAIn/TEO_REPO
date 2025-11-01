from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, time

META = {
    "name": "HeartbeatLoop",
    "outputs": ["system.heartbeat.tick"],
    "description": "Primary timing source for all loop synchronization."
}

class HeartbeatLoop(BaseLoop):
    auto_start = True

    async def init(self):
        self.interval = 1.0  # 1 second between pulses
        self.last_beat = time.time()
        print(f"[Init] {self.name} active — interval={self.interval:.3f}s")

    async def tick(self, dt):
        now = time.time()
        delta = now - self.last_beat
        if delta >= self.interval:
            self.last_beat = now
            bus = get_bus()
            if bus:
                await bus.publish("system.heartbeat.tick", {
                    "timestamp": now,
                    "interval": self.interval,
                    "delta": delta
                })
            print(f"[Heartbeat] Δ={delta:.3f}s | t={now:.1f}")
        await asyncio.sleep(0)
        return {"id": self.name, "delta": delta, "timestamp": now}
