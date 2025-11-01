import json, time, psutil, numpy as np, matplotlib.pyplot as plt, os
from datetime import datetime

def run_adaptive_refinement(duration=120, duty_init=0.7, alpha=0.2, window=10):
    print(f"[TGO Adaptive Range] running {duration}s, duty_init={duty_init}, alpha={alpha}, window={window}")
    cpu_trace, mem_trace, duty_trace = [], [], []
    duty = duty_init
    start = time.time()
    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        cpu_trace.append(cpu)
        mem_trace.append(mem)

        # rolling variance feedback
        if len(cpu_trace) >= window:
            recent = cpu_trace[-window:]
            var = np.var(recent)
            avg = np.mean(recent)
            # adaptive midpoint
            target = np.clip(0.6 + (0.1 * (avg - 5) / 5), 0.4, 0.8)
            if avg > 6:
                duty -= alpha * (avg - 5) / 10
            elif avg < 4:
                duty += alpha * (5 - avg) / 10
            # gentle recentering toward target
            duty += (target - duty) * 0.05
            duty = np.clip(duty, 0.4, 0.9)

        duty_trace.append(duty)

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "mem_avg": np.mean(mem_trace),
        "duty_mean": np.mean(duty_trace),
        "cpu_var": float(np.var(cpu_trace)),
        "trace": {
            "cpu": cpu_trace,
            "mem": mem_trace,
            "duty": duty_trace
        }
    }

    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase9_refinement.json")
    with open(outfile, "w") as f:
        json.dump(result, f, indent=4)
    print(f"[TGO Adaptive Range] Results saved: {outfile}")

    # Visualization
    t = range(len(cpu_trace))
    plt.figure(figsize=(10,5))
    plt.plot(t, cpu_trace, label="CPU %", alpha=0.7)
    plt.plot(t, mem_trace, label="MEM %", alpha=0.6)
    plt.plot(t, [d*100 for d in duty_trace], "--", label="Duty % (scaled)")
    plt.xlabel("Sample")
    plt.ylabel("Percent / Duty")
    plt.title("Trinity Adaptive Range Refinement — Phase 9")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase9_plot.png")
    plt.savefig(img_path)
    print(f"[TGO Adaptive Range] Plot saved: {img_path}")

if __name__ == "__main__":
    run_adaptive_refinement()
