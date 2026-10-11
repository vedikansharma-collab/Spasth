import asyncio
import ssl
import sys
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Ensure dotenv is loaded
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

raw_url = os.getenv("DATABASE_URL", "")
u = urlparse(raw_url)
HOST = u.hostname or "127.0.0.1"
PORT = 5433

import websockets

async def handle_client(reader, writer):
    uri = f"wss://{HOST}/v2"
    ctx = ssl.create_default_context()
    try:
        async with websockets.connect(
            uri,
            ssl=ctx,
            subprotocols=["binary"],
            max_size=None,
            ping_interval=20,
            ping_timeout=20
        ) as ws:
            async def tcp_to_ws():
                try:
                    while True:
                        data = await reader.read(65536)
                        if not data:
                            break
                        await ws.send(data)
                except Exception:
                    pass
                finally:
                    try:
                        await ws.close()
                    except Exception:
                        pass

            async def ws_to_tcp():
                try:
                    async for msg in ws:
                        if isinstance(msg, str):
                            msg = msg.encode("utf-8")
                        writer.write(msg)
                        await writer.drain()
                except Exception:
                    pass
                finally:
                    try:
                        writer.close()
                    except Exception:
                        pass

            await asyncio.gather(tcp_to_ws(), ws_to_tcp())
    except Exception as e:
        try:
            writer.close()
        except Exception:
            pass

async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", PORT)
    print(f"[DB-TUNNEL] Listening on 127.0.0.1:{PORT} -> wss://{HOST}/v2", flush=True)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[DB-TUNNEL] Stopped.")
