import asyncio, time, random, psutil, json, statistics
from pathlib import Path

async def simulate(label, duration):
    print(f"[{label}] starting...")
    cpu, mem = [], []
    start = time.time()
    for _ in range(duration):
        cpu.append(psutil.cpu_percent(interval=1))
        mem.append(psutil.virtual_memory().percent)
        await asyncio.sleep(random.uniform(0.01,0.05))
    result = {
        "label": label,
        "duration": round(time.time() - start, 2),
        "cpu_avg": round(statistics.mean(cpu), 2),
        "mem_avg": round(statistics.mean(mem), 2)
    }
    print(f"[{label}] done ✅")
    return result

async def run_suite():
    print("🎯 Trinity Δ₂ Performance Suite active...")
    start = time.time()
    results = await asyncio.gather(
        simulate("Memory", 30),
        simulate("Gaming", 30),
        simulate("Grid", 30)
    )
    cpu_change = psutil.cpu_percent(interval=None)
    mem_use = psutil.virtual_memory().percent
    summary = {
        "phase": "Δ₂_performance_suite",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_total": round(time.time() - start, 2),
        "cpu_now": cpu_change,
        "mem_now": mem_use,
        "tasks": results
    }
    with open("benchmarks/delta2_suite_results.json", "w") as f:
        json.dump(summary, f, indent=4)
    print("✅ Δ₂ Performance Suite complete.")
    return summary

if __name__ == "__main__":
    asyncio.run(run_suite())
