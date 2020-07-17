import asyncio
import json
import websockets
MESSAGE = json.dumps({"id": 1246250723598336, "id_str": "1246250723598336", "order_type": 0, "datetime": "1593095405", "microtimestamp": "1593095405223000", "amount": 1.0799, "amount_str": "1.07990000", "price": 9246.29, "price_str": "9246.29", "event": "order_created", "bitstamp_channel": "live_orders_btcusd", "ccy": "btcusd", "exos_timestamp": "2020-06-25T14:30:05.280925"})

async def hello(websocket, path):
    name = input("What's your name? ")
    print(MESSAGE)
    await websocket.send(MESSAGE)
start_server = websockets.serve(hello, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
