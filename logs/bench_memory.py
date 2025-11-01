import random, time, statistics
from collections import OrderedDict
TARGET_MAINT_DT = 0.10   # maintenance cadence
SIM_OPS = 60_000
CACHE_CAP = 5_000

def zipf_id(n=20_000, s=1.1):
    # simple Zipf-like: popular keys come up more often
    r = random.random()
    k = int((n**(1-s) - (n*r)**(1-s)) / (1-s))
    return max(0, min(n-1, k))

class LRU:
    def __init__(self, cap):
        self.cap = cap; self.d = OrderedDict()
        self.hits = 0; self.misses = 0
    def get(self, k):
        if k in self.d:
            self.d.move_to_end(k); self.hits += 1; return True
        self.misses += 1; return False
    def put(self, k):
        self.d[k] = True; self.d.move_to_end(k)
        if len(self.d) > self.cap: self.d.popitem(last=False)

def run(corrected=False):
    c = LRU(CACHE_CAP)
    stall_times = []
    last = time.perf_counter()
    ewma = None; alpha=0.3; kp=0.9

    for i in range(SIM_OPS):
        # workload op
        k = zipf_id()
        if not c.get(k): c.put(k)

        # periodic maintenance (compaction/eviction scanning)
        now = time.perf_counter(); dt = now - last; last = now
        if corrected:
            ewma = dt if ewma is None else (1-alpha)*ewma + alpha*dt
            drift = (ewma - TARGET_MAINT_DT)
            sleep_for = max(0.0, TARGET_MAINT_DT + random.uniform(-0.01,0.02) - kp*drift)
        else:
            sleep_for = max(0.0, TARGET_MAINT_DT + random.uniform(-0.01,0.02))
        t0 = time.perf_counter()
        time.sleep(sleep_for)  # emulate maintenance pass
        stall_times.append(time.perf_counter() - t0)

    hit_rate = c.hits / max(1, (c.hits+c.misses))
    st = sorted(stall_times); p95 = st[int(0.95*len(st))-1]
    return {
        "hit_rate": hit_rate,
        "stall_mean": sum(st)/len(st),
        "stall_p95": p95,
        "stall_stdev": statistics.pstdev(st) if len(st)>1 else 0.0
    }

if __name__ == "__main__":
    print("\n=== Memory Maintenance Benchmark (LRU + D2) ===")
    base = run(False); d2 = run(True)
    def f(x): return f"{x:.4f}"
    print(f"Hit rate            : base={f(base['hit_rate'])}  ->  D2={f(d2['hit_rate'])}")
    print(f"Stall mean (s)      : base={f(base['stall_mean'])} ->  D2={f(d2['stall_mean'])}")
    print(f"Stall p95  (s)      : base={f(base['stall_p95'])}  ->  D2={f(d2['stall_p95'])}")
    print(f"Stall stdev (s)     : base={f(base['stall_stdev'])}->  D2={f(d2['stall_stdev'])}\n")

