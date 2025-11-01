from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, time, json, csv, io

META = {
    "name": "TranslatorLoop",
    "inputs": ["system.input.raw"],
    "outputs": ["system.input.cleaned", "system.input.error"],
    "description": "Classifies/sanitizes inbound payloads to Trinity-standard cleaned messages."
}

class TranslatorLoop(BaseLoop):
    auto_start = True

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.stats = {"ok": 0, "err": 0}

    async def init(self):
        bus = get_bus()
        if bus:
            bus.subscribe("system.input.raw", self._on_raw)
        print(f"[Init] {self.name} subscribed to system.input.raw")

    async def _on_raw(self, message):
        ts = time.time()
        payload = message.get("payload", {})
        mime = (payload.get("mime") or "").lower()
        text = payload.get("text")
        cleaned = None
        ttype = None
        ok = True

        try:
            # JSON
            if mime.startswith("application/json"):
                obj = json.loads(text) if isinstance(text, str) else text
                cleaned = obj
                ttype = "json"
            # CSV
            elif mime in ("text/csv", "application/csv"):
                rows = list(csv.reader(io.StringIO(text or "")))
                cleaned = rows
                ttype = "csv"
            # Plain text fallback
            else:
                cleaned = text if isinstance(text, str) else str(text)
                ttype = "text"
        except Exception as e:
            ok = False
            cleaned = {"error": str(e), "raw": (text if isinstance(text, str) else str(text))}

        bus = get_bus()
        if bus:
            if ok:
                await bus.publish("system.input.cleaned", {
                    "type": ttype,
                    "clean": True,
                    "content": cleaned,
                    "timestamp": ts
                })
                self.stats["ok"] += 1
            else:
                await bus.publish("system.input.error", {
                    "type": ttype or "unknown",
                    "clean": False,
                    "content": cleaned,
                    "timestamp": ts
                })
                self.stats["err"] += 1

    async def tick(self, dt):
        await asyncio.sleep(0)
        return {"id": self.name, "latency": dt, "ok": self.stats["ok"], "err": self.stats["err"], "timestamp": time.time()}

