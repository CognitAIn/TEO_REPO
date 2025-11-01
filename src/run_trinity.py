import asyncio, sys
sys.path.append("loops")

from loops.Trinity_STEM import Supervisor

if __name__ == "__main__":
    try:
        asyncio.run(Supervisor(buffer_seconds=1.0).run())
    except KeyboardInterrupt:
        print("\n[Supervisor] Graceful shutdown.")
