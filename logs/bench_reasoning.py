import asyncio, random, time, statistics, sys
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TARGET_DT = 0.05   # scheduler tick target (s)
SIM_TIME  = 15.0   # seconds
N_TASKS   = 800    # total tasks offered
PROGRESS_INTERVAL = 2.0  # seconds

def service_time():  # lognormal service times ~ realistic LLM/RAG microservices mix
    return random.lognormvariate(-2.0, 0.7)  # ~30–120 ms typical tail

def jitter():  # scheduler jitter (network, thread, GC)
    j = random.uniform(-0.010, 0.015)
    if random.random() < 0.03: j += random.uniform(-0.020, 0.040)
    return j

class QueueSim:
    def __init__(self, corrected: bool):
        self.corrected = corrected
        self.latencies, self.queue_depths = [], []
        self.completed = 0; self.enqueued = 0
        self.q = asyncio.Queue()
        self.ewma = None; self.alpha = 0.25; self.kp = 0.8
        self.last_report = time.perf_counter()

    async def producer(self):
        start = time.perf_counter()
        while time.perf_counter() - start < SIM_TIME and self.enqueued < N_TASKS:
            burst = random.randint(1, 6)
            for _ in range(burst):
                await self.q.put(time.perf_counter())
                self.enqueued += 1
            await asyncio.sleep(max(0.01 + random.uniform(-0.005, 0.02), 0))

    async def worker(self):
        last = time.perf_counter()
        while self.completed < N_TASKS:
            now = time.perf_counter(); dt = now - last; last = now
            if self.corrected:
                self.ewma = dt if self.ewma is None else (1-self.alpha)*self.ewma + self.alpha*dt
                drift = (self.ewma - TARGET_DT)
                sleep_for = max(0.0, TARGET_DT + jitter() - self.kp*drift)
            else:
                sleep_for = max(0.0, TARGET_DT + jitter())
            await asyncio.sleep(sleep_for)

            if not self.q.empty():
                t0 = await self.q.get()
                await asyncio.sleep(service_time())
                self.latencies.append(time.perf_counter() - t0)
                self.completed += 1
            self.queue_depths.append(self.q.qsize())

            # live progress every 2 s
            if time.perf_counter() - self.last_report >= PROGRESS_INTERVAL:
                done_pct = 100 * self.completed / max(1, N_TASKS)
                mean_lat = (sum(self.latencies)/len(self.latencies)) if self.latencies else 0
                print(f"[Progress] {self.completed}/{N_TASKS} ({done_pct:.1f}%)  q={self.q.qsize()}  "
                      f"mean_lat={mean_lat:.3f}s")
                sys.stdout.flush()
                self.last_report = time.perf_counter()

            if self.completed >= N_TASKS:
                break

    async def run(self):
        await asyncio.gather(self.producer(), self.worker())
        return self.summary()

    def summary(self):
        if not self.latencies: return {}
        lat = sorted(self.latencies)
        p95 = lat[int(0.95*len(lat))-1]; p99 = lat[int(0.99*len(lat))-1]
        stdev_q = statistics.pstdev(self.queue_depths) if len(self.queue_depths)>1 else 0.0
        return {
            "done": self.completed,
            "mean_lat": sum(lat)/len(lat),
            "p95_lat": p95,
            "p99_lat": p99,
            "q_mean": sum(self.queue_depths)/max(1,len(self.queue_depths)),
            "q_stdev": stdev_q
        }

async def main():
    print("\n=== AI Reasoning Pipeline Benchmark (Δ₂ with Progress) ===")
    base = await QueueSim(False).run()
    d2   = await QueueSim(True).run()
    def f(x): return f"{x:.4f}"
    print(f"\nTasks completed    : base={base['done']}  →  Δ₂={d2['done']}")
    print(f"Mean latency (s)   : base={f(base['mean_lat'])}  →  Δ₂={f(d2['mean_lat'])}")
    print(f"P95 latency  (s)   : base={f(base['p95_lat'])}   →  Δ₂={f(d2['p95_lat'])}")
    print(f"P99 latency  (s)   : base={f(base['p99_lat'])}   →  Δ₂={f(d2['p99_lat'])}")
    print(f"Queue mean / σ     : base={f(base['q_mean'])}/{f(base['q_stdev'])} →  "
          f"Δ₂={f(d2['q_mean'])}/{f(d2['q_stdev'])}\n")

if __name__ == "__main__":
    asyncio.run(main())
