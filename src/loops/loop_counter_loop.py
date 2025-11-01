from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, time

META = {
    "name": "LoopCounterLoop",
    "inputs": [],
    "outputs": ["system.health.snapshot"],
    "description": "Reports counts from both GLOBAL_BUS and Supervisor loop registry."
}

class LoopCounterLoop(BaseLoop):
    auto_start = True

    async def init(self):
        self.last_report = 0
        self.interval = 5.0
        print(f"[Init] {self.name} active — comparing Supervisor and GLOBAL_BUS.")

    async def tick(self, dt):
        await asyncio.sleep(0)
        bus = get_bus()
        bus_count = 0
        sup_count = 0
        now = time.time()

        try:
            if bus and hasattr(bus, "subscribers"):
                bus_count = len(bus.subscribers)

            # new: pull from supervisor_ref bound in Trinity_STEM.py
            sup = getattr(bus, "supervisor_ref", None)
            if sup and hasattr(sup, "loops"):
                sup_count = len(sup.loops)

            total = sup_count or bus_count

            if now - self.last_report >= self.interval:
                self.last_report = now
                print(f"[SyncCheck] expected={bus_count}  reported={bus_count}  total={total}  Δt={dt:.3f}s  uptime={now:.1f}")
                if bus:
                    await bus.publish("system.health.snapshot", {
                        "timestamp": now,
                        "bus_loops": bus_count,
                        "supervisor_loops": sup_count,
                        "total": total,
                        "delta_t": dt
                    })

            return {
                "id": self.name,
                "latency": dt,
                "bus_loops": bus_count,
                "supervisor_loops": sup_count,
                "timestamp": now
            }

        except Exception as e:
            return {"id": self.name, "error": str(e), "timestamp": time.time()}
