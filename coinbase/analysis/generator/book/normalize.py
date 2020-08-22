
import sys
import math

import numpy as np
import pandas as pd

from enum import Enum, IntEnum
from collections import namedtuple

Action = Enum('Action', 'ASK BID TRADE')
class Row(IntEnum):
    INDEX = 0
    TIME = 1
    TYPE = 2
    VALUE = 3
    SIZE = 4
    CONDITIONCODES = 5
    
TopOfBook = namedtuple('TopOfBook', ["time", "event_type", "ask_price", "ask_qty",
                                     "bid_price", "bid_qty", "trade_price", "trade_qty", "conditionCodes"])

if __name__ == "__main__":
    data_dir = "/home/harlan/ucsb/projects/exos_internship/CryptoStrat_Internship/kraken/generator/data_dumps"
    currency_file = sys.argv[1]

    last_ask = (0,0)
    last_bid = (0,0)
    book = [] # list of TopOfBook's
    tsum = [] # holds subsequent condition codes
    
    df = pd.read_csv(data_dir + "/" + currency_file)
    
    for row in df.itertuples():
        action = row[Row.TYPE]
        condition = row[Row.CONDITIONCODES]
        if action == "BID":
            last_bid = (row[Row.VALUE], row[Row.SIZE])
            
        if action == "ASK":
            last_ask = (row[Row.VALUE], row[Row.SIZE])
            
        if action == "TRADE":
            if condition == "TSUM":
                t = TopOfBook(time=row[Row.TIME],
                              event_type=Action.TRADE,
                              ask_price=last_ask[0],
                              ask_qty=last_ask[1],
                              bid_price=last_bid[0],
                              bid_qty=last_bid[1],
                              trade_price=row[Row.VALUE],
                              trade_qty=row[Row.SIZE],
                              conditionCodes="")
                #tsum.append("TSUM")
                book.append(t)
            
            # else if condition in "AS,OR,AB,AL" and tsum:
            #     book[-1].conditionCodes 
                

    # create dataframe
    top = pd.DataFrame.from_records(book, columns=TopOfBook._fields)
    top.to_csv(currency_file.replace(".csv", "_top.csv"), index=False)
    
    # visualize
