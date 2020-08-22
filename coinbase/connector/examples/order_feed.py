
import asyncio

from copra.rest import Client

loop = asyncio.get_event_loop()

client = Client(loop)

async def get_stats():
    btc_stats = await client.get_24hour_stats('BTC-USD')
    print(btc_stats)

loop.run_until_complete(get_stats())
loop.run_until_complete(client.close())

# sample output
# {'open': '9618.85000000', 'high': '9694.81000000', 'low': '9572.22000000', 'volume': '7387.11815961', 'last': '9629.13000000', 'volume_30day': '346108.46778134'}
