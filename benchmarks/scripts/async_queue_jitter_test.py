import json, math, random, time
import numpy as np

# Simulated async CPU queue:
# - Arrivals with bursty noise emulate thread spikes
# - Service pace is adjusted by the controller each step
def simulate_queue(steps, controller_step, seed=0, target_latency=1.0):
    rng = random.Random(seed)
    latency_hist = []
    service_pace = 1.0
    queue_len = 0.0
    e_prev = 0.0
    for t in range(steps):
        # Bursty arrivals: base + colored noise
        arrivals = max(0.0, 1.0 + 0.35*rng.gauss(0,1) + 0.25*math.sin(2*math.pi*t/97))
        # Service completed this tick
        serviced = min(queue_len + arrivals, service_pace)
        queue_len = max(0.0, queue_len + arrivals - serviced)

        # Proxy latency = queue length; error vs target
        latency = queue_len
        e = latency - target_latency

        # Update controller (returns delta to service pace)
        du = controller_step(e, e_prev, t)
        service_pace = max(0.1, service_pace + du)

        e_prev = e
        latency_hist.append(latency)

    lat = np.array(latency_hist, dtype=float)
    mean = float(np.mean(lat) + 1e-12)
    std  = float(np.std(lat))
    jitter_pct = 100.0 * std / mean
    return {
        "mean_latency": mean,
        "std_latency": std,
        "jitter_pct": jitter_pct,
        "trace_samples": [round(x,4) for x in lat[:50]]  # small peek for sanity
    }

# Δ+1 harmonic controller
def make_delta_plus_one(K=0.08, alpha=0.9):
    def step(e, e_prev, t):
        d = e - e_prev
        clip_mag = alpha * abs(d)
        u = K * e
        if u >  clip_mag: u =  clip_mag
        if u < -clip_mag: u = -clip_mag
        return -u  # negative du increases service when error>0 (lag)
    return step

# Adam-like baseline treating error as a "gradient"
def make_adam(eta=0.02, b1=0.9, b2=0.999, eps=1e-8):
    m=v=0.0
    t=0
    def step(e, e_prev, _t):
        nonlocal m,v,t
        t += 1
        g = e
        m = b1*m + (1-b1)*g
        v = b2*v + (1-b2)*(g*g)
        mhat = m / (1 - b1**t)
        vhat = v / (1 - b2**t)
        du = -eta * mhat / (math.sqrt(vhat)+eps)
        return -du  # negative du increases service when error>0 (lag)
    return step

def run_trials(trials=10, steps=2000):
    seeds = list(range(trials))
    dp1_stats = []
    adam_stats = []

    for s in seeds:
        dp1 = simulate_queue(steps, make_delta_plus_one(), seed=s)
        ad  = simulate_queue(steps, make_adam(),            seed=s)
        dp1_stats.append(dp1["jitter_pct"])
        adam_stats.append(ad["jitter_pct"])

    return {
        "config": {"trials": trials, "steps": steps, "arrival_noise":"bursty + sinusoid", "target_latency": 1.0},
        "Δ+1_controller": {
            "jitter_pct_mean": float(np.mean(dp1_stats)),
            "jitter_pct_std":  float(np.std(dp1_stats)),
        },
        "Adam_optimizer": {
            "jitter_pct_mean": float(np.mean(adam_stats)),
            "jitter_pct_std":  float(np.std(adam_stats)),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    random.seed(0)
    result = run_trials(trials=10, steps=2000)
    outpath = "benchmarks/results/async_jitter_2000.json"
    import os
    os.makedirs("benchmarks/results", exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Async jitter test complete →", outpath)
    print(json.dumps(result, indent=2))
