import json, time, random, os
import numpy as np

def prbs(length, period=31, high=1.0, low=-1.0):
    # Simple LFSR-like PRBS
    s = 0xACE1
    seq=[]
    for _ in range(length):
        bit = ((s >> 0) ^ (s >> 2) ^ (s >> 3) ^ (s >> 5)) & 1
        s = (s >> 1) | (bit << 15)
        seq.append(high if (s % period) > period//2 else low)
    return seq

def delta_plus_one(y, eta=0.06, alpha=0.6):
    theta=0; last=0; out=[]; deltas=[]
    for e in y:
        d = eta*e + alpha*last
        theta += d; last=d
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
    return dict(
        error_var=float(np.var(err)),
        abs_error_mean=float(np.mean(np.abs(err))),
        output_std=float(np.std(out)),
        energy_integral=float(np.sum(deltas))
    )

def run(length=1000, noise=0.05, seed=42, outpath="benchmarks/results/prbs.json"):
    random.seed(seed); np.random.seed(seed)
    os.makedirs("benchmarks/results", exist_ok=True)
    target = np.array(prbs(length))
    noisev = np.random.normal(0, noise, size=length)
    y = target + noisev
    out_d, d_d = delta_plus_one(y); err_d = y - out_d
    out_a, d_a = adam(y);           err_a = y - out_a
    res = {"Δ+1": metrics(err_d,out_d,d_d), "Adam": metrics(err_a,out_a,d_a),
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "config": {"length":length,"noise":noise,"seed":seed}}
    with open(outpath,"w") as f: json.dump(res,f,indent=2)
    print("✅ PRBS →", outpath)

if __name__=="__main__":
    run()
