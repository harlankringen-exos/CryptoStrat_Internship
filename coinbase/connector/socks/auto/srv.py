
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import urlparse
import random

from autobahn.asyncio.websocket import WebSocketServerFactory
from autobahn.asyncio.websocket import WebSocketServerProtocol

class MyServerProtocol(WebSocketServerProtocol):

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
            
        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        
        ## echo back message verbatim
        self.sendMessage(payload, isBinary)
        
    def onConnect(self,request):
        print("client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("Websock connection open")

        # # stream messages
        # read data dump file into memory
        match = {"type":"match","trade_id":14587419,"maker_order_id":"91b59a7c-6a07-4039-9536-21daf3cb3282","taker_order_id":"47888661-47cc-4af6-a26e-ea359b236b1b","side":"buy","size":"0.0659","price":"9120.8","product_id":"BTC-USD","sequence":180754935,"time":"2020-06-30T19:10:24.602001Z"}

        update = {"type":"l2update","product_id":"BTC-USD","changes":[["buy","9079.24","0.06920000"]],"time":"2020-06-30T19:10:25.546819Z"}

        for _ in range(10000):
            choice = random.randint(0,1)
            if choice == 0:
                msg = json.dumps(match).encode('utf-8')
            else:
                msg = json.dumps(update).encode('utf-8')

            self.send(msg,True)
        
        # outf = open("/home/harlan/ucsb/projects/exos_internship/CryptoStrat_Internship/connector/data_dumps/all.out", "r")
        # all = outf.readlines()        
        # # binary encode, msg pack whatever
        # for update in all:
        #     msg = json.dumps(json.loads(update)).encode('utf-8')

        #     # send off
        #     self.sendMessage(msg, True)
        # print("done")
        
if __name__ == "__main__":
    factory = WebSocketServerFactory("ws://127.0.0.1:9000")
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
