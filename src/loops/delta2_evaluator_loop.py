from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, time, statistics
from collections import deque

META = {
    "name": "Delta2EvaluatorLoop",
    "inputs": ["system.health.snapshot"],
    "outputs": ["system.delta.metrics", "system.delta.alert"],
    "description": "Δ2 evaluator: computes drift/variance/trend from health snapshots and emits stability score."
}

class Delta2EvaluatorLoop(BaseLoop):
    auto_start = True

    async def init(self):
        self.target_dt = 1.0     # expected inter-beat interval from SelfDiagnostic/Heartbeat
        self.buf_size = 30       # rolling window for stats
        self.samples = deque(maxlen=self.buf_size)
        self.ewma = None
        self.last_score = None
        self.alerts = 0

        bus = get_bus()
        if bus:
            bus.subscribe("system.health.snapshot", self._on_health)
        print(f"[Init] {self.name} watching system.health.snapshot (window={self.buf_size})")

    async def _on_health(self, msg: dict):
        """
        Expected shape (already emitted by your loops):
          { "timestamp": ..., "loop_count": int, "delta_t": float, ... }
        """
        dt = msg.get("delta_t")
        if dt is None:
            return
        self.samples.append(float(dt))

        # EWMA update (smooth drift estimate)
        alpha = 0.2
        if self.ewma is None:
            self.ewma = dt
        else:
            self.ewma = (1 - alpha) * self.ewma + alpha * dt

        # Compute metrics if we have enough data
        if len(self.samples) >= max(5, int(self.buf_size * 0.5)):
            drift = self.ewma - self.target_dt
            try:
                var = statistics.pvariance(self.samples)
                stdev = var ** 0.5
            except statistics.StatisticsError:
                var = 0.0
                stdev = 0.0

            # Simple monotonic trend via last and first in window
            trend = (self.samples[-1] - self.samples[0]) / max(1, len(self.samples)-1)

            # Stability score: 1.0 is perfect; penalize drift + jitter
            # Tunable weights:
            w_drift = 2.0
            w_jitter = 1.0
            raw_penalty = (w_drift * abs(drift)) + (w_jitter * stdev)
            score = max(0.0, 1.0 - raw_penalty)

            self.last_score = score

            out = {
                "timestamp": time.time(),
                "target_dt": self.target_dt,
                "ewma_dt": round(self.ewma, 6),
                "drift": round(drift, 6),
                "stdev": round(stdev, 6),
                "trend_per_step": round(trend, 6),
                "score": round(score, 6),
                "n": len(self.samples),
            }

            bus = get_bus()
            if bus:
                await bus.publish("system.delta.metrics", out)

                # Alert if we’re drifting far or jittering hard
                if abs(drift) > 0.15 or stdev > 0.08:
                    self.alerts += 1
                    await bus.publish("system.delta.alert", {
                        "timestamp": out["timestamp"],
                        "reason": "resonance_out_of_bounds",
                        "drift": out["drift"],
                        "stdev": out["stdev"],
                        "score": out["score"],
                        "n": out["n"],
                    })

    async def tick(self, dt):
        # keep this loop featherweight; all heavy work is event-driven
        await asyncio.sleep(0)
        return {
            "id": self.name,
            "latency": dt,
            "score": self.last_score,
            "samples": len(self.samples),
            "alerts": self.alerts,
            "timestamp": time.time(),
        }
