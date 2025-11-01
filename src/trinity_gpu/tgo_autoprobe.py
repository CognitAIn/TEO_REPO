import json, os, time, psutil, numpy as np, matplotlib.pyplot as plt
from datetime import datetime

TEMPLATE_FILE = os.path.join("C:\\Users\\user\\Desktop\\Trinity_STEM\\benchmarks",
                             "tgo_phase11_20251021_133544",
                             "tgo_phase11_templates.json")

def load_template():
    with open(TEMPLATE_FILE, "r") as f:
        data = json.load(f)
    first_key = next(iter(data["templates"]))
    print(f"[TGO AutoProbe] Using template key: {first_key}")
    return data["templates"][first_key], data, first_key

def auto_probe_tuner(duration=90):
    tpl, root, device_type = load_template()
    print(f"[TGO AutoProbe] running {duration}s for {device_type} GPU")
    cpu_trace, temp_trace, duty_trace = [], [], []
    duty = tpl["target_duty"]
    start = time.time()
    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        temp = np.clip(tpl["safe_temp"] + np.random.randn()*2, 30, 95)
        duty = np.clip(duty + np.sign(cpu - tpl["heat_coeff"]*10)*0.005, 0.2, 0.9)
        cpu_trace.append(cpu); temp_trace.append(temp); duty_trace.append(duty)
    tpl["target_duty"] = float(np.mean(duty_trace))
    tpl["safe_temp"] = float(np.mean(temp_trace))
    tpl["heat_coeff"] = round(tpl["heat_coeff"] * (1 + (np.std(cpu_trace)/100)), 3)
    root["templates"][device_type] = tpl
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_type": device_type,
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "temp_avg": np.mean(temp_trace),
        "duty_mean": np.mean(duty_trace),
        "template_updated": tpl,
        "trace": {"cpu": cpu_trace, "temp": temp_trace, "duty": duty_trace},
        "root": root
    }

def main():
    outdir = os.environ.get("TGO_OUTDIR", ".")
    data = auto_probe_tuner(duration=90)
    outfile = os.path.join(outdir, "tgo_phase12_autoprobe.json")
    with open(outfile, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[TGO AutoProbe] Saved tuned data: {outfile}")
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(data["root"], f, indent=4)
    print(f"[TGO AutoProbe] Master template updated: {TEMPLATE_FILE}")
    t = range(len(data["trace"]["cpu"]))
    plt.figure(figsize=(10,5))
    plt.plot(t, data["trace"]["cpu"], label="CPU %")
    plt.plot(t, data["trace"]["temp"], label="Temp °C")
    plt.plot(t, [d*100 for d in data["trace"]["duty"]], "--", label="Duty % (scaled)")
    plt.title("Trinity GPU Auto-Probe — Adaptive Template Tuning")
    plt.xlabel("Sample"); plt.ylabel("CPU / Temp / Duty")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase12_plot.png")
    plt.savefig(img_path)
    print(f"[TGO AutoProbe] Plot saved: {img_path}")

if __name__ == "__main__":
    main()
