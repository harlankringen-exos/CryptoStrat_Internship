
import asyncio

from autobahn.asyncio.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory


class MyClientProtocol(WebSocketClientProtocol):
    
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        
    async def onOpen(self):
        print("WebSocket connection open.")

        # # start sending messages every second ..
        # while True:
        #     self.sendMessage("Hello, world!".encode('utf8'))
        #     self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
        #     await asyncio.sleep(1)

        name = input("What's your name? ")
        self.sendMessage(f"> {name}".encode("utf-8"))
        await asyncio.sleep(1)
        
    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
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
