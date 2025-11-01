import time, json, datetime, psutil

# Attempt imports for all major vendors
GPU_BACKENDS = {}
try:
    import GPUtil
    GPU_BACKENDS["nvidia"] = "GPUtil"
except Exception:
    pass
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_BACKENDS["nvidia_nvml"] = "NVML"
except Exception:
    pass
try:
    import torch
    if torch.cuda.is_available():
        GPU_BACKENDS["cuda"] = "PyTorch CUDA"
    elif hasattr(torch, "hip") and torch.hip.is_available():
        GPU_BACKENDS["amd"] = "ROCm"
except Exception:
    pass
try:
    import pyopencl as cl
    platforms = cl.get_platforms()
    if platforms:
        GPU_BACKENDS["intel"] = "OpenCL"
except Exception:
    pass

def snapshot():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    gpus = []
    # Try all GPU backends sequentially
    if "nvidia" in GPU_BACKENDS:
        try:
            gpus = [{"id": g.id, "load": g.load*100, "mem": g.memoryUtil*100} for g in GPUtil.getGPUs()]
        except Exception:
            pass
    elif "nvidia_nvml" in GPU_BACKENDS:
        try:
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(h)
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                gpus.append({
                    "id": i,
                    "load": util.gpu,
                    "mem": 100 * mem.used / mem.total
                })
        except Exception:
            pass
    elif "amd" in GPU_BACKENDS:
        try:
            gpus = [{"id": 0, "load": torch.cuda.utilization(), "mem": torch.cuda.memory_allocated()/torch.cuda.max_memory_allocated()*100}]
        except Exception:
            pass
    elif "intel" in GPU_BACKENDS:
        try:
            gpus = [{"id": 0, "load": 0.0, "mem": 0.0, "vendor": "Intel"}]
        except Exception:
            pass
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu": cpu,
        "mem": mem,
        "gpu": gpus,
        "active_backends": GPU_BACKENDS
    }

def run_observer(duration=20, out_path="observer_report.json"):
    data=[]
    start = time.time()
    print(f"[TGO] Observer running {duration}s  | Active backends: {list(GPU_BACKENDS.keys())}")
    while time.time()-start < duration:
        snap = snapshot()
        data.append(snap)
        gtxt = f" GPU: {[round(g['load'],1) for g in snap['gpu']]}" if snap['gpu'] else ""
        print(f"[{snap['timestamp']}] CPU={snap['cpu']:.1f}% MEM={snap['mem']:.1f}%{gtxt}")
        time.sleep(1)
    json.dump(data, open(out_path,"w"), indent=4)
    print(f"\n[✓] Report saved: {out_path}")

if __name__ == "__main__":
    run_observer(20)
