import time, json, psutil, statistics, asyncio, random
from pathlib import Path

async def orchestrated(duration=60):
    print("🧠 Δ₂ orchestrator active...")
    cpu, mem = [], []
    start = time.time()
    ewma, alpha, kp = None, 0.25, 0.85
    target = 0.15
    while time.time() - start < duration:
        drift = (ewma - target) if ewma else 0
        sleep_for = max(0.005, target - kp*drift + random.uniform(-0.01,0.01))
        t0 = time.time()
        await asyncio.sleep(sleep_for)
        ewma = (1-alpha)*ewma + alpha*(time.time()-t0) if ewma else (time.time()-t0)
        cpu.append(psutil.cpu_percent(interval=None))
        mem.append(psutil.virtual_memory().percent)
    data = {
        "phase": "orchestrated",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": round(time.time() - start, 2),
        "cpu_avg": round(statistics.mean(cpu), 2),
        "cpu_peak": round(max(cpu), 2),
        "mem_avg": round(statistics.mean(mem), 2),
        "mem_peak": round(max(mem), 2)
    }
    with open("benchmarks/orchestrated_results.json","w") as f:
        json.dump(data,f,indent=4)
    print("✅ Δ₂ Orchestrator complete.")
    return data

if __name__ == "__main__":
    asyncio.run(orchestrated())
