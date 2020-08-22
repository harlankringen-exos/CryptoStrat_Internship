
# Generate ORE from Kraken Exchange

## Packages

```
# sudo apt install python3-pip

```

## Sources of Data

### Bloomberg futures

This data has millisecond resolution and was downloaded with the `aws` command.
We treat this data with the `normalize.py` script to get the data in a top of
book representation.

The filenames indicate the instrument and date of expiry.  For instance,
"BTCN0_Curncy.csv" indicates we are looking at bitcoin data for the month of
July in the year 2020.

### BTC market 

This data shows the raw bitcoin prices at the microsecond level and is procured
with the dl.py script (on the remote machine currently).  Note that we have only
been keeping track of this source since around May.  Also I don't know what the
source of this is, Bloomberg, etc.

## Issues with Timing

1. The bloomberg data has millisecond offsets courtesy of Matteo in separate
   files, labeled e.g. "BTCM0_ms-offset.csv".  
2. There is a particular logic involved in ensuring trades with NaN offsets get
   mapped to the last known offset in the timebin lest we find events that moved
   backward in time.  More information is available in "trade_time_interstitial.ipynb.
