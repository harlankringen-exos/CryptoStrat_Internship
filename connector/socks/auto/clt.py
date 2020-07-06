
import asyncio
import json
from multiprocessing import Queue
import time

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory
import msgpack as ms


class MyClientProtocol(WebSocketClientProtocol):

    async def onOpen(self):
        print("WebSocket connection open.")

        # name = input("What's your name? ")
        # self.sendMessage(f"> {name}".encode("utf-8"))
        await asyncio.sleep(1)
        
    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
            msg = json.loads(payload.decode('utf8'))
            print(msg)
            recv = time.time_ns()

            # ore-ify, first pass, no real optimization or cleverness
            q = Queue()
            with open('msgpack.out', 'wb') as self.outf:
                version = ms.pack([1,0,0], self.outf)
                header = ms.pack([{'symbol': 'BTC-USD', 'price_tick': 0.01, 'qty_tick': 1}], self.outf)
                ts_seq = ms.pack([0, recv], self.outf)
                try:
                    lvl_seq = ms.pack([14, recv, 0, 0, 0, 0, msg['changes'][0][1], msg['changes'][0][2], msg['changes'][0][0] == 'buy'], self.outf)
                except KeyError as e:
                    pass
            
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':

    factory = WebSocketClientFactory("ws://127.0.0.1:9000")
    factory.protocol = MyClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, '127.0.0.1', 9000)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
