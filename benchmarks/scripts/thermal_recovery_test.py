import json, random, math, time
import numpy as np

def delta_plus_one_controller(steps=150, alpha=1.2, K=0.8, noise=0.1, spike_step=75, spike_scale=1.3):
    e_prev, u_prev = 0, 0
    energy, power, latency = [], [], []
    for t in range(steps):
        chaos = random.gauss(0, noise)
        if t == spike_step:
            chaos += spike_scale
        e = chaos - 0.2*u_prev
        Δ = e - e_prev
        u = max(min(K*e, alpha*abs(Δ)), -alpha*abs(Δ))
        e_prev, u_prev = e, u
        energy.append(u)
        power.append(chaos)
        latency.append(abs(e))
    rec_iter = next((i for i in range(spike_step, steps) if abs(latency[i]) < 0.05), steps)
    return np.var(latency), np.mean(latency), np.std(energy), rec_iter

def adam_optimizer(steps=150, eta=0.05, beta1=0.9, beta2=0.999, noise=0.1, spike_step=75, spike_scale=1.3):
    m, v, theta = 0, 0, random.uniform(-1, 1)
    errors, outputs = [], []
    for t in range(1, steps + 1):
        grad = theta + noise * random.gauss(0,1)
        if t == spike_step:
            grad += spike_scale
        m = beta1 * m + (1 - beta1) * grad
        v = beta2 * v + (1 - beta2) * (grad ** 2)
        m_hat = m / (1 - beta1 ** t)
        v_hat = v / (1 - beta2 ** t)
        theta -= eta * m_hat / (math.sqrt(v_hat) + 1e-8)
        errors.append(grad)
        outputs.append(theta)
    rec_iter = next((i for i in range(spike_step, steps) if abs(errors[i]) < 0.05), steps)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs), rec_iter

def run_trials(trials=20):
    results = {"Δ+1_controller": [], "Adam_optimizer": []}
    for _ in range(trials):
        results["Δ+1_controller"].append(delta_plus_one_controller())
        results["Adam_optimizer"].append(adam_optimizer())
    dp1 = np.mean(results["Δ+1_controller"], axis=0)
    ad  = np.mean(results["Adam_optimizer"], axis=0)
    summary = {
        "Δ+1_controller": {
            "error_var": dp1[0],
            "abs_error_mean": dp1[1],
            "output_std": dp1[2],
            "recovery_iters": dp1[3]
        },
        "Adam_optimizer": {
            "error_var": ad[0],
            "abs_error_mean": ad[1],
            "output_std": ad[2],
            "recovery_iters": ad[3]
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return summary

if __name__ == "__main__":
    result = run_trials()
    outpath = "benchmarks/results/thermal_recovery_test.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)
    print("\\n✅ Thermal recovery test complete. Results saved to", outpath)
    print(json.dumps(result, indent=2))
