
import numpy as np
import json
from datetime import datetime
import time

last_time = 0;
sec_to_ns = 1000000000
price_digits = 2;
qty_digits = 8;

with open("/home/harlan/ucsb/projects/exos_internship/CryptoStrat_Internship/connector/cpp/server/test_exos_time.set", "r") as f:
    for line in f.readlines():
        cur = json.loads(line)
        now = int(cur["exos_time"])
        inow = now // sec_to_ns
        
        print("timing:")
        print(now, inow, '\n')
        if inow - last_time >= 1:
            print([0, inow])
            last_time = inow
        recv = int(  1_000_000_000 * (now -  last_time))
        batch = 0
        #product = cur["product_id"]
        inmt_id = 0 #self.product_id_map[product]
        if cur["type"] == "snapshot":
            voffset = 0
            for price, size in cur["bids"]:
                price_n = int(float(price) // price_digits) #self.denoms[product].quote)
                size_n = int(float(size) // qty_digits) #self.denoms[product].base)
                print( [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), True])
            for price, size in cur["asks"]:
                price_n = int(float(price) // price_digits) #self.denoms[product].quote)
                size_n = int(float(size) // qty_digits) #self.denoms[product].base)
                print( [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), False])

        elif cur["type"] == "l2update":
            voffset = int(1_000_000_000 * (datetime.fromisoformat(cur["time"][0:-1]).timestamp() - last_time) - recv)
            for side,price,size in cur["changes"]:
                print("prices: ", price, size)
                price_n = int(float(price) // price_digits) #self.denoms[product].quote)
                size_n = int(float(size) // qty_digits) #self.denoms[product].base)
                print(  [14, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), side == "buy"])

        elif cur["type"] == "match":
            print("prices: ", price, size)
            voffset = int(1_000_000_000 * (datetime.fromisoformat(cur["time"][0:-1]).timestamp() - last_time) - recv)
            price_n = int(float(cur['price']) // price_digits) #self.denoms[product].quote)
            size_n = int(float(cur['size']) // qty_digits) #self.denoms[product].base)
            print( [11, recv, voffset, 0, batch, inmt_id, int(price_n), int(size_n), cur['side'].upper()[0]])
            



        
        
        
