import json, math, random, time, os
import numpy as np

# --- Stabilized Δ+1 controller ---
def make_delta_plus_one(K=0.015, alpha=0.5, gamma=0.2):
    prev_d = 0.0
    def step(e, e_prev, t):
        nonlocal prev_d
        d = e - e_prev
        dd = d - prev_d  # second-order damping term
        prev_d = d
        clip_mag = alpha * abs(d)
        u = K * (e - gamma * dd)
        u = max(-clip_mag, min(clip_mag, u))
        return -u
    return step

# --- Adam baseline ---
def make_adam(eta=0.02, b1=0.9, b2=0.999, eps=1e-8):
    m=v=0.0; t=0
    def step(e, e_prev, _t):
        nonlocal m,v,t
        t += 1
        g = e
        m = b1*m + (1-b1)*g
        v = b2*v + (1-b2)*(g*g)
        mhat = m / (1 - b1**t)
        vhat = v / (1 - b2**t)
        du = -eta * mhat / (math.sqrt(vhat)+eps)
        return -du
    return step

# --- Simulation setup ---
def simulate_queue(steps, controller_step, seed=0, target_latency=1.0):
    rng = random.Random(seed)
    latency_hist = []
    service_pace = 1.0
    queue_len = 0.0
    e_prev = 0.0
    for t in range(steps):
        arrivals = max(0.0, 1.0 + 0.35*rng.gauss(0,1) + 0.25*math.sin(2*math.pi*t/97))
        serviced = min(queue_len + arrivals, service_pace)
        queue_len = max(0.0, queue_len + arrivals - serviced)
        latency = queue_len
        e = latency - target_latency
        du = controller_step(e, e_prev, t)
        service_pace = max(0.1, service_pace + du)
        e_prev = e
        latency_hist.append(latency)
    lat = np.array(latency_hist, dtype=float)
    mean = float(np.mean(lat) + 1e-12)
    std  = float(np.std(lat))
    jitter_pct = 100.0 * std / mean
    return {"mean_latency": mean, "std_latency": std, "jitter_pct": jitter_pct}

def run_trials(trials=10, steps=2000):
    seeds = list(range(trials))
    dp1_stats, adam_stats = [], []
    for s in seeds:
        dp1 = simulate_queue(steps, make_delta_plus_one(), seed=s)
        ad  = simulate_queue(steps, make_adam(), seed=s)
        dp1_stats.append(dp1["jitter_pct"])
        adam_stats.append(ad["jitter_pct"])
    return {
        "config": {"trials": trials, "steps": steps, "controller":"Δ+1 stabilized (K=0.015, α=0.5, γ=0.2)"},
        "Δ+1_stabilized": {
            "jitter_pct_mean": float(np.mean(dp1_stats)),
            "jitter_pct_std":  float(np.std(dp1_stats))
        },
        "Adam_optimizer": {
            "jitter_pct_mean": float(np.mean(adam_stats)),
            "jitter_pct_std":  float(np.std(adam_stats))
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    random.seed(0)
    result = run_trials(trials=10, steps=2000)
    os.makedirs("benchmarks/results", exist_ok=True)
    outpath = "benchmarks/results/async_jitter_2000_stabilized.json"
    with open(outpath, "w") as f: json.dump(result, f, indent=2)
    print("\n✅ Stabilized async jitter test complete →", outpath)
    print(json.dumps(result, indent=2))
