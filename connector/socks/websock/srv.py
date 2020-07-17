
import asyncio
import websockets

async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    # greeting = f"Hello {name}!"
    match = {"type":"match","trade_id":14587419,"maker_order_id":"91b59a7c-6a07-4039-9536-21daf3cb3282","taker_order_id":"47888661-47cc-4af6-a26e-ea359b236b1b","side":"buy","size":"0.0659","price":"9120.8","product_id":"BTC-USD","sequence":180754935,"time":"2020-06-30T19:10:24.602001Z"}

    update = {"type":"l2update","product_id":"BTC-USD","changes":[["buy","9079.24","0.06920000"]],"time":"2020-06-30T19:10:25.546819Z"}

    for _ in range(10000):
        choice = random.randint(0,1)
        if choice == 0:
            msg = json.dumps(match).encode('utf-8')
        else:
            msg = json.dumps(update).encode('utf-8')
            
        websocket.send(msg)

    #await websocket.send(greeting)
    # print(f"> {greeting}")

start_server = websockets.serve(hello, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
