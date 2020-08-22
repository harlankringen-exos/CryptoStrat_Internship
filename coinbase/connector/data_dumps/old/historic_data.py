
import asyncio
import csv
from datetime import date

from copra.rest import Client

loop = asyncio.get_event_loop()

client = Client(loop)
    
async def get_stats(s=None,e=None):
    btc_stats = await client.get_24hour_stats('BTC-USD')
    products = await client.products()
    historic = await client.historic_rates('BTC-USD',
                                               granularity=86400,
                                               start=s,
                                               end=e)
    for i in products:
        print(i['id'])
        
    return products

if __name__ == "__main__":

    s = date.fromisoformat('2020-05-01')
    e = date.fromisoformat('2020-05-30')
    
    dat = loop.run_until_complete(get_stats(s,e))
    loop.run_until_complete(client.close())

    with open('historic.csv','w') as f:
        writer = csv.writer(f)
        writer.writerows(dat)
# GNT-USDC
# XRP-BTC
# REP-BTC
# XTZ-USD
# ETC-BTC
# KNC-BTC
# LOOM-USDC
# BTC-GBP
# EOS-USD
# OMG-GBP
# BAT-USDC
# LINK-USD
# ETH-USDC
# DASH-USD
# COMP-BTC
# ETH-GBP
# ETH-BTC
# XTZ-BTC
# ZEC-USDC
# EOS-BTC
# ZEC-BTC
# EOS-EUR
# REP-USD
# BCH-USD
# KNC-USD
# XRP-USD
# ZRX-EUR
# BCH-BTC
# BAT-ETH
# BTC-EUR
# ATOM-BTC
# BCH-GBP
# OMG-BTC
# BCH-EUR
# LTC-EUR
# MKR-USD
# OMG-USD
# ETC-EUR
# OMG-EUR
# ATOM-USD
# LTC-BTC
# ETC-GBP
# XLM-BTC
# XRP-EUR
# XLM-USD
# DNT-USDC
# ETH-USD
# ETH-EUR
# ETC-USD
# LINK-ETH
# XLM-EUR
# DAI-USDC
# MKR-BTC
# DAI-USD
# ALGO-USD
# CVC-USDC
# LTC-USD
# MANA-USDC
# ZRX-BTC
# BTC-USDC
# ETH-DAI
# ZRX-USD
# BTC-USD
# OXT-USD
# LTC-GBP
# DASH-BTC
# COMP-USD
