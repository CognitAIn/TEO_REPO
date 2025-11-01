import json, time, statistics
from pathlib import Path

def merge():
    b = json.load(open("benchmarks/baseline_results.json"))
    o = json.load(open("benchmarks/orchestrated_results.json"))
    p = json.load(open("benchmarks/delta2_suite_results.json"))
    delta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_delta_avg": round(o["cpu_avg"] - b["cpu_avg"], 2),
        "cpu_delta_peak": round(o["cpu_peak"] - b["cpu_peak"], 2),
        "mem_delta_avg": round(o["mem_avg"] - b["mem_avg"], 2),
        "mem_delta_peak": round(o["mem_peak"] - b["mem_peak"], 2),
        "runtime_ratio": round(o["duration"]/max(1e-9,b["duration"]),2),
        "suite_cpu_now": p["cpu_now"],
        "suite_mem_now": p["mem_now"],
        "suite_duration": p["duration_total"]
    }
    with open("benchmarks/master_summary.json","w") as f:
        json.dump(delta,f,indent=4)
    print("\\n--- 🧩 Trinity Δ₂ Master Summary ---\\n")
    for k,v in delta.items(): print(f"{k:20}: {v}")
    print("\\nResults saved → benchmarks/master_summary.json")

if __name__ == "__main__":
    merge()
