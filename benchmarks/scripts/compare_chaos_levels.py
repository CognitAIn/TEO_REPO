#!/usr/bin/env python3
import json, math, random, time, os
import numpy as np

def delta_plus_one_controller(chaos_amp=1.0, noise=0.05, steps=200):
    theta = random.uniform(-1, 1)
    prev_delta = 0
    errors, outputs = [], []
    for _ in range(steps):
        grad = chaos_amp * theta + noise * random.gauss(0, 1)
        delta = -grad + 0.3 * prev_delta
        theta += delta
        prev_delta = delta
        errors.append(grad)
        outputs.append(theta)
    recovery = next((i for i, e in enumerate(errors) if abs(e) < 0.02), steps)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs), recovery, np.sum(np.abs(np.diff(outputs)))

def adam_optimizer(chaos_amp=1.0, noise=0.05, steps=200):
    m, v, theta = 0, 0, random.uniform(-1, 1)
    errors, outputs = [], []
    for t in range(1, steps + 1):
        grad = chaos_amp * theta + noise * random.gauss(0, 1)
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * grad ** 2
        m_hat = m / (1 - 0.9 ** t)
        v_hat = v / (1 - 0.999 ** t)
        theta -= 0.05 * m_hat / (math.sqrt(v_hat) + 1e-8)
        errors.append(grad)
        outputs.append(theta)
    recovery = next((i for i, e in enumerate(errors) if abs(e) < 0.02), steps)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs), recovery, np.sum(np.abs(np.diff(outputs)))

def run_level(level, chaos_amp, noise):
    trials = 10
    d, a = [], []
    for _ in range(trials):
        d.append(delta_plus_one_controller(chaos_amp, noise))
        a.append(adam_optimizer(chaos_amp, noise))
    d, a = np.mean(d, axis=0), np.mean(a, axis=0)
    return {
        "level": level,
        "Δ+1_controller": {"error_var": d[0], "abs_error_mean": d[1], "output_std": d[2], "recovery_iters": d[3], "energy_integral": d[4]},
        "Adam_optimizer": {"error_var": a[0], "abs_error_mean": a[1], "output_std": a[2], "recovery_iters": a[3], "energy_integral": a[4]},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

def main():
    os.makedirs("benchmarks/results", exist_ok=True)
    configs = [
        ("low", 0.8, 0.03),
        ("medium", 1.0, 0.07),
        ("high", 1.2, 0.12)
    ]
    summary = {}
    for lvl, amp, noise in configs:
        result = run_level(lvl, amp, noise)
        summary[lvl] = result
        with open(f"benchmarks/results/chaos_level_{lvl}.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"✅ Completed chaos level {lvl}")
    with open("benchmarks/results/chaos_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\n✅ Full multi-chaos benchmark complete → benchmarks/results/chaos_summary.json")

if __name__ == "__main__":
    main()
