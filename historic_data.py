
import asyncio
import csv
from datetime import date

from copra.rest import Client

loop = asyncio.get_event_loop()

client = Client(loop)

async def get_stats(s=None,e=None):
    btc_stats = await client.get_24hour_stats('BTC-USD')
    historic = await client.historic_rates('BTC-USD',
                                               granularity=86400,
                                               start=s,
                                               end=e)
    return historic

if __name__ == "__main__":

    s = date.fromisoformat('2020-05-01')
    e = date.fromisoformat('2020-05-30')
    
    dat = loop.run_until_complete(get_stats(s,e))
    loop.run_until_complete(client.close())

    with open('historic.csv','w') as f:
        writer = csv.writer(f)
        writer.writerows(dat)
