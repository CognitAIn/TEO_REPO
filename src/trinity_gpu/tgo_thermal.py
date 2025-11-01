import json, time, psutil, numpy as np, matplotlib.pyplot as plt, os
from datetime import datetime

def run_thermal_governor(duration=150, alpha=0.3, heat_coeff=0.07, cool_coeff=0.05, temp_limit=80):
    print(f"[TGO Thermal] running {duration}s  α={alpha}  heat_coeff={heat_coeff}  limit={temp_limit}°C")
    cpu_trace, temp_trace, duty_trace = [], [], []
    duty, temp = 0.7, 40.0  # starting duty & nominal core temp
    start = time.time()

    def simulate_heat(cpu, duty, temp):
        heat_in = (cpu * heat_coeff) + (duty * 10 * heat_coeff)
        cool_out = (temp - 35) * cool_coeff
        return temp + heat_in - cool_out

    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        temp = simulate_heat(cpu, duty, temp)
        cpu_trace.append(cpu)
        temp_trace.append(temp)

        # feedback: reduce duty if overheating, raise if cool
        if temp > temp_limit:
            duty -= alpha * (temp - temp_limit) / 50
        elif temp < temp_limit - 10:
            duty += alpha * 0.05

        # minor adaptive CPU correction
        if cpu < 4: duty += 0.02
        elif cpu > 8: duty -= 0.02

        duty = np.clip(duty, 0.3, 0.9)
        duty_trace.append(duty)

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_trace),
        "cpu_avg": float(np.mean(cpu_trace)),
        "temp_avg": float(np.mean(temp_trace)),
        "temp_peak": float(np.max(temp_trace)),
        "duty_mean": float(np.mean(duty_trace)),
        "trace": {"cpu": cpu_trace, "temp": temp_trace, "duty": duty_trace}
    }

    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase11_thermal.json")
    with open(outfile, "w") as f:
        json.dump(result, f, indent=4)
    print(f"[TGO Thermal] JSON saved: {outfile}")

    # Plot visualization
    t = range(len(cpu_trace))
    plt.figure(figsize=(10,5))
    plt.plot(t, cpu_trace, label="CPU %", alpha=0.7)
    plt.plot(t, temp_trace, label="Simulated °C", alpha=0.6)
    plt.plot(t, [d*100 for d in duty_trace], "--", label="Duty % (scaled)")
    plt.xlabel("Sample"); plt.ylabel("Load / Temp / Duty")
    plt.title("Trinity Thermal Governor — Phase 11")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase11_plot.png")
    plt.savefig(img_path)
    print(f"[TGO Thermal] Plot saved: {img_path}")

if __name__ == "__main__":
    run_thermal_governor()
