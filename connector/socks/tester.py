
# open a connection to the feed and stream to stdout

import asyncio
# import pdb
import json
from multiprocessing import Process, Queue
import sys
import websockets

from .clk import Timer, TimerError

FEED_URL = 'wss://ws-feed.pro.coinbase.com:443'
SANDBOX_FEED_URL = 'wss://ws-feed-public.sandbox.pro.coinbase.com:443'
REQUEST = "connector/requests"

MAX_SIZE = 100 # size of message queue before writing out

@Timer()
async def req(q, req_file):
    ctr = 0
    async with websockets.connect(SANDBOX_FEED_URL) as websocket:
        with open(REQUEST + '/' + req_file) as f:
            text = json.load(f)
            msg = json.dumps(text)

            await websocket.send(msg)

            # pdb.set_trace()
                            
            while True:
                if q.qsize() % 10 == 0:
                    print(q.qsize())
                resp = await websocket.recv()
                q.put(resp)
                
def writer(ad):
    q = ad['queue']
    outfile = ad['out_file']
    ctr = 0
    while True:
        if q.qsize() >= (MAX_SIZE):
            ctr += 1
            print("flushing: ", ctr)
            batch = ""
            for _ in range(MAX_SIZE):
                batch += q.get() + "\n"
            outfile.write(batch)
            outfile.flush()
    
def run():

    rf = sys.argv[1]
    outfile = open(sys.argv[2], 'a')    
    q = Queue()
    arg_dict = {'req_file':rf, 'out_file':outfile, 'queue':q}

    p = Process(target=writer, args=(arg_dict,))
    p.start()

    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(req(q, rf))
    finally:
        # should have another run_until_complete/.stop() to end gracefully
        arg_dict['out_file'].close()
        p.join()
        loop.close()
