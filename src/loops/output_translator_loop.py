from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, json, csv, io, time

META = {
    "name": "OutputTranslatorLoop",
    "inputs": ["system.output.request"],
    "outputs": ["system.output.ready"],
    "description": "Converts output requests into formatted data strings (JSON, CSV, etc.) and publishes them."
}

class OutputTranslatorLoop(BaseLoop):
    """Self-healing translator loop with duplicate-load guard."""
    auto_start = True
    translated: int = 0          # <-- class-level default prevents attribute errors

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        # ensure instance attribute exists even before async init
        self.translated = getattr(self, "translated", 0)
        self._subscribed = False

    async def init(self):
        # prevent double subscription if Supervisor reloads twice
        if self._subscribed:
            return
        self._subscribed = True

        bus = get_bus()
        if bus:
            bus.subscribe("system.output.request", self._on_request)
        print(f"[Init] {self.name} subscribed to system.output.request")

    async def _on_request(self, msg):
        rid = msg.get("rid")
        fmt = (msg.get("format") or "json").lower()
        data = msg.get("data")
        result = None

        try:
            if fmt == "json":
                result = json.dumps(data, indent=2)

            elif fmt == "csv":
                output = io.StringIO()
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    output.write(str(data))
                result = output.getvalue()

            elif fmt == "text":
                result = str(data)

            else:
                result = f"[Unsupported format: {fmt}]"

            bus = get_bus()
            if bus:
                await bus.publish("system.output.ready", {
                    "rid": rid,
                    "format": fmt,
                    "result": result,
                    "timestamp": time.time()
                })

            self.translated += 1

        except Exception as e:
            print(f"[Error] {self.name} failed on {rid}: {e}")

    async def tick(self, dt):
        await asyncio.sleep(0)
        return {
            "id": self.name,
            "latency": dt,
            "translated": self.translated,
            "timestamp": time.time()
        }
