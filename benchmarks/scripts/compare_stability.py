#!/usr/bin/env python3
import numpy as np, random, json, math, time

def generate_disturbance(t, drift, noise, impulse_prob=0.02):
    base = math.sin(drift*t*0.03) * math.sin(0.6*t)
    impulse = random.gauss(0, 4.0) if random.random() < impulse_prob else 0
    return base + impulse + random.gauss(0, noise)

# Δ+1 Controller
def delta_plus_one_controller(eta=0.08, alpha=0.7, steps=600, noise=0.08):
    last_delta = 0
    theta = random.uniform(-1, 1)
    errors, outputs, deltas = [], [], []
    drift = random.uniform(0.9, 1.3)
    recovery = None
    for t in range(1, steps+1):
        grad = theta + generate_disturbance(t, drift, noise)
        delta = eta*grad + alpha*last_delta
        theta -= delta
        last_delta = delta
        errors.append(grad)
        outputs.append(theta)
        deltas.append(abs(delta))
        if recovery is None and abs(grad) < 0.05:
            recovery = t
    recovery = recovery or steps
    energy = sum(deltas)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs), recovery, energy

# Adam optimizer
def adam_optimizer(eta=0.05, beta1=0.9, beta2=0.999, steps=600, noise=0.08):
    m=v=0; theta=random.uniform(-1,1)
    errors, outputs, deltas = [], [], []
    drift = random.uniform(0.9, 1.3)
    recovery=None
    for t in range(1, steps+1):
        grad = theta + generate_disturbance(t, drift, noise)
        m = beta1*m + (1-beta1)*grad
        v = beta2*v + (1-beta2)*(grad**2)
        m_hat = m/(1-beta1**t)
        v_hat = v/(1-beta2**t)
        delta = eta*m_hat/(math.sqrt(v_hat)+1e-8)
        theta -= delta
        errors.append(grad)
        outputs.append(theta)
        deltas.append(abs(delta))
        if recovery is None and abs(grad) < 0.05:
            recovery = t
    recovery = recovery or steps
    energy = sum(deltas)
    return np.var(errors), np.mean(np.abs(errors)), np.std(outputs), recovery, energy

def run_stability_comparison(trials=12):
    results = {"delta_plus_one": [], "adam": []}
    for _ in range(trials):
        results["delta_plus_one"].append(delta_plus_one_controller())
        results["adam"].append(adam_optimizer())
    dp1 = np.mean(results["delta_plus_one"], axis=0)
    ad  = np.mean(results["adam"], axis=0)
    def summary(arr): 
        return {"error_var": arr[0], "abs_error_mean": arr[1], "output_std": arr[2],
                "recovery_iter": arr[3], "energy_integral": arr[4],
                "stability_score": 1/(arr[0]*arr[2]*arr[4]+1e-8)}
    return {
        "Δ+1_controller": summary(dp1),
        "Adam_optimizer": summary(ad),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    result = run_stability_comparison()
    outpath = "benchmarks/results/delta1_vs_adam_stability.json"
    with open(outpath,"w") as f: json.dump(result,f,indent=2)
    print("\\n🧩 Stability benchmark complete →", outpath)
    print(json.dumps(result,indent=2))
