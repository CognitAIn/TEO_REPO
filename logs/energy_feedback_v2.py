import time, json, psutil, threading, queue, statistics, argparse, random

class EnergyToken:
    """Represents a unit of 'energy' allocated to a worker thread."""
    def __init__(self, id, power=1.0): 
        self.id = id
        self.power = power
        self.timestamp = time.time()

class FractalEnergyBroker:
    """Adaptive energy allocator balancing work vs. thermodynamic load."""
    def __init__(self, max_tokens=4):
        self.max_tokens = max_tokens
        self.tokens = queue.Queue(maxsize=max_tokens)
        self.avg_cpu_window = []
        self.lock = threading.Lock()
        for i in range(max_tokens):
            self.tokens.put(EnergyToken(i))

    def sense(self):
        """Reads instantaneous CPU load and updates rolling window."""
        cpu = psutil.cpu_percent(interval=None)
        with self.lock:
            self.avg_cpu_window.append(cpu)
            if len(self.avg_cpu_window) > 10:
                self.avg_cpu_window.pop(0)
        return statistics.mean(self.avg_cpu_window)

    def allocate(self):
        """Hands out token if below adaptive threshold."""
        load = self.sense()
        threshold = 65 - (load * 0.1)  # adaptive headroom target
        if not self.tokens.empty() and load < threshold:
            return self.tokens.get()
        return None

    def release(self, token):
        if token:
            self.tokens.put(token)

def work_cycle(broker, stop_flag, results):
    ops = 0
    while not stop_flag.is_set():
        token = broker.allocate()
        if token:
            # simulate work proportional to energy
            span = 0.002 * token.power
            _ = sum(x*x for x in range(250))
            time.sleep(span)
            ops += 1
            broker.release(token)
        else:
            time.sleep(0.01)
    results.append(ops)

def run(duration=60, threads=4):
    broker = FractalEnergyBroker(max_tokens=threads)
    stop_flag = threading.Event()
    results = []
    workers = [threading.Thread(target=work_cycle, args=(broker, stop_flag, results)) for _ in range(threads)]
    [t.start() for t in workers]
    start = time.time()
    samples_cpu, samples_mem = [], []
    while time.time() - start < duration:
        samples_cpu.append(psutil.cpu_percent(interval=1))
        samples_mem.append(psutil.virtual_memory().percent)
        if int(time.time() - start) % 10 == 0:
            print(f"[{time.strftime('%H:%M:%S')}] ⏱ {int(time.time()-start)}s | CPU {samples_cpu[-1]:.1f}% | MEM {samples_mem[-1]:.1f}% | Tokens {broker.tokens.qsize()}")
    stop_flag.set()
    [t.join() for t in workers]
    runtime = time.time() - start
    metrics = {
        "duration": round(runtime,2),
        "cpu_avg": round(statistics.mean(samples_cpu),2),
        "mem_avg": round(statistics.mean(samples_mem),2),
        "cpu_peak": round(max(samples_cpu),2),
        "mem_peak": round(max(samples_mem),2),
        "work_ops": sum(results)
    }
    return metrics

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--out", type=str, default="energy_v2_results.json")
    args = ap.parse_args()
    print(f"[orchestrated_v2] running for {args.duration}s with {args.threads} threads")
    data = run(args.duration, args.threads)
    json.dump(data, open(args.out,"w"), indent=4)
    print(json.dumps(data, indent=4))
