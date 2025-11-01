import json, time, psutil, numpy as np, matplotlib.pyplot as plt, os
from datetime import datetime

def run_thermo_adaptive(duration=180, alpha=0.25, beta=0.15, heat_coeff=0.06, cool_coeff=0.04, temp_limit=80):
    print(f"[TGO ThermoAdaptive] running {duration}s α={alpha} β={beta}")
    cpu_trace, power_trace, temp_trace, duty_trace = [], [], [], []
    duty, temp = 0.75, 40.0
    start = time.time()

    def simulate_heat(cpu, power, temp):
        heat_in = (cpu + power*10) * heat_coeff
        cool_out = (temp - 35) * cool_coeff
        return temp + heat_in - cool_out

    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        gpu_power = np.clip((duty * 10) + np.random.normal(0, 0.2), 0, 12)
        temp = simulate_heat(cpu, gpu_power, temp)

        # adaptive feedback: combine heat + load feedback
        if temp > temp_limit:
            duty -= alpha * (temp - temp_limit) / 50
        elif temp < temp_limit - 15:
            duty += alpha * 0.05
        duty -= beta * (cpu / 100.0 - 0.05)  # light dynamic correction

        duty = np.clip(duty, 0.3, 0.9)
        cpu_trace.append(cpu)
        power_trace.append(gpu_power)
        temp_trace.append(temp)
        duty_trace.append(duty)

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": float(np.mean(cpu_trace)),
        "power_avg": float(np.mean(power_trace)),
        "temp_avg": float(np.mean(temp_trace)),
        "temp_peak": float(np.max(temp_trace)),
        "duty_mean": float(np.mean(duty_trace))
    }

    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase12_thermo_adaptive.json")
    with open(outfile, "w") as f:
        json.dump(result, f, indent=4)
    print(f"[TGO ThermoAdaptive] JSON saved: {outfile}")

    t = range(len(cpu_trace))
    plt.figure(figsize=(10,5))
    plt.plot(t, cpu_trace, label="CPU %", alpha=0.7)
    plt.plot(t, power_trace, label="GPU Power (sim)", alpha=0.6)
    plt.plot(t, temp_trace, label="Temp °C", alpha=0.5)
    plt.plot(t, [d*100 for d in duty_trace], "--", label="Duty % (scaled)")
    plt.xlabel("Sample"); plt.ylabel("Load / Power / Temp / Duty")
    plt.title("Trinity Thermo-Adaptive Power Distribution — Phase 12")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase12_plot.png")
    plt.savefig(img_path)
    print(f"[TGO ThermoAdaptive] Plot saved: {img_path}")

if __name__ == "__main__":
    run_thermo_adaptive()
