import psutil, time, json, numpy as np
from tqdm import trange

def adaptive_feedback(duration=60, duty=0.8, alpha=0.25):
    """Adaptive feedback loop with variance learning"""
    cpu_samples, mem_samples, duty_trace = [], [], []
    last_adj = time.time()
    t_end = time.time() + duration
    base_duty = duty

    print(f"[TGO Adaptive] running {duration}s  duty={duty} α={alpha}")

    while time.time() < t_end:
        # collect system metrics
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        cpu_samples.append(cpu)
        mem_samples.append(mem)

        # adaptive adjustment (every 5s)
        if time.time() - last_adj > 5:
            variance = np.var(cpu_samples[-10:]) if len(cpu_samples) >= 10 else 0
            # proportional correction: higher variance → lower duty
            duty = max(0.3, min(1.0, base_duty - alpha * (variance / 10)))
            duty_trace.append(duty)
            last_adj = time.time()

        # simulate orchestration work (duty ratio)
        work_time = 0.02 * duty  # nominal GPU cycle
        time.sleep(work_time)

    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(cpu_samples),
        "cpu_avg": float(np.mean(cpu_samples)),
        "mem_avg": float(np.mean(mem_samples)),
        "duty_trace": duty_trace,
        "duty_mean": float(np.mean(duty_trace) if duty_trace else base_duty)
    }
    print(json.dumps(result, indent=4))
    return result

if __name__ == "__main__":
    adaptive_feedback(90, 0.8)
