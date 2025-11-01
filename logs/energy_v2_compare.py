import json, pathlib, statistics
root = pathlib.Path(__file__).resolve().parent
v1 = json.load(open(root.parent/"energy"/"energy_results.json"))
v2 = json.load(open(root/"energy_v2_results.json"))
delta = {
    "timestamp": v2["timestamp"] if "timestamp" in v2 else None,
    "cpu_avg_drop_%": round((v1["orchestrated"]["cpu_avg"] - v2["cpu_avg"]) / v1["orchestrated"]["cpu_avg"] * 100, 2),
    "throughput_gain_%": round((v2["work_ops"] - v1["orchestrated"]["work_ops"]) / v1["orchestrated"]["work_ops"] * 100, 2),
    "mem_stability_%": round(100 - abs(v2["mem_avg"] - v1["orchestrated"]["mem_avg"]) / v1["orchestrated"]["mem_avg"] * 100, 2)
}
print(json.dumps(delta, indent=4))
