#!/usr/bin/env python3
import time, random, statistics, json, os

def workload():
    s = 0
    for _ in range(1000000):
        s += random.randint(0, 9)
    return s

def run_benchmark(runs=5):
    latencies = []
    for _ in range(runs):
        t0 = time.perf_counter()
        workload()
        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)
    return {
        "runs": runs,
        "latency_ms": latencies,
        "p50": statistics.median(latencies),
        "p95": sorted(latencies)[int(0.95 * len(latencies)) - 1],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

if __name__ == "__main__":
    os.makedirs("benchmarks/results", exist_ok=True)
    result = run_benchmark()
    with open("benchmarks/results/sample_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Benchmark completed. Results saved to benchmarks/results/sample_result.json")
