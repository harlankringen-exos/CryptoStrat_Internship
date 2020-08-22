import time
from io import BytesIO
import msgpack
import requests
from datetime import datetime
from collections import namedtuple
from streaming_data_pipeline.interface import Middleware

Increment = namedtuple("Increment", "quote base")

class OreGenerator(Middleware):

    def __init__(self, products):
        self.denoms = OreGenerator.get_denominators()
        self.last_time = 0
        self.product_id_map = {v: i for i,v in enumerate(products)}


    @staticmethod
    def get_denominators():
        resp = requests.get("https://api.pro.coinbase.com/products")
        cfg = resp.json()
        return {v["id"]: Increment(float(v["quote_increment"]), float(v["base_increment"])) for v in cfg}

    async def __call__(self, cur):
        now = datetime.fromisoformat(cur["exos_timestamp"]).timestamp()
        inow = int(now)
        if inow - self.last_time >= 1:
            yield [0, inow]
            self.last_time = inow

        recv = int(  1_000_000_000 * (now -  self.last_time))
        batch = 0
        product = cur["product_id"]
        inmt_id = self.product_id_map[product]
        if cur["type"] == "snapshot":
            voffset = 0
            for price, size in cur["bids"]:
                price_n = int(float(price) // self.denoms[product].quote)
                size_n = int(float(size) // self.denoms[product].base)
                yield [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), True]
            for price, size in cur["asks"]:
                price_n = int(float(price) // self.denoms[product].quote)
                size_n = int(float(size) // self.denoms[product].base)
                yield [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), False]
        elif cur["type"] == "l2update":
            voffset = int(1_000_000_000 * (datetime.fromisoformat(cur["time"][0:-1]).timestamp() - self.last_time) - recv)
            for side,price,size in cur["changes"]:
                price_n = int(float(price) // self.denoms[product].quote)
                size_n = int(float(size) // self.denoms[product].base)
                yield  [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), side == "buy"]
        elif cur["type"] == "match":
            voffset = int(1_000_000_000 * (datetime.fromisoformat(cur["time"][0:-1]).timestamp() - self.last_time) - recv)
            price_n = int(float(cur['price']) // self.denoms[product].quote)
            size_n = int(float(cur['size']) // self.denoms[product].base)
            yield [11, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), cur['side'].upper()[0]]


class MsgPackPlugin:

    def __init__(self, buf):
        self.buf = buf

    async def __call__(self, stream):
        packer = msgpack.Packer()
        async for msg in stream:
            print(msg)
            self.buf.write(packer.pack(msg))

