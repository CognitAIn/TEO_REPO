import json, time, random, os, math
import numpy as np

def lorenz(T=1000, dt=0.01, sigma=10, rho=28, beta=8/3, seed=7):
    random.seed(seed); np.random.seed(seed)
    x=y=z=1.0
    xs=[]
    for _ in range(T):
        dx = sigma*(y-x)
        dy = x*(rho - z) - y
        dz = x*y - beta*z
        x += dx*dt; y += dy*dt; z += dz*dt
        xs.append(x)
    xs = np.array(xs); xs = (xs - xs.mean())/(xs.std()+1e-8)  # normalize
    return xs

def delta_plus_one(y, eta=0.05, alpha=0.65):
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
    rec = next((i for i,e in enumerate(np.abs(err)) if e<0.03), len(err))
    return dict(
        error_var=float(np.var(err)),
        abs_error_mean=float(np.mean(np.abs(err))),
        output_std=float(np.std(out)),
        recovery_iters=int(rec),
        energy_integral=float(np.sum(deltas))
    )

def run(T=4000, dt=0.01, seed=7, noise=0.06, outpath="benchmarks/results/lorenz.json"):
    os.makedirs("benchmarks/results", exist_ok=True)
    x = lorenz(T=T, dt=dt, seed=seed)
    y = x + np.random.normal(0, noise, size=len(x))
    out_d, d_d = delta_plus_one(y); err_d = y - out_d
    out_a, d_a = adam(y);           err_a = y - out_a
    res = {"Δ+1": metrics(err_d,out_d,d_d), "Adam": metrics(err_a,out_a,d_a),
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "config": {"T":T,"dt":dt,"seed":seed,"noise":noise}}
    with open(outpath,"w") as f: json.dump(res,f,indent=2)
    print("✅ Lorenz chaos →", outpath)

if __name__=="__main__":
    run()
