import json, time, psutil, numpy as np, os, matplotlib.pyplot as plt
from datetime import datetime

def load_model(model_path):
    try:
        with open(model_path) as f: return json.load(f)
    except Exception: return None

def adaptive_validate(model, duration=90):
    coeffs = model.get("coefficients", {}) if model else {}
    baseline = model.get("baseline", 0.0)
    duty = model.get("data", [{}])[-1].get("duty_mean", 0.6)
    cpu_trace, mem_trace, duty_trace = [], [], []

    print(f"[TGO Validate] running {duration}s | start duty={duty:.2f} | baseline={baseline:.2f}")

    start = time.time()
    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        # predict next duty from model if available
        if coeffs:
            cpu_term = coeffs.get("cpu_avg", 0) * cpu
            mem_term = coeffs.get("mem_avg", 0) * mem
            duty = max(0.3, min(0.9, duty - 0.01*(cpu_term + mem_term - baseline)))
        duty_trace.append(duty)
        cpu_trace.append(cpu)
        mem_trace.append(mem)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "mem_avg": np.mean(mem_trace),
        "duty_mean": np.mean(duty_trace),
        "trace": {"cpu": cpu_trace, "mem": mem_trace, "duty": duty_trace}
    }

if __name__ == "__main__":
    model_dir = r"C:\Users\user\Desktop\Trinity_STEM\benchmarks"
    # pick most recent Phase-5 model
    candidates = sorted(
        [os.path.join(dp, f) for dp,_,fs in os.walk(model_dir) for f in fs if f.startswith("tgo_phase5_") and f.endswith("learning.json")],
        key=os.path.getmtime, reverse=True)
    model = load_model(candidates[0]) if candidates else None

    results = adaptive_validate(model)
    outdir = os.environ.get("TGO_OUTDIR", ".")
    out_json = os.path.join(outdir, "tgo_phase8_validation.json")
    with open(out_json, "w") as f: json.dump(results, f, indent=4)
    print(f"[TGO Validate] Saved JSON: {out_json}")

    # plot
    t = range(len(results["trace"]["cpu"]))
    plt.figure(figsize=(10,5))
    plt.plot(t, results["trace"]["cpu"], label="CPU %", alpha=0.7)
    plt.plot(t, results["trace"]["mem"], label="MEM %", alpha=0.6)
    plt.plot(t, [d*100 for d in results["trace"]["duty"]], label="Duty % (scaled)", linestyle="--")
    plt.title("Trinity Adaptive Validation — Phase 8")
    plt.xlabel("Sample"); plt.ylabel("Percent / Scaled Duty")
    plt.grid(True, linestyle="--", alpha=0.5); plt.legend(); plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase8_plot.png")
    plt.savefig(img_path)
    print(f"[TGO Validate] Plot saved: {img_path}")
