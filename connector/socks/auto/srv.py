
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import urlparse

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
