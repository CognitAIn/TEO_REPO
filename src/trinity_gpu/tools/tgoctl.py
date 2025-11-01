import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tgo_agent

def run():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print("[TGO] Active GPU frameworks detected:", list(tgo_agent.GPU_BACKENDS.keys()))

    elif cmd == "run":
        tgo_agent.run_observer(15)

    elif cmd == "active":
        from trinity_gpu.tgo_active import run_active
        dur = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        run_active(dur)

    elif cmd == "efficiency":
        try:
            from trinity_gpu.tgo_efficiency import run_efficiency_test
            dur = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            duty = 0.8
            if "--duty" in sys.argv:
                duty = float(sys.argv[sys.argv.index("--duty") + 1])
            print(json.dumps(run_efficiency_test(dur, duty), indent=4))
        except ImportError as e:
            print("⚠ Efficiency module not found. Make sure tgo_efficiency.py exists.")
            print("Details:", e)

    else:
        print("Usage: python tgoctl.py [status|run|active <seconds>|efficiency <seconds> --duty <value>]")

if __name__ == "__main__":
    run()
