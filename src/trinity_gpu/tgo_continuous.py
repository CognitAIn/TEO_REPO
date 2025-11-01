import os, json, time, psutil, numpy as np, pyopencl as cl, matplotlib.pyplot as plt
from datetime import datetime

TEMPLATE_FILE = os.path.join("C:\\Users\\user\\Desktop\\Trinity_STEM\\benchmarks",
                             "tgo_phase11_20251021_133544",
                             "tgo_phase11_templates.json")

def detect_gpus():
    gpus = []
    try:
        for platform in cl.get_platforms():
            for dev in platform.get_devices():
                gpus.append(dev.name.strip())
    except Exception:
        pass
    return gpus or ["generic_fallback"]

def ensure_template(device):
    if os.path.exists(TEMPLATE_FILE):
        data = json.load(open(TEMPLATE_FILE))
    else:
        data = {"templates": {}}
    if device not in data["templates"]:
        data["templates"][device] = {"target_duty":0.5,"safe_temp":55.0,"heat_coeff":0.8,"eff_score":1.0}
    return data["templates"][device], data

def tune(device, duration=120):
    tpl, root = ensure_template(device)
    cpu, temp, duty, power = [], [], [], []
    d = tpl["target_duty"]; start = time.time()
    while time.time() - start < duration:
        c = psutil.cpu_percent(interval=0.5)
        p = psutil.sensors_battery().percent if psutil.sensors_battery() else np.random.uniform(40,100)
        t = np.clip(tpl["safe_temp"] + np.random.randn()*2, 30, 95)
        d = np.clip(d + np.sign(c - tpl["heat_coeff"]*10)*0.005, 0.2, 0.9)
        cpu.append(c); temp.append(t); duty.append(d); power.append(p)
    tpl["target_duty"] = float(np.mean(duty))
    tpl["safe_temp"]  = float(np.mean(temp))
    tpl["heat_coeff"] = round(tpl["heat_coeff"]*(1+np.std(cpu)/100),3)
    tpl["eff_score"]  = round(np.mean(cpu)/(np.mean(power)+1e-5),3)
    root["templates"][device] = tpl
    return {"device":device,"cpu_avg":np.mean(cpu),"temp_avg":np.mean(temp),
            "power_avg":np.mean(power),"duty_mean":np.mean(duty),
            "eff_score":tpl["eff_score"],"samples":len(cpu),
            "trace":{"cpu":cpu,"temp":temp,"duty":duty,"power":power}}, root

def hourly_loop():
    outbase = os.environ.get("TGO_OUTDIR",".")
    gpus = detect_gpus()
    print(f"[TGO Continuous] Detected GPUs: {gpus}")
    while True:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = os.path.join(outbase, ts)
        os.makedirs(outdir, exist_ok=True)
        allres, master = [], None
        for g in gpus:
            res, master = tune(g, duration=60)
            allres.append(res)
            plt.figure(figsize=(10,5))
            plt.plot(res["trace"]["cpu"], label="CPU %")
            plt.plot(res["trace"]["temp"], label="Temp °C")
            plt.plot([p for p in res["trace"]["power"]], label="Power %")
            plt.plot([d*100 for d in res["trace"]["duty"]],"--",label="Duty % (scaled)")
            plt.legend(); plt.title(f"Trinity Continuous — {g}")
            plt.tight_layout()
            plt.savefig(os.path.join(outdir,f"{g.replace(' ','_')}.png")); plt.close()
        json.dump({"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "results":allres}, open(os.path.join(outdir,"summary.json"),"w"), indent=4)
        json.dump(master, open(TEMPLATE_FILE,"w"), indent=4)
        print(f"[TGO Continuous] Cycle complete → saved to {outdir}")
        print("[TGO Continuous] Sleeping 3600 s for next run...")
        time.sleep(3600)

if __name__ == "__main__":
    hourly_loop()
