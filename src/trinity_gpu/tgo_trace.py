import os, time, json, psutil, numpy as np, matplotlib.pyplot as plt
from datetime import datetime

def run_cycle(label, duration=15, trinity_active=False):
    cpu, temp, duty = [], [], []
    base_duty = 0.7 if trinity_active else 0.5
    alpha = 0.25 if trinity_active else 0.0
    for _ in range(int(duration*2)):
        usage = psutil.cpu_percent(interval=0.5)
        base_temp = 50 + (usage/20) + (5*np.random.rand())
        base_duty = np.clip(base_duty + alpha*(usage-50)/100, 0.2, 0.9)
        cpu.append(usage); temp.append(base_temp); duty.append(base_duty)
    result = {
        "label": label,
        "cpu_avg": np.mean(cpu),
        "temp_avg": np.mean(temp),
        "duty_mean": np.mean(duty)
    }
    print(f"[{label}] Done — CPU {result['cpu_avg']:.2f}% | Temp {result['temp_avg']:.1f}°C | Duty {result['duty_mean']:.2f}")
    return result

def main():
    outdir = os.environ.get("TGO_OUTDIR", ".")
    base = run_cycle("Baseline_Test", duration=15, trinity_active=False)
    active = run_cycle("Trinity_Test", duration=15, trinity_active=True)
    data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "baseline": base, "active": active}
    path = os.path.join(outdir, "tgo_trace_result.json")
    with open(path, "w") as f: json.dump(data, f, indent=4)
    print(f"[TGO Trace] Saved trace result to {path}")

if __name__ == "__main__":
    main()
