from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, os, time

META = {
    "name": "SelfDiagnosticLoop",
    "inputs": [],
    "outputs": ["system.health.metrics"],
    "description": "Reports tick count and observed latency at a controlled interval."
}

class SelfDiagnosticLoop(BaseLoop):
    auto_start = True

    async def init(self):
        # Rate limit for prints / reports (seconds)
        try:
            self.report_interval = float(os.environ.get("HEALTH_REPORT_INTERVAL", "1.0"))
        except Exception:
            self.report_interval = 1.0

        self.ticks = 0
        self.last_report = time.perf_counter()
        print(f"[Init] {self.name} active — interval={self.report_interval:.3f}s")

    async def tick(self, dt: float):
        """
        Called by Supervisor once per scheduler sweep.
        We rate-limit logs and always yield to avoid runaway printing.
        """
        self.ticks += 1
        now = time.perf_counter()
        should_report = (now - self.last_report) >= self.report_interval

        # Always yield: never spin
        await asyncio.sleep(1.0)

        if should_report:
            self.last_report = now
            # Compute a stable latency estimate (bounded)
            est = max(0.0, float(dt))
            msg = f"[Health] ticks={self.ticks} latency≈{est:.3f}s alerts=0"
            print(msg)

            # Publish a compact metrics event (non-blocking if bus exists)
            bus = get_bus()
            if bus:
                await bus.publish("system.health.metrics", {
                    "ticks": self.ticks,
                    "latency": est,
                    "ts": time.time()
                })

        return {
            "id": self.name,
            "latency": float(dt),
            "ticks": self.ticks,
            "timestamp": time.time()
        }

