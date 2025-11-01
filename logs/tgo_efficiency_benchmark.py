import os, time, json, statistics, argparse
import psutil
try:
    import pyopencl as cl
    import numpy as np
    OPENCL_OK = True
except Exception as e:
    OPENCL_OK = False

def monitor_samples(stop_flag, cpu_samples, mem_samples, period=1.0):
    while not stop_flag["stop"]:
        cpu_samples.append(psutil.cpu_percent(interval=None))
        mem_samples.append(psutil.virtual_memory().percent)
        time.sleep(period)

def setup_opencl(prefer_gpu=True):
    if not OPENCL_OK:
        raise RuntimeError("PyOpenCL not available")
    ctx = None
    # Try to find a GPU device first (Intel iGPU), else any device
    for platform in cl.get_platforms():
        devs = platform.get_devices(device_type=cl.device_type.GPU if prefer_gpu else cl.device_type.ALL)
        if devs:
            ctx = cl.Context([devs[0]])
            break
    if ctx is None:
        # Fallback: any device available
        for platform in cl.get_platforms():
            devs = platform.get_devices()
            if devs:
                ctx = cl.Context([devs[0]])
                break
    if ctx is None:
        raise RuntimeError("No OpenCL device found")
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
    dev = ctx.devices[0]
    return ctx, queue, dev

KERNEL_SRC = r"""
__kernel void saxpy(const float a,
                    __global const float* x,
                    __global float* y)
{
    int gid = get_global_id(0);
    y[gid] = a * x[gid] + y[gid];
}
"""

def run_phase(label, duration_s, window_s, vec_size, orchestrated=False):
    phase_start = time.time()
    cpu_samples, mem_samples = [], []
    stop_flag = {"stop": False}

    # Light threadless sampler (non-blocking): just poll inline on window boundaries
    # If you ever need a separate thread, you can switch to threading.Thread(target=monitor_samples,...)

    work_ops = 0
    kernel_times_ms = []

    if OPENCL_OK:
        ctx, queue, dev = setup_opencl(prefer_gpu=True)
        import pyopencl as cl
        import numpy as np
        mf = cl.mem_flags
        # Buffers ~ 4M floats ~ 16MB each vector by default
        x = np.ones(vec_size, dtype=np.float32)
        y = np.zeros(vec_size, dtype=np.float32)
        a = np.float32(2.0)
        buf_x = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=x)
        buf_y = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=y)
        prg = cl.Program(ctx, KERNEL_SRC).build()
        global_size = (vec_size,)
        local_size  = None
    else:
        # CPU fallback with NumPy (still allows end-to-end test)
        import numpy as np
        a = 2.0
        x = np.ones(vec_size, dtype=np.float32)
        y = np.zeros(vec_size, dtype=np.float32)

    # Simple energy-aware broker target: reduce duty when CPU is high
    # duty in [0.25, 0.85], default ~0.65
    def target_duty(cpu_now):
        base = 0.65
        adjust = -0.004 * max(0.0, cpu_now - 20.0)
        d = min(0.85, max(0.25, base + adjust))
        return d

    try:
        while (time.time() - phase_start) < duration_s:
            frame_start = time.time()
            # sample CPU/mem once per window for stats and broker
            cpu_now = psutil.cpu_percent(interval=None)
            mem_now = psutil.virtual_memory().percent
            cpu_samples.append(cpu_now)
            mem_samples.append(mem_now)

            # compute time budget for work in this window
            if orchestrated:
                duty = target_duty(cpu_now)
            else:
                duty = 1.0
            work_budget = window_s * duty
            deadline = frame_start + work_budget

            # perform as many kernels as we can inside the budget
            ops_this_window = 0
            while time.time() < deadline:
                if OPENCL_OK:
                    evt = prg.saxpy(queue, global_size, local_size, np.float32(2.0), buf_x, buf_y)
                    evt.wait()
                    # profile kernel time
                    kt = (evt.profile.end - evt.profile.start) * 1e-6  # ms
                    kernel_times_ms.append(kt)
                else:
                    # CPU fallback
                    y = 2.0 * x + y
                ops_this_window += 1

            work_ops += ops_this_window

            # sleep remaining idle time in window
            elapsed = time.time() - frame_start
            to_sleep = max(0.0, window_s - elapsed)
            if to_sleep > 0:
                time.sleep(to_sleep)
    finally:
        stop_flag["stop"] = True

    # Summarize
    dur = time.time() - phase_start
    metrics = {
        "phase": label,
        "device": ("OpenCL: " + (dev.name if OPENCL_OK else "CPU-NumPy")),
        "duration": round(dur, 3),
        "cpu_avg": round(statistics.mean(cpu_samples), 2) if cpu_samples else None,
        "cpu_peak": round(max(cpu_samples), 2) if cpu_samples else None,
        "mem_avg": round(statistics.mean(mem_samples), 2) if mem_samples else None,
        "mem_peak": round(max(mem_samples), 2) if mem_samples else None,
        "work_ops": int(work_ops),
        "ops_per_sec": round(work_ops / dur, 3) if dur > 0 else None,
    }
    if kernel_times_ms:
        metrics.update({
            "kernel_ms_avg": round(statistics.mean(kernel_times_ms), 3),
            "kernel_ms_p95": round(np.percentile(kernel_times_ms, 95), 3) if OPENCL_OK else None,
        })
    return metrics

