import json, time, psutil, numpy as np, matplotlib.pyplot as plt, os
from datetime import datetime

def run_predictive_feedback(duration=90, duty_init=0.7, alpha=0.3):
    print(f"[TGO Predictive] running {duration}s, initial duty={duty_init}, alpha={alpha}")
    cpu_trace, mem_trace, duty_trace = [], [], []
    duty = duty_init
    start = time.time()
    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        cpu_trace.append(cpu)
        mem_trace.append(mem)
        duty_trace.append(duty)
        if len(cpu_trace) > 5:
            trend = np.polyfit(range(len(cpu_trace[-5:])), cpu_trace[-5:], 1)[0]
            if trend > 0.3:
                duty = max(0.3, duty - alpha * 0.1)
            elif trend < -0.3:
                duty = min(0.9, duty + alpha * 0.1)
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "mem_avg": np.mean(mem_trace),
        "duty_mean": np.mean(duty_trace),
        "duty_trace": duty_trace,
        "cpu_trace": cpu_trace,
        "mem_trace": mem_trace
    }

if __name__ == "__main__":
    data = run_predictive_feedback()
    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase4_predictive.json")
    with open(outfile, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[TGO Predictive] Saved JSON: {outfile}")

    # Visualization
    t = range(len(data["cpu_trace"]))
    plt.figure(figsize=(10,5))
    plt.plot(t, data["cpu_trace"], label="CPU %", alpha=0.7)
    plt.plot(t, data["mem_trace"], label="MEM %", alpha=0.5)
    plt.plot(t, [d*100 for d in data["duty_trace"]], label="Duty % (scaled)", linestyle="--")
    plt.xlabel("Sample")
    plt.ylabel("Percent / Scaled Duty")
    plt.title("Trinity Adaptive Feedback — Phase 4 Predictive Visualization")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase4_plot.png")
    plt.savefig(img_path)
    print(f"[TGO Predictive] Plot saved: {img_path}")
