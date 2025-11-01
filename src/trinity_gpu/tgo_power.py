import json, time, psutil, numpy as np, matplotlib.pyplot as plt, os
from datetime import datetime

def run_power_distribution(duration=120, alpha=0.25, window=10):
    print(f"[TGO Power] running {duration}s, alpha={alpha}, window={window}")
    cpu_trace, gpu_trace, duty_trace, pwr_trace = [], [], [], []
    duty = 0.7
    start = time.time()

    def fake_gpu_power(duty):
        # Simulated GPU watt usage (for integrated GPU)
        base = 6.5 + (duty * 4.0)
        jitter = np.random.uniform(-0.3, 0.3)
        return base + jitter

    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        gpu_power = fake_gpu_power(duty)
        total_power = gpu_power + (cpu / 10)
        cpu_trace.append(cpu)
        gpu_trace.append(gpu_power)
        pwr_trace.append(total_power)

        if len(cpu_trace) >= window:
            avg_cpu = np.mean(cpu_trace[-window:])
            var_cpu = np.var(cpu_trace[-window:])
            avg_pwr = np.mean(pwr_trace[-window:])

            # adaptive feedback: combine efficiency + variance
            stability = max(0.1, 1 - var_cpu / 20)
            target = np.clip(0.6 + (0.1 * (avg_cpu - 5) / 5), 0.4, 0.9)
            if avg_cpu > 6:
                duty -= alpha * (avg_cpu - 5) / 10
            elif avg_cpu < 4:
                duty += alpha * (5 - avg_cpu) / 10
            duty += (target - duty) * 0.05 * stability
            duty = np.clip(duty, 0.3, 0.9)

        duty_trace.append(duty)

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "gpu_power_avg": np.mean(gpu_trace),
        "total_power_avg": np.mean(pwr_trace),
        "cpu_var": float(np.var(cpu_trace)),
        "duty_mean": np.mean(duty_trace),
        "trace": {
            "cpu": cpu_trace,
            "gpu_power": gpu_trace,
            "duty": duty_trace,
            "total_power": pwr_trace
        }
    }

    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase10_power.json")
    with open(outfile, "w") as f:
        json.dump(result, f, indent=4)
    print(f"[TGO Power] Results saved: {outfile}")

    # Visualization
    t = range(len(cpu_trace))
    plt.figure(figsize=(10,5))
    plt.plot(t, cpu_trace, label="CPU %", alpha=0.7)
    plt.plot(t, [p*10 for p in gpu_trace], label="GPU Power x10 (sim)", alpha=0.6)
    plt.plot(t, [d*100 for d in duty_trace], "--", label="Duty % (scaled)")
    plt.xlabel("Sample")
    plt.ylabel("CPU / Power / Duty")
    plt.title("Trinity Adaptive Power Distribution — Phase 10")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase10_plot.png")
    plt.savefig(img_path)
    print(f"[TGO Power] Plot saved: {img_path}")

if __name__ == "__main__":
    run_power_distribution()
