import time, psutil, numpy as np, json, pyopencl as cl

def run_efficiency_test(duration=60, duty=0.8):
    start = time.time()
    ctx = cl.create_some_context(interactive=False)
    queue = cl.CommandQueue(ctx)
    dev = ctx.devices[0]
    device_name = f"OpenCL: {dev.name}"

    baseline_data = []
    orchestrated_data = []

    def sample_phase(tag, duty_cycle):
        readings = []
        t0 = time.time()
        while time.time() - t0 < duration:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            # create a dummy OpenCL kernel to simulate workload
            a_np = np.random.rand(256).astype(np.float32)
            b_np = np.random.rand(256).astype(np.float32)
            mf = cl.mem_flags
            a_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a_np)
            b_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b_np)
            prg = cl.Program(ctx, """
            __kernel void add(__global const float *a, __global const float *b, __global float *c) {
                int gid = get_global_id(0);
                c[gid] = a[gid] + b[gid];
            }""").build()
            c_g = cl.Buffer(ctx, mf.WRITE_ONLY, a_np.nbytes)
            start_evt = prg.add(queue, a_np.shape, None, a_g, b_g, c_g)
            start_evt.wait()
            elapsed = 1000 * (time.time() - t0)
            readings.append({
                "phase": tag,
                "cpu": cpu,
                "mem": mem,
                "elapsed_ms": elapsed
            })
            time.sleep(max(0.001, (1 - duty_cycle) * 0.5))
        return readings

    # Run both test phases
    baseline_data = sample_phase("baseline", 1.0)
    orchestrated_data = sample_phase("orchestrated", duty)

    def summarize(data):
        cpu = [d["cpu"] for d in data]
        mem = [d["mem"] for d in data]
        return {
            "cpu_avg": np.mean(cpu),
            "mem_avg": np.mean(mem),
            "samples": len(data)
        }

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": device_name,
        "baseline": summarize(baseline_data),
        "orchestrated": summarize(orchestrated_data),
        "cpu_drop_pct": round(100 * (summarize(baseline_data)["cpu_avg"] - summarize(orchestrated_data)["cpu_avg"]) / summarize(baseline_data)["cpu_avg"], 2)
    }
    return results

if __name__ == "__main__":
    print(json.dumps(run_efficiency_test(30, 0.8), indent=4))