def compare(a, b):
    # b is orchestrated
    comp = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": b.get("device", "unknown"),
        "work_ops_baseline": a["work_ops"],
        "work_ops_orchestrated": b["work_ops"],
        "ops_sec_baseline": a["ops_per_sec"],
        "ops_sec_orchestrated": b["ops_per_sec"],
        "throughput_ratio": round((b["ops_per_sec"] / a["ops_per_sec"]), 3) if a["ops_per_sec"] else None,
        "cpu_avg_baseline": a["cpu_avg"],
        "cpu_avg_orchestrated": b["cpu_avg"],
        "cpu_drop_pct": round(((a["cpu_avg"] - b["cpu_avg"]) / a["cpu_avg"]) * 100.0, 2) if a["cpu_avg"] else None,
        "mem_avg_baseline": a["mem_avg"],
        "mem_avg_orchestrated": b["mem_avg"],
        "efficiency_ops_per_cpu_baseline": round(a["ops_per_sec"] / max(1e-6, a["cpu_avg"]), 3) if a["cpu_avg"] else None,
        "efficiency_ops_per_cpu_orchestrated": round(b["ops_per_sec"] / max(1e-6, b["cpu_avg"]), 3) if b["cpu_avg"] else None,
    }
    if "kernel_ms_avg" in a and "kernel_ms_avg" in b:
        comp.update({
            "kernel_ms_avg_baseline": a.get("kernel_ms_avg"),
            "kernel_ms_avg_orchestrated": b.get("kernel_ms_avg"),
            "kernel_ms_p95_baseline": a.get("kernel_ms_p95"),
            "kernel_ms_p95_orchestrated": b.get("kernel_ms_p95"),
        })
    return comp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=45, help="seconds per phase")
    ap.add_argument("--window", type=float, default=0.05, help="seconds per control window")
    ap.add_argument("--size", type=int, default=4_194_304, help="vector length (floats)")
    ap.add_argument("--out", type=str, default=r"tgo_efficiency_results.json")
    args = ap.parse_args()

    print(f"[baseline] OpenCL test, duration={args.duration}s, window={args.window}s, size={args.size}")
    base = run_phase("baseline", args.duration, args.window, args.size, orchestrated=False)
    print(json.dumps(base, indent=4))

    print(f"\n[orchestrated] Energy-aware duty cycle enabled")
    orch = run_phase("orchestrated", args.duration, args.window, args.size, orchestrated=True)
    print(json.dumps(orch, indent=4))

    comp = compare(base, orch)
    print("\n--- Comparison ---")
    print(json.dumps(comp, indent=4))

    out_path = os.path.abspath(args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"baseline": base, "orchestrated": orch, "comparison": comp}, f, indent=4)
    print(f"\nResults written to: {out_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        raise
