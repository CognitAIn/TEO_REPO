import time, random, statistics
TARGET_FRAME = 1.0/60.0  # 60 FPS
SECS = 20

def work_ms():
    # variable frame work: physics/render/AI load
    base = random.uniform(0.004, 0.010)
    if random.random()<0.05: base += random.uniform(0.005, 0.020)  # spikes
    return base

def run(corrected=False):
    frames = []
    start = last = time.perf_counter()
    ewma=None; alpha=0.25; kp=0.7
    while time.perf_counter() - start < SECS:
        now = time.perf_counter(); dt = now - last; last = now
        # frame work
        time.sleep(work_ms())
        # sleep to next frame
        if corrected:
            ewma = dt if ewma is None else (1-alpha)*ewma + alpha*dt
            drift = ewma - TARGET_FRAME
            sleep_for = max(0.0, TARGET_FRAME - (time.perf_counter()-now) - kp*drift)
        else:
            sleep_for = max(0.0, TARGET_FRAME - (time.perf_counter()-now))
        time.sleep(sleep_for)
        frames.append(time.perf_counter() - now)

    frames.sort()
    p1low = frames[int(0.99*len(frames))]  # 1% low (worst)
    return {
        "fps_mean": 1.0/(sum(frames)/len(frames)),
        "fps_1pct_low": 1.0/p1low,
        "frame_stdev": statistics.pstdev(frames) if len(frames)>1 else 0.0
    }

if __name__ == "__main__":
    print("\n=== Game Loop Benchmark (Frame Stability) ===")
    base = run(False); d2 = run(True)
    def f(x): return f"{x:.2f}"
    print(f"Mean FPS            : base={f(base['fps_mean'])}  ->  D2={f(d2['fps_mean'])}")
    print(f"1% low FPS          : base={f(base['fps_1pct_low'])} ->  D2={f(d2['fps_1pct_low'])}")
    print(f"Frame stdev (s)     : base={base['frame_stdev']:.5f} ->  D2={d2['frame_stdev']:.5f}\n")

