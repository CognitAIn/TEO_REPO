import json, time, sys
from pathlib import Path
import argparse

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("orchestrated")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a = load(args.baseline)
    b = load(args.orchestrated)
    delta = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_avg_change": round(b["cpu_avg"] - a["cpu_avg"], 2),
        "cpu_peak_change": round(b["cpu_peak"] - a["cpu_peak"], 2),
        "mem_avg_change": round(b["mem_avg"] - a["mem_avg"], 2),
        "mem_peak_change": round(b["mem_peak"] - a["mem_peak"], 2),
        "duration_ratio": round(b["duration"]/a["duration"], 2) if a["duration"] else None
    }
    Path(args.out).write_text(json.dumps(delta, indent=4), encoding="utf-8")
    print(json.dumps(delta, indent=4))

if __name__ == "__main__":
    main()
