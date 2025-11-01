import time, json, psutil, statistics
from pathlib import Path

def run_baseline(duration=60):
    print("📊 Baseline probe running...")
    cpu, mem = [], []
    start = time.time()
    while time.time() - start < duration:
        cpu.append(psutil.cpu_percent(interval=1))
        mem.append(psutil.virtual_memory().percent)
    data = {
        "phase": "baseline",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": round(time.time() - start, 2),
        "cpu_avg": round(statistics.mean(cpu), 2),
        "cpu_peak": round(max(cpu), 2),
        "mem_avg": round(statistics.mean(mem), 2),
        "mem_peak": round(max(mem), 2)
    }
    Path("benchmarks").mkdir(exist_ok=True)
    with open("benchmarks/baseline_results.json","w") as f:
        json.dump(data,f,indent=4)
    print("✅ Baseline complete.")
    return data

if __name__ == "__main__":
    run_baseline()
