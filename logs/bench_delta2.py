import asyncio, time, statistics, sys, math, random

TARGET_DT = 0.20      # target tick (s)
DURATION  = 20.0      # per mode (s)
REPORT_EVERY = 2.0    # live report cadence

def jitter():
    # bounded jitter with occasional burst
    base = random.uniform(-0.030, 0.030)    # ±30ms
    if random.random() < 0.05:
        base += random.uniform(-0.040, 0.040)  # 5% chance ±40ms extra
    return base

class ModeStats:
    def __init__(self, name):
        self.name = name
        self.samples = []
        self.drifts  = []
        self.start   = None

    def add(self, dt, target_dt):
        self.samples.append(dt)
        self.drifts.append(dt - target_dt)

    def summarize(self):
        if not self.samples:
            return {}
        mean_dt = sum(self.samples)/len(self.samples)
        p95 = sorted(self.samples)[int(0.95*len(self.samples))-1]
        stdev = statistics.pstdev(self.samples) if len(self.samples) > 1 else 0.0
        mean_drift = sum(self.drifts)/len(self.drifts)
        # Stability score: 1.0 perfect, penalize abs drift + jitter
        score = max(0.0, 1.0 - (2.0*abs(mean_drift) + 1.0*stdev))
        return {
            "n": len(self.samples),
            "mean_dt": mean_dt,
            "p95_dt": p95,
            "stdev": stdev,
            "mean_drift": mean_drift,
            "score": score
        }

async def run_mode(name, corrected=False):
    stats = ModeStats(name)
    start = time.perf_counter()
    last  = start
    next_report = start + REPORT_EVERY

    # Δ₂ emulation: EWMA drift estimator + proportional correction
    ewma = None
    alpha = 0.20
    k_p = 0.75  # proportional strength (tunable)

    while True:
        now = time.perf_counter()
        if now - start >= DURATION:
            break

        # observed interval (dt) since last tick
        dt = now - last
        last = now

        # record
        stats.add(dt, TARGET_DT)

        # live report
        if now >= next_report:
            s = stats.summarize()
            if s:
                print(f"[{name}] t={now-start:5.1f}s  mean={s['mean_dt']:.4f}s  stdev={s['stdev']:.4f}s  drift={s['mean_drift']:+.4f}s  score={s['score']:.3f}")
            next_report += REPORT_EVERY

        # compute sleep target
        sleep_target = TARGET_DT + jitter()

        if corrected:
            # update EWMA drift estimate
            ewma = dt if ewma is None else (1-alpha)*ewma + alpha*dt
            drift = ewma - TARGET_DT
            # proportional correction (negative drift => shorten; positive => lengthen)
            sleep_target -= k_p * drift

        # never negative
        sleep_for = max(0.0, sleep_target)
        await asyncio.sleep(sleep_for)

    return stats

async def main():
    print("\n=== Trinity Δ₂ Benchmark ===")
    print(f"Target interval: {TARGET_DT:.3f}s, per-mode duration: {DURATION:.0f}s\n")

    # Baseline (no correction)
    base = await run_mode("Baseline", corrected=False)
    # Δ₂ corrected
    corr = await run_mode("Delta2", corrected=True)

    sb = base.summarize()
    sc = corr.summarize()

    def fmt(s): return f"{s:.4f}"
    print("\n--- Results ---")
    print(f"Ticks                : baseline={sb['n']}  delta2={sc['n']}")
    print(f"Mean interval (s)    : baseline={fmt(sb['mean_dt'])}  →  delta2={fmt(sc['mean_dt'])}")
    print(f"Mean drift   (s)     : baseline={fmt(sb['mean_drift'])}  →  delta2={fmt(sc['mean_drift'])}")
    print(f"Stdev / jitter (s)   : baseline={fmt(sb['stdev'])}  →  delta2={fmt(sc['stdev'])}")
    print(f"95th pct interval(s) : baseline={fmt(sb['p95_dt'])}  →  delta2={fmt(sc['p95_dt'])}")
    print(f"Stability score (0-1): baseline={sb['score']:.3f}      →  delta2={sc['score']:.3f}")

    # Quick improvement deltas
    drift_improve = (abs(sb['mean_drift']) - abs(sc['mean_drift']))
    jitter_improve = (sb['stdev'] - sc['stdev'])
    score_improve = (sc['score'] - sb['score'])
    print("\n--- Improvement ---")
    print(f"Drift reduction  (s): {fmt(drift_improve)}")
    print(f"Jitter reduction (s): {fmt(jitter_improve)}")
    print(f"Score gain           : {score_improve:.3f}\n")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        # ensure reliable short-sleep timing on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
