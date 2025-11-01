import numpy as np, time, json, psutil, statistics, asyncio, pathlib, subprocess

root = pathlib.Path(__file__).resolve().parent
out_dir = root / "delta3_logs"
out_dir.mkdir(exist_ok=True)
cycles = 10
matrix_size = 1500  # tune for intensity

async def monitor_progress(label, start):
    while True:
        elapsed = time.time() - start
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        print(f"[{time.strftime('%H:%M:%S')}] ({label}) ⏱ {elapsed:.1f}s | CPU {cpu:.1f}% | MEM {mem:.1f}%")
        await asyncio.sleep(10)

def matrix_test(label):
    times = []
    print(f"\n[{label}] Starting matrix compute benchmark... {cycles} cycles, {matrix_size}x{matrix_size}")
    start = time.time()
    for i in range(cycles):
        A, B = np.random.rand(matrix_size, matrix_size), np.random.rand(matrix_size, matrix_size)
        t0 = time.time()
        _ = A @ B
        times.append(time.time() - t0)
        print(f"Cycle {i+1}/{cycles} -> {times[-1]:.4f}s")
    duration = time.time() - start
    return {
        "phase": label,
        "duration": round(duration, 2),
        "mean_cycle": round(statistics.mean(times), 4),
        "p95_cycle": round(np.percentile(times, 95), 4),
        "cpu_now": psutil.cpu_percent(interval=None),
        "mem_now": psutil.virtual_memory().percent
    }

async def run_phase(label, orchestrated=False):
    start = time.time()
    monitor = asyncio.create_task(monitor_progress(label, start))
    try:
        result = await asyncio.to_thread(matrix_test, label)
    finally:
        monitor.cancel()
    out_path = out_dir / f"{label}_metrics.json"
    json.dump(result, out_path.open("w"), indent=4)
    print(f"\n✔ {label} complete -> {out_path}")
    return result

def compare(a, b):
    diff = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mean_cycle_improvement": round(a["mean_cycle"] - b["mean_cycle"], 4),
        "p95_improvement": round(a["p95_cycle"] - b["p95_cycle"], 4),
        "cpu_delta": round(b["cpu_now"] - a["cpu_now"], 2),
        "mem_delta": round(b["mem_now"] - a["mem_now"], 2),
        "duration_ratio": round(b["duration"] / a["duration"], 2)
    }
    out_path = out_dir / "comparison_results.json"
    json.dump(diff, out_path.open("w"), indent=4)
    print("\n--- Δ₃ Comparison Results ---")
    print(json.dumps(diff, indent=4))
    return diff

async def main():
    baseline = await run_phase("baseline", orchestrated=False)
    print("\nLaunching Trinity orchestrator...\n")
    orch = subprocess.Popen(["python", "-u", str(root.parent / "run_trinity.py")])
    await asyncio.sleep(15)  # warm-up
    orchestrated = await run_phase("orchestrated", orchestrated=True)
    orch.terminate()
    compare(baseline, orchestrated)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⚠️ Interrupted manually.")

