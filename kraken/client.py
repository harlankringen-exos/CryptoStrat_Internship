import json
import aiohttp
from aiostream import stream, pipe
from util import make_logger

KRAKEN_NONNULL_RECV_TIMEOUT = 300
LOGGER = make_logger(__name__)


class KrakenClientException(Exception):
    pass


def requires_connection(func):
    def wrapped(self, *args, **kwargs):
        if not self.connected:
            raise KrakenClientException("Not connected")
        return func(self, *args, **kwargs)

    return wrapped

def wrap_stream(func):
    def wrapped(self, *args, **kwargs):
        return stream.iterate(func(self, *args, **kwargs)) | pipe.timeout(KRAKEN_NONNULL_RECV_TIMEOUT)
    return wrapped


class KrakenClient:
    def __init__(self, base_uri: str = "wss://ws.kraken.com"):
        self.base_uri = base_uri
        self.connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.sock = await self.session.ws_connect(self.base_uri)
        self.connected = True

    async def disconnect(self):
        await self.session.close()
    
    @requires_connection
    def raw_stream(self):
        return (
            stream.call(self.sock.receive)
            | pipe.cycle()
        )

    @requires_connection
    @wrap_stream
    async def stream(self, reconnect_count=0):
        reconnects = 0
        while True:
            msg = await self.sock.receive()
            if msg.type == aiohttp.WSMsgType.CLOSE:
                LOGGER.info("Kraken has closed the websocket connection, code: %d", msg.data)
                if reconnect_count == -1 or reconnects < reconnect_count:
                    LOGGER.info("Reconnecting")
                    await self.connect()
                    reconnects += 1
                else:
                    exit(0)
            if msg.data is not None and isinstance(msg.data, str):
                yield json.loads(msg.data)

    @requires_connection
    async def send(self, msg):
        await self.sock.send_str(json.dumps(msg))
