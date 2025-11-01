from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, time

META = {
    "name": "OutputRouterLoop",
    "inputs": ["system.input.cleaned"],
    "outputs": ["system.output.request"],
    "description": "Routes cleaned input into output requests when payload declares an output job."
}

class OutputRouterLoop(BaseLoop):
    auto_start = True

    async def init(self):
        self.forwarded = 0
        bus = get_bus()
        if bus:
            bus.subscribe("system.input.cleaned", self._on_cleaned)
        print(f"[Init] {self.name} watching system.input.cleaned")

    async def _on_cleaned(self, msg):
        content = msg.get("content")
        if isinstance(content, dict) and (content.get("route") == "output" or msg.get("route") == "output"):
            rid = content.get("rid") or msg.get("rid")
            fmt = (content.get("format") or msg.get("format") or "json").lower()
            data = content.get("data") if "data" in content else content
            bus = get_bus()
            if bus:
                await bus.publish("system.output.request", {
                    "rid": rid,
                    "format": fmt,
                    "data": data,
                    "timestamp": time.time()
                })
                self.forwarded += 1

    async def tick(self, dt):
        await asyncio.sleep(0)
        return {
            "id": self.name,
            "latency": dt,
            "forwarded": self.forwarded,
            "timestamp": time.time()
        }
