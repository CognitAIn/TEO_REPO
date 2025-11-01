import asyncio, json, psutil, time, statistics, sys
from pathlib import Path

# Ensure parent directory (Trinity_STEM) is on sys.path
root = Path(__file__).resolve().parent.parent
sys.path.extend([str(root), str(root / "loops"), str(root / "benchmarks")])

# Import from benchmarks directly
from benchmarks.bench_memory import run as run_memory
from benchmarks.bench_gaming import run as run_gaming
from benchmarks.bench_grid import run as run_grid


async def monitor_progress(start_time):
    while True:
        elapsed = time.time() - start_time
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        print(f"[{time.strftime('%H:%M:%S')}] ⏱  Elapsed {elapsed:.1f}s | CPU {cpu:.1f}% | MEM {mem:.1f}%")
        await asyncio.sleep(10)


async def run_with_progress(name, func):
    print(f"[{name}] starting...")
    result = await asyncio.to_thread(func)
    print(f"[{name}] done ✅")
    return result


async def composite():
    start = time.time()
    print("\n🚀 Running Trinity Δ₂ Composite Benchmark (Async Unified Mode + Progress Tracker)...\n")

    monitor = asyncio.create_task(monitor_progress(start))

    cpu_before = psutil.cpu_percent(interval=None)
    mem_before = psutil.virtual_memory().percent

    try:
        results = await asyncio.gather(
            run_with_progress("Memory", run_memory),
            run_with_progress("Gaming", run_gaming),
            run_with_progress("Grid", run_grid),
            return_exceptions=True
        )
    finally:
        monitor.cancel()

    cpu_after = psutil.cpu_percent(interval=None)
    mem_after = psutil.virtual_memory().percent
    end = time.time()

    durations = [r.get("duration", 0) if isinstance(r, dict) else 0 for r in results]
    latencies = [r.get("mean_latency", 0) if isinstance(r, dict) else 0 for r in results]

    composite = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_total": round(end - start, 3),
        "cpu_change": round(cpu_after - cpu_before, 2),
        "mem_change": round(mem_after - mem_before, 2),
        "durations": durations,
        "latencies": latencies,
        "mean_latency_global": round(statistics.mean(latencies), 4) if latencies else 0,
        "variance_latency": round(statistics.pstdev(latencies), 4) if latencies else 0
    }

    out_path = Path(root / "benchmarks" / "composite_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(composite, f, indent=4)

    print("\n✅ Composite Benchmark Complete.")
    print(f"   Duration: {composite['duration_total']}s | Mean Latency: {composite['mean_latency_global']}s")
    print(f"   CPU Δ: {composite['cpu_change']}% | MEM Δ: {composite['mem_change']}%")
    print(f"   Results saved → {out_path}")


if __name__ == "__main__":
    try:
        asyncio.run(composite())
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted manually.")
