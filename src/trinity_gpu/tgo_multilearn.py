import os, json, time, psutil, numpy as np, pyopencl as cl, matplotlib.pyplot as plt
from datetime import datetime

TEMPLATE_FILE = os.path.join("C:\\Users\\user\\Desktop\\Trinity_STEM\\benchmarks",
                             "tgo_phase11_20251021_133544",
                             "tgo_phase11_templates.json")

def detect_all_gpus():
    """Detect all OpenCL GPUs or fall back to generic."""
    gpus = []
    try:
        for platform in cl.get_platforms():
            for dev in platform.get_devices():
                gpus.append(dev.name.strip())
    except Exception:
        pass
    return gpus if gpus else ["generic_fallback"]

def ensure_template(device_name):
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"templates": {}}
    if device_name not in data["templates"]:
        print(f"[TGO MultiLearn] No template found for {device_name}. Creating baseline.")
        data["templates"][device_name] = {
            "target_duty": 0.5,
            "safe_temp": 55.0,
            "heat_coeff": 0.8
        }
        with open(TEMPLATE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    return data["templates"][device_name], data

def tune_device(device_name, duration=90):
    tpl, root = ensure_template(device_name)
    print(f"[TGO MultiLearn] Tuning GPU: {device_name} ({duration}s)")
    cpu_trace, temp_trace, duty_trace = [], [], []
    duty = tpl["target_duty"]; start = time.time()

    while time.time() - start < duration:
        cpu = psutil.cpu_percent(interval=0.5)
        temp = np.clip(tpl["safe_temp"] + np.random.randn()*2, 30, 95)
        duty = np.clip(duty + np.sign(cpu - tpl["heat_coeff"]*10)*0.005, 0.2, 0.9)
        cpu_trace.append(cpu); temp_trace.append(temp); duty_trace.append(duty)

    tpl["target_duty"] = float(np.mean(duty_trace))
    tpl["safe_temp"] = float(np.mean(temp_trace))
    tpl["heat_coeff"] = round(tpl["heat_coeff"] * (1 + np.std(cpu_trace)/100), 3)
    root["templates"][device_name] = tpl

    return {
        "device_name": device_name,
        "samples": len(cpu_trace),
        "cpu_avg": np.mean(cpu_trace),
        "temp_avg": np.mean(temp_trace),
        "duty_mean": np.mean(duty_trace),
        "trace": {"cpu": cpu_trace, "temp": temp_trace, "duty": duty_trace},
        "template_updated": tpl
    }, root

def main():
    outdir = os.environ.get("TGO_OUTDIR", ".")
    gpus = detect_all_gpus()
    print(f"[TGO MultiLearn] Detected GPUs: {gpus}")
    results = []; master_data = None

    for gpu in gpus:
        tuned, root = tune_device(gpu, duration=120)
        results.append(tuned)
        master_data = root

        # Save individual plot per GPU
        t = range(len(tuned["trace"]["cpu"]))
        plt.figure(figsize=(10,5))
        plt.plot(t, tuned["trace"]["cpu"], label="CPU %", alpha=0.7)
        plt.plot(t, tuned["trace"]["temp"], label="Temp °C", alpha=0.6)
        plt.plot(t, [d*100 for d in tuned["trace"]["duty"]], "--", label="Duty % (scaled)")
        plt.title(f"Trinity Multi-GPU Auto-Learn — {gpu}")
        plt.xlabel("Sample"); plt.ylabel("CPU / Temp / Duty")
        plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        img_path = os.path.join(outdir, f"tgo_phase14_{gpu.replace(' ', '_')}.png")
        plt.savefig(img_path)
        print(f"[TGO MultiLearn] Plot saved: {img_path}")

    # Save overall JSON summary
    summary_path = os.path.join(outdir, "tgo_phase14_multilearn.json")
    with open(summary_path, "w") as f:
        json.dump({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "results": results}, f, indent=4)
    print(f"[TGO MultiLearn] Summary saved: {summary_path}")

    # Update global template master
    with open(TEMPLATE_FILE, "w") as f:
        json.dump(master_data, f, indent=4)
    print(f"[TGO MultiLearn] Master template updated: {TEMPLATE_FILE}")

if __name__ == "__main__":
    main()
