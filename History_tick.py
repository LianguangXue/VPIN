import pandas as pd
from datetime import datetime
from datetime import timezone
import numpy as np
from ib_insync import *


def his_tick_extract(start, end, contracts):
    # start: start time for tick data
    # end: end time for tick data
    util.startLoop()
    ib.qualifyContracts(*contracts)
    amd = contracts[0]
    temp_start = start
    ticks = []
    while pd.to_datetime(temp_start, utc=True) <= pd.to_datetime(end, utc=True):
        temp_end = ''
        tick = ib.reqHistoricalTicks(amd, temp_start, temp_end, 1000, 'BID_ASK', useRth=False)
        print(temp_start)
        temp_start = tick[-1][0]
        ticks += tick
    df = pd.DataFrame(ticks)
    dftime_local = df['time'].dt.tz_convert('America/New_York')
    df['time'] = pd.to_datetime(dftime_local, '%Y-%m-%d %H:%M:%S').astype(str)

    long = len(df)
    df.index = df.time
    avg_price = (df.priceBid + df.priceAsk) / 2
    ttl_volume = df.sizeBid + df.sizeAsk

    new_df = pd.DataFrame(np.random.randn(long, 2), columns=['price', 'volume'])
    new_df.index = df.time
    new_df['price'] = avg_price
    new_df['volume'] = ttl_volume
    new_df.index = new_df.index.map(lambda x: str(x)[0:19])
    return new_df