import os, json, time
import numpy as np
from benchmarks.scripts.async_queue_jitter_stabilized import simulate_queue, make_delta_plus_one, make_adam

def run_final(K=0.01, alpha=0.9, gamma=0.95, trials=10, steps=3000):
    dp1_stats, adam_stats = [], []
    for s in range(trials):
        dp1 = simulate_queue(steps, make_delta_plus_one(K=K, alpha=alpha, gamma=gamma), seed=s)
        ad  = simulate_queue(steps, make_adam(), seed=s)
        dp1_stats.append(dp1["jitter_pct"])
        adam_stats.append(ad["jitter_pct"])
    return {
        "config": {"trials": trials, "steps": steps, "K": K, "alpha": alpha, "gamma": gamma},
        "Δ+1_final": {
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
    result = run_final()
    os.makedirs("benchmarks/results", exist_ok=True)
    outpath = "benchmarks/results/async_jitter_3000_final_tuned.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Final Δ+1 benchmark complete →", outpath)
    print(json.dumps(result, indent=2))
