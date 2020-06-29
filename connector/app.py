
import asyncio
from datetime import datetime
import sys

from connector.infrastructure.client import Client
from connector.infrastructure.channel import Channel

class Heartbeat:
    def __init__(self, hb_dict):
        self.type = hb_dict["type"]
        self.last_trade_id = hb_dict['last_trade_id']
        self.product_id = hb_dict['product_id']
        self.sequence = int(hb_dict['sequence'])
        self.time = datetime.strptime(hb_dict['time'], '%Y-%m-%dT%H:%M:%S.%fZ')

    def __repr__(self):
        rep  = "{}\t\t\t\t{}\n".format(self.product_id, self.time)
        rep += "=============================================================\n"
        rep += "    Sequence: {0}   Last Trade ID: {1}\n".format(self.sequence, self.last_trade_id)
        rep += "=============================================================\n"
        return rep

class Match:
    def __init__(self, m_dict):
        self.type = m_dict["type"]
        self.last_trade_id = m_dict['trade_id']
        self.maker_order_id = m_dict['maker_order_id']
        self.taker_order_id = m_dict['taker_order_id']
        self.side = m_dict['side']
        self.size = float(m_dict['size'])
        self.price = float(m_dict['price'])
        self.product_id = m_dict['product_id']
        self.sequence = int(m_dict['sequence'])
        self.time = datetime.strptime(m_dict['time'], '%Y-%m-%dT%H:%M:%S.%fZ')

    def __repr__(self):
        rep  = "{}\t\t\t\t{}\n".format(self.product_id, self.time)
        rep += "=============================================================\n"
        rep += "    Sequence: {0}   Last Trade ID: {1}\n".format(self.sequence, self.last_trade_id)
        rep += "    Maker: {0}      Taker: {1}\n".format(self.maker_order_id, self.taker_order_id)
        rep += "    Price: ${:.2f}\tSize:{:.8f}\tSide:{: >5}\n".format(self.price, self.size, self.side)
        rep += "=============================================================\n"
        return rep
    
class Tick:
    def __init__(self, tick_dict):
        self.product_id = tick_dict['product_id']
        self.best_bid = float(tick_dict['best_bid'])
        self.best_ask = float(tick_dict['best_ask'])
        self.price = float(tick_dict['price'])
        self.side = tick_dict['side']
        self.size = float(tick_dict['last_size'])
        self.time = datetime.strptime(tick_dict['time'], '%Y-%m-%dT%H:%M:%S.%fZ')

        self.last_trade_id = int(tick_dict['trade_id'])
        self.product_id = tick_dict['product_id']
        self.sequence = int(tick_dict['sequence'])

    @property
    def spread(self):
        return self.best_ask - self.best_bid

    def __repr__(self):
        rep  = "{}\t\t\t\t{}\n".format(self.product_id, self.time)
        rep += "=============================================================\n"
        rep += "   Price: ${:.2f}\tSize:{:.8f}\tSide:{: >5}\n".format(self.price, self.size, self.side)
        rep += "Best ask: ${:.2f}\tBest bid: ${:.2f}\tSpread: ${:.2f}\n".format(self.best_ask, self.best_bid, self.spread)
        rep += "    Sequence: {0}   Last Trade ID: {1}\n".format(self.sequence, self.last_trade_id)
        rep += "=============================================================\n"
        return rep

class Ticker(Client):
    def on_message(self, message):
        if message['type'] == 'ticker'and'time' in message:
            tick = Tick(message)
            print(tick, "\n\n")
        if message["type"] == "heartbeat":
            hb = Heartbeat(message)
            print(hb, '\n\n')
        if message["type"] == "match":
            m = Match(message)
            print(m, '\n\n')
            
def run():
    product_id = sys.argv[1]
    loop = asyncio.get_event_loop()
    channel = [Channel('ticker', product_id),
               Channel('heartbeat', product_id),
               Channel('matches', product_id)]
    ticker = Ticker(loop, channel)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(ticker.close())
        loop.close()
