#!/usr/bin/env python3
import asyncio
from tgo_core.config import load_config
from tgo_core.telemetry import Telemetry
from tgo_core.governor import ResonanceGovernor
from tgo_core.scheduler import HoloframeScheduler

async def main():
    cfg = load_config("tgo_config.yaml")
    telemetry = Telemetry(cfg)
    governor = ResonanceGovernor(cfg, telemetry)
    scheduler = HoloframeScheduler(cfg, telemetry, governor)
    await scheduler.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("TGO stopped by user.")
