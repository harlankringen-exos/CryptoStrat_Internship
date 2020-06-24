
import asyncio

from copra.websocket import Channel, Client

loop = asyncio.get_event_loop()

ws = Client(loop, Channel('heartbeat', 'BTC-USD'))

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(ws.close())
    loop.close()

# sample output
# {'type': 'subscriptions', 'channels': [{'name': 'heartbeat', 'product_ids': ['BTC-USD']}]}
# {'type': 'heartbeat', 'last_trade_id': 0, 'product_id': 'BTC-USD', 'sequence': 14896899746, 'time': '2020-06-24T01:47:38.913284Z'}
# {'type': 'heartbeat', 'last_trade_id': 0, 'product_id': 'BTC-USD', 'sequence': 14896899776, 'time': '2020-06-24T01:47:39.913320Z'}
