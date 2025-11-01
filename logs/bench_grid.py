# Simplified frequency control test:
#   Swing eq: df/dt = (Pm - Pe - D*f)/M
#   Primary droop: Pm = Pm0 - Kp*f
#   D2 acts like bias-correcting AGC (EWMA on f, trims Pm)
import math, statistics, random

DT = 0.05       # integration step (s)
T_SIM = 30.0    # seconds
M = 10.0        # inertia
D = 1.0         # damping
Pm0 = 0.0       # nominal mech power setpoint
Kp = 5.0        # primary droop gain
STEP_TIME = 3.0
STEP_SIZE = 0.8  # sudden load (Pe increase)

def run(corrected=False):
    f = 0.0      # frequency deviation (Hz relative)
    Pm = Pm0
    Pe = 0.0
    trace = []
    ewma=None; alpha=0.1; kagc=3.0

    t=0.0
    while t < T_SIM:
        # step load
        if abs(t-STEP_TIME) < 1e-9: Pe += STEP_SIZE
        # primary droop
        Pm = Pm0 - Kp*f
        # D2 AGC bias correction (slow)
        if corrected:
            ewma = f if ewma is None else (1-alpha)*ewma + alpha*f
            Pm -= kagc*ewma*DT  # small trim per step

        # swing
        dfdt = (Pm - Pe - D*f)/M
        f += dfdt*DT
        trace.append((t, f))
        t += DT
    return trace

def summarize(tr):
    freqs = [x[1] for x in tr]
    nadir = min(freqs)
    # settling: first time |f| < 0.02 and stays within ±0.02 thereafter
    settle = None
    for i,(t,f) in enumerate(tr):
        if abs(f) < 0.02 and all(abs(x[1])<0.02 for x in tr[i:]):
            settle = t; break
    return {"nadir": nadir, "settle": settle}

if __name__ == "__main__":
    print("\n=== Power Grid Step Response (D2 as AGC) ===")
    base = summarize(run(False))
    d2   = summarize(run(True))
    def g(x): return "∞" if x is None else f"{x:.2f}s"
    print(f"Nadir (most negative freq) : base={base['nadir']:.3f} -> D2={d2['nadir']:.3f}")
    print(f"Settling time (|f|<0.02Hz) : base={g(base['settle'])} -> D2={g(d2['settle'])}\n")

