
import sys
import traceback

import asyncio
import websockets
import time

async def hello():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        ts = time.perf_counter_ns()
        greeting = await websocket.recv()
        latency = time.perf_counter_ns() - ts
        #print(f"{latency}", flush=True)

if __name__ == "__main__":	
    try:
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(hello())
    except KeyboardInterrupt:
        print("\nhi\n")
        print(repr(traceback.extract_stack()))
        print(repr(traceback.format_stack()))              
        #traceback.print_exc(file=sys.stdout)
    finally:
        #server.close()
        loop.close()
