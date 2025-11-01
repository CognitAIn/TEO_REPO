import time, json, psutil, statistics, pathlib, asyncio

root = pathlib.Path(__file__).resolve().parent
bench_dir = root
results = {}

async def monitor_progress(label, start_time):
    while True:
        elapsed = time.time() - start_time
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        print(f"[{time.strftime('%H:%M:%S')}] ({label}) ? Elapsed {elapsed:.1f}s | CPU {cpu:.1f}% | MEM {mem:.1f}%")
        await asyncio.sleep(10)

async def run_probe(label, orchestrated=False):
    start = time.time()
    samples_cpu, samples_mem = [], []
    duration = 60  # 1-minute runtime
    print(f"\n[{label.upper()}] starting {'(orchestrated)' if orchestrated else '(baseline)'} probe...")
    monitor = asyncio.create_task(monitor_progress(label, start))
    try:
        for _ in range(duration):
            samples_cpu.append(psutil.cpu_percent(interval=1))
            samples_mem.append(psutil.virtual_memory().percent)
    finally:
        monitor.cancel()
    runtime = time.time() - start
    metrics = {
        "phase": label,
        "orchestrated": orchestrated,
        "duration": round(runtime, 2),
        "cpu_avg": round(statistics.mean(samples_cpu), 2),
        "cpu_peak": round(max(samples_cpu), 2),
        "mem_avg": round(statistics.mean(samples_mem), 2),
        "mem_peak": round(max(samples_mem), 2),
    }
    out_path = bench_dir / f"{label}_metrics.json"
    json.dump(metrics, out_path.open("w"), indent=4)
    print(f"? {label} probe complete ? {out_path.name}")
    return metrics

def compare(a, b):
    delta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_avg_improvement": round(a["cpu_avg"] - b["cpu_avg"], 2),
        "mem_avg_improvement": round(a["mem_avg"] - b["mem_avg"], 2),
        "runtime_ratio": round(b["duration"]/a["duration"], 2),
        "cpu_peak_change": round(b["cpu_peak"] - a["cpu_peak"], 2),
        "mem_peak_change": round(b["mem_peak"] - a["mem_peak"], 2),
    }
    out = bench_dir / "performance_comparison.json"
    json.dump(delta, out.open("w"), indent=4)
    print(f"\n?? Comparison complete ? {out}")
    print(json.dumps(delta, indent=4))
    return delta

async def main():
    baseline = await run_probe("baseline", orchestrated=False)
    orchestrated = await run_probe("orchestrated", orchestrated=True)
    compare(baseline, orchestrated)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n?? Benchmark interrupted manually.")
