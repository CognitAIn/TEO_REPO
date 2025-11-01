import json, time, math, random, os
import numpy as np

def step_impulse_series(steps, impulse_p, noise):
    series = []
    target = 1.0
    for t in range(steps):
        base = target if t>steps//5 else 0.0
        impulse = random.gauss(0, 0.8) if random.random()<impulse_p else 0
        series.append(base + impulse + random.gauss(0, noise))
    return series

def delta_plus_one(y, eta=0.08, alpha=0.7):
    theta=0; last=0; out=[]; deltas=[]
    for e in y:
        d = eta*e + alpha*last
        theta += d; last = d
        out.append(theta); deltas.append(abs(d))
    return np.array(out), np.array(deltas)

def adam(y, lr=0.05, b1=0.9, b2=0.999):
    m=v=0; theta=0; out=[]; deltas=[]; t=0
    for e in y:
        t+=1; g=e
        m=b1*m+(1-b1)*g; v=b2*v+(1-b2)*(g*g)
        mh=m/(1-b1**t); vh=v/(1-b2**t)
        d = lr*mh/(vh**0.5+1e-8)
        theta += d; out.append(theta); deltas.append(abs(d))
    return np.array(out), np.array(deltas)

def metrics(err, out, deltas):
    abs_err=np.abs(err)
    rec = next((i for i,e in enumerate(abs_err) if e<0.02), len(err))
    return dict(
        error_var=float(np.var(err)),
        abs_error_mean=float(np.mean(abs_err)),
        output_std=float(np.std(out)),
        recovery_iters=int(rec),
        energy_integral=float(np.sum(deltas))
    )

def run(steps=600, impulse_p=0.03, noise=0.05, seed=0, outpath="benchmarks/results/step_impulse.json"):
    random.seed(seed); np.random.seed(seed)
    os.makedirs("benchmarks/results", exist_ok=True)
    y = step_impulse_series(steps, impulse_p, noise)
    out_d, d_d = delta_plus_one(y); err_d = np.array(y)-out_d
    out_a, d_a = adam(y);           err_a = np.array(y)-out_a
    res = {
      "Δ+1": metrics(err_d, out_d, d_d),
      "Adam": metrics(err_a, out_a, d_a),
      "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
      "config": {"steps":steps,"impulse_p":impulse_p,"noise":noise,"seed":seed}
    }
    with open(outpath,"w") as f: json.dump(res,f,indent=2)
    print("✅ step/impulse →", outpath)

if __name__=="__main__":
    run()
