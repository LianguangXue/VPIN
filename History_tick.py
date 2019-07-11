import pandas as pd
from datetime import datetime
from datetime import timezone
import numpy as np
from ib_insync import *
from datetime import timedelta

def process_data(tick):
    df = pd.DataFrame(tick)
    dftime_local = df['time']
    df['time'] = pd.to_datetime(dftime_local, '%Y-%m-%d %H:%M:%S').astype(str).map(lambda x: str(x)[0:19])

    long = len(df)
    avg_price = (df.priceBid + df.priceAsk) / 2
    ttl_volume = df.sizeBid + df.sizeAsk

    new_df = pd.DataFrame(np.random.randn(long, 3), columns=['time', 'price', 'volume'])
    new_df['time'] = df.time
    new_df['price'] = avg_price
    new_df['volume'] = ttl_volume
    return new_df


def data_convert(ticks):
    df = pd.DataFrame(index=ticks.time.values)
    df['price'] = ticks['price'].values
    df['volume'] = ticks['volume'].values
    return df


def check_excess(start, ticks, end):
    ticks = ticks[pd.to_datetime(ticks.index, utc=True) <= pd.to_datetime(end, utc=True)]
    ticks = ticks[pd.to_datetime(ticks.index, utc=True) >= pd.to_datetime(start, utc=True)]
    return ticks
	
def duplicate_drop(tick,ticks):
    tick['count'] = tick.groupby(['time','price','volume']).cumcount()
    ticks['count'] = ticks.groupby(['time','price','volume']).cumcount()

    ticks = pd.concat([ticks,tick], ignore_index=False)
    ticks = ticks.drop_duplicates()
    ticks = ticks.drop(['count'], axis=1)
    return ticks
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
def his_tick_extract(start,end,contracts,ib):
    #start: start time for tick data
    #end: end time for tick data
    amd = contracts[0]
    temp_start = start
    ticks=pd.DataFrame(columns = ['time','price','volume'])
    while  pd.to_datetime(temp_start,utc=True) <= pd.to_datetime(end,utc=True):
        
        temp_end = ''
        tick = ib.reqHistoricalTicks(amd, temp_start, temp_end, 1000, 'BID_ASK', useRth=False)
        temp_start = tick[-1][0]
        print("Tick data length",len(tick))
        if len(tick)<1000:
            print('Jump at this time')
            temp_start += timedelta(seconds=1)
        print(temp_start)
        tick = pd.DataFrame(tick)
        tick = process_data(tick)
        ticks = duplicate_drop(tick,ticks)
        print(temp_start)
        print(temp_end)
    ticks = data_convert(ticks)
    ticks = check_excess(start,ticks,end)
    return ticks