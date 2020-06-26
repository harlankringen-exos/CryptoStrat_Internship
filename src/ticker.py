import asyncio
from datetime import datetime
import sys
from copra.websocket import Channel, Client

class Tick:
    def __init__(self, tick_dict):
        self.product_id = tick_dict['product_id']
        self.best_bid = float(tick_dict['best_bid'])
        self.best_ask = float(tick_dict['best_ask'])
        self.price = float(tick_dict['price'])
        self.side = tick_dict['side']
        self.size = float(tick_dict['last_size'])
        self.time = datetime.strptime(tick_dict['time'], '%Y-%m-%dT%H:%M:%S.%fZ')

    @property
    def spread(self):
        return self.best_ask - self.best_bid

    def __repr__(self):
        rep  = "{}\t\t\t\t{}\n".format(self.product_id, self.time)
        rep += "=============================================================\n"
        rep += "   Price: ${:.2f}\tSize:{:.8f}\tSide:{: >5}\n".format(self.price, self.size, self.side)
        rep += "Best ask: ${:.2f}\tBest bid: ${:.2f}\tSpread: ${:.2f}\n".format(self.best_ask, self.best_bid, self.spread)
        rep += "=============================================================\n"
        return rep

class Ticker(Client):
    def on_message(self, message):
        if message['type'] == 'ticker'and'time' in message:
            tick = Tick(message)
            print(tick, "\n\n")

product_id = sys.argv[1]
loop = asyncio.get_event_loop()
channel = Channel('ticker', product_id)
ticker = Ticker(loop, channel)
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(ticker.close())
    loop.close()
