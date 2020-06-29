
# open a connection to the feed and stream to stdout

import asyncio
import json
import websockets

FEED_URL = 'wss://ws-feed.pro.coinbase.com:443'
SANDBOX_FEED_URL = 'wss://ws-feed-public.sandbox.pro.coinbase.com:443'
REQUEST = "connector/requests/multi_channel.json"

async def req():
    async with websockets.connect(SANDBOX_FEED_URL) as websocket:
        with open(REQUEST) as f:
            text = json.load(f)
            msg = json.dumps(text)

            await websocket.send(msg)
            while True:
                resp = await websocket.recv()
                print("resp: ", resp)


def run():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(req())
    except:
        # should have another run_until_complete/.stop() to end the stream more
        # gracefully
        loop.close()
