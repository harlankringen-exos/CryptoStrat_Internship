
import asyncio
import pdb
import websockets

from pyinstrument import Profiler

async def hello():
    #uri = "ws://localhost:8765"
    uri = "ws://169.231.16.174:8765"
    async with websockets.connect(uri) as websocket:
        name = input("What's your name? ")

        await websocket.send(name)
        print(f"> {name}")


        # profiler = Profiler()
        # profiler.start()

        
        pdb.set_trace()
        greeting = await websocket.recv()


        # profiler.stop()
        # print(profiler.output_text(unicode=True, color=True))

        print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())
