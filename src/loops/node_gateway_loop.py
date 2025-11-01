from loops.Trinity_STEM import BaseLoop, get_bus
import asyncio, json, socket, time

META = {
    "name": "NodeGatewayLoop",
    "inputs": [],
    "outputs": ["system.input.raw"],
    "description": "TCP gateway for local clients — accepts JSON payloads and injects them into the system bus."
}

class NodeGatewayLoop(BaseLoop):
    auto_start = True

    async def init(self):
        self.host = "127.0.0.1"
        self.port = 8765
        self.token = hex(int(time.time() * 1000000))[2:18]
        self.server = None
        print(f"[Init] NodeGatewayLoop listening on {self.host}:{self.port}  token={self.token}")

        asyncio.create_task(self._run_server())

    async def _run_server(self):
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self.server = server
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        bus = get_bus()
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                msg = json.loads(line.decode().strip())
                await bus.publish("system.input.raw", msg)
            except Exception as e:
                print(f"[Error] NodeGatewayLoop: {e}")
        writer.close()
        await writer.wait_closed()

    async def tick(self, dt):
        await asyncio.sleep(0.25)
        return {"id": self.name, "latency": dt, "timestamp": time.time()}
