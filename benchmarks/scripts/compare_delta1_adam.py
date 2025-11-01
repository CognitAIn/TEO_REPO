#!/usr/bin/env python3
import math, random, json, time
import numpy as np

def delta_plus_one_controller(K=0.8, alpha=0.6, steps=200, noise=0.03):
    e_prev = 0
    u_prev = 0
    errors, outputs = [], []
    for t in range(steps):
        # simulate system error (target=0)
        e = random.uniform(-1, 1) + noise * random.gauss(0, 1)
        u = max(min(K * e,  alpha * (u_prev - e_prev)), -alpha * (u_prev - e_prev))
        outputs.append(u)
        errors.append(e)
        e_prev, u_prev = e, u
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs)

def adam_optimizer(eta=0.05, beta1=0.9, beta2=0.999, steps=200, noise=0.03):
    m, v = 0, 0
    theta = random.uniform(-1, 1)
    errors, outputs = [], []
    for t in range(1, steps+1):
        grad = theta + noise * random.gauss(0,1)
        m = beta1*m + (1-beta1)*grad
        v = beta2*v + (1-beta2)*(grad**2)
        m_hat = m/(1-beta1**t)
        v_hat = v/(1-beta2**t)
        theta -= eta*m_hat/(math.sqrt(v_hat)+1e-8)
        errors.append(grad)
        outputs.append(theta)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs)

def run_comparison():
    trials = 10
    results = {"delta_plus_one": [], "adam": []}
    for _ in range(trials):
        results["delta_plus_one"].append(delta_plus_one_controller())
        results["adam"].append(adam_optimizer())
    dp1 = np.mean(results["delta_plus_one"], axis=0)
    ad  = np.mean(results["adam"], axis=0)
    return {
        "Δ+1_controller": {"error_var": dp1[0], "abs_error_mean": dp1[1], "output_std": dp1[2]},
        "Adam_optimizer": {"error_var": ad[0],  "abs_error_mean": ad[1],  "output_std": ad[2]},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    result = run_comparison()
    outpath = "benchmarks/results/delta1_vs_adam.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)
    print("\\n✅ Comparative benchmark complete. Results saved to", outpath)
    print(json.dumps(result, indent=2))
