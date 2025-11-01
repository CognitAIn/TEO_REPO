import time, threading, queue, random
from trinity_gpu.energy_tokenizer import TokenAllocator
from trinity_gpu.energy_router import EnergyRouter
try:
    # Optional: if your status path exposes backends
    from trinity_gpu import tgo_agent
    _BACKENDS = getattr(tgo_agent, "GPU_BACKENDS", {"cpu":{}})
except Exception:
    _BACKENDS = {"cpu":{}}

# OPTIONAL simple telemetry shims; return {"utilization": <0..100>}
def _nv_telemetry():
    try:
        import pynvml as nv
        nv.nvmlInit()
        h = nv.nvmlDeviceGetHandleByIndex(0)
        u = nv.nvmlDeviceGetUtilizationRates(h).gpu
        nv.nvmlShutdown()
        return {"utilization": float(u)}
    except Exception:
        return {"utilization": 50.0}

def _intel_telemetry():
    # Stub: many Windows systems lack a simple Intel GPU API in Python.
    return {"utilization": 50.0}

def build_router():
    get_telemetry = {}
    if "nvidia" in _BACKENDS:
        get_telemetry["nvidia"] = _nv_telemetry
    if "intel" in _BACKENDS:
        get_telemetry["intel"] = _intel_telemetry
    # always include cpu as fallback
    if "cpu" not in _BACKENDS:
        _BACKENDS["cpu"] = {}
        get_telemetry["cpu"] = lambda: {"utilization": 50.0}
    return EnergyRouter(_BACKENDS, get_telemetry=get_telemetry, frame_ms=100.0)

class WorkQueue:
    def __init__(self):
        self.q = queue.Queue()

    def submit(self, tok):
        self.q.put(tok)

    def drain(self, limit=32):
        items = []
        try:
            while len(items)<limit:
                items.append(self.q.get_nowait())
        except Exception:
            pass
        return items

def run_active(seconds:int=30, submit_rate_hz:float=10.0):
    alloc = TokenAllocator()
    router = build_router()
    wq = WorkQueue()

    # producer: emit forecast tokens
    stop = threading.Event()
    def producer():
        tid = 0
        period = 1.0/submit_rate_hz
        while not stop.is_set():
            tid += 1
            # random small jobs; importance & deadlines vary
            imp = random.uniform(0.3, 1.0)
            wu  = random.randint(50, 250)           # work units
            ddl = random.choice([0.0, 80.0, 160.0]) # ms
            tok = alloc.forecast_to_token(f"task-{tid}", imp, wu, deadline_ms=ddl)
            wq.submit(tok)
            time.sleep(period)

    t = threading.Thread(target=producer, daemon=True)
    t.start()

    print(f"[TGO Active] started for {seconds}s | backends={list(_BACKENDS.keys())}")
    t0 = time.time()
    frames = 0
    while (time.time() - t0) < seconds:
        tokens = wq.drain(limit=64)
        if tokens:
            ranked = alloc.rank(tokens)
            budgets = router.route(ranked)
            # Print a compact summary line (first few budgets)
            preview = ", ".join([f"{b.task_id}->{b.device}:{b.allow_ms:.0f}ms" for b in budgets[:5]])
            print(f"[frame {frames:05d}] assigned {len(budgets)} budgets | {preview}")
            # settle with an approximate actual energy (demo)
            for tok in ranked:
                alloc.settle(tok, actual_joules=tok.predicted_joules*random.uniform(0.8, 1.2))
        else:
            print(f"[frame {frames:05d}] idle")
        frames += 1
        time.sleep(0.1)

    stop.set()
    print("[TGO Active] done.")

if __name__ == "__main__":
    run_active(30, submit_rate_hz=12.0)
