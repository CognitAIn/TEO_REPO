import argparse, time, json, psutil, statistics, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    start = time.time()
    cpu_samples, mem_samples = [], []
    for i in range(args.duration):
        cpu_samples.append(psutil.cpu_percent(interval=1))
        mem_samples.append(psutil.virtual_memory().percent)
        if (i+1) % 10 == 0:
            avg_cpu = sum(cpu_samples)/len(cpu_samples)
            avg_mem = sum(mem_samples)/len(mem_samples)
            print(f"[{time.strftime('%H:%M:%S')}] [{args.label}] {i+1}/{args.duration}s | CPU(avg) {avg_cpu:.1f}% | MEM(avg) {avg_mem:.1f}%")

    runtime = time.time() - start
    metrics = {
        "phase": args.label,
        "duration": round(runtime, 2),
        "cpu_avg": round(statistics.mean(cpu_samples), 2),
        "cpu_peak": round(max(cpu_samples), 2),
        "mem_avg": round(statistics.mean(mem_samples), 2),
        "mem_peak": round(max(mem_samples), 2)
    }
    Path(args.out).write_text(json.dumps(metrics, indent=4), encoding="utf-8")
    print(f"{args.label} done -> {args.out}")
    print(json.dumps(metrics, indent=4))

if __name__ == "__main__":
    main()
