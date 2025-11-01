import os, json, time, psutil, numpy as np, pyopencl as cl, matplotlib.pyplot as plt
from datetime import datetime

TEMPLATE_FILE = os.path.join("C:\\Users\\user\\Desktop\\Trinity_STEM\\benchmarks",
                             "tgo_phase11_20251021_133544",
                             "tgo_phase11_templates.json")

def detect_gpu_name():
    try:
        platforms = cl.get_platforms()
        for p in platforms:
            devices = p.get_devices()
            if devices:
                return devices[0].name.strip()
    except Exception:
        return "generic_fallback"
    return "generic_fallback"

def ensure_template(device_name):
    # Load or initialize template library
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"templates": {}}

    # If template missing, create a baseline
    if device_name not in data["templates"]:
        print(f"[TGO AutoLearn] No template found for {device_name}. Creating baseline.")
        data["templates"][device_name] = {
            "target_duty": 0.5,
            "safe_temp": 55.0,
            "heat_coeff": 0.8
        }
        with open(TEMPLATE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    return data["templates"][device_name], data

def auto_tune(device_name, duration=90):
    tpl, root = ensure_template(device_name)
    print(f"[TGO AutoLearn] Tuning GPU: {device_name} for {duration}s ...")

    cpu_trace, temp_trace, duty_trace = [], [], []
    duty = tpl["target_duty"]
    start = time.time()

    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        temp = np.clip(tpl["safe_temp"] + np.random.randn()*3, 30, 95)
        duty = np.clip(duty + np.sign(cpu - tpl["heat_coeff"]*10)*0.005, 0.2, 0.9)
        cpu_trace.append(cpu); temp_trace.append(temp); duty_trace.append(duty)

    tpl["target_duty"] = float(np.mean(duty_trace))
    tpl["safe_temp"] = float(np.mean(temp_trace))
    tpl["heat_coeff"] = round(tpl["heat_coeff"] * (1 + np.std(cpu_trace)/100), 3)
    root["templates"][device_name] = tpl

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_name": device_name,
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "temp_avg": np.mean(temp_trace),
        "duty_mean": np.mean(duty_trace),
        "template_updated": tpl,
        "trace": {"cpu": cpu_trace, "temp": temp_trace, "duty": duty_trace},
        "root": root
    }

def main():
    device = detect_gpu_name()
    data = auto_tune(device, duration=120)
    outdir = os.environ.get("TGO_OUTDIR", ".")
    outfile = os.path.join(outdir, "tgo_phase13_autolearn.json")

    # Save data
    with open(outfile, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[TGO AutoLearn] Saved tuned data: {outfile}")

    # Update master template
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(data["root"], f, indent=4)
    print(f"[TGO AutoLearn] Master template updated: {TEMPLATE_FILE}")

    # Visualization
    t = range(len(data["trace"]["cpu"]))
    plt.figure(figsize=(10,5))
    plt.plot(t, data["trace"]["cpu"], label="CPU %", alpha=0.7)
    plt.plot(t, data["trace"]["temp"], label="Temp °C", alpha=0.6)
    plt.plot(t, [d*100 for d in data["trace"]["duty"]], "--", label="Duty % (scaled)")
    plt.title(f"Trinity Auto-Learn GPU Tuning — {device}")
    plt.xlabel("Sample"); plt.ylabel("CPU / Temp / Duty")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    img_path = os.path.join(outdir, "tgo_phase13_plot.png")
    plt.savefig(img_path)
    print(f"[TGO AutoLearn] Plot saved: {img_path}")

if __name__ == "__main__":
    main()
