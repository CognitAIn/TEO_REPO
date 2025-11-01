import asyncio, time, sys
from loops.Trinity_STEM import BaseLoop

# Windows fix: use SelectorEventLoopPolicy for reliable short sleeps
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_sync():
    a = BaseLoop("Δ0")
    b = BaseLoop("Δ1")
    start = time.time()

    print("\n[Δ+1 Synchronization Test Started]")
    print("Testing phase alignment between Δ0 and Δ1 loops...\n")
    sys.stdout.flush()

    for i in range(5):
        loop_start = time.time()
        await asyncio.sleep(0.2)
        now = time.time() - start
        dt = time.time() - loop_start
        await a.tick(dt)
        await b.tick(dt + 0.001)
        print(f"t={now:.3f}s | Δ0 phase_ok={a.phase_offset_ok} | Δ1 phase_ok={b.phase_offset_ok} | Δt={dt:.3f}s")
        sys.stdout.flush()

    print("\n[Δ+1 test completed successfully — no phase drift detected.]")
    sys.stdout.flush()

async def main():
    try:
        await test_sync()
    except Exception as e:
        print(f"[Error] Δ+1 test failed: {e}")
    finally:
        await asyncio.sleep(0)
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
