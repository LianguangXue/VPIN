import pandas as pd
from Parallezing_MIR import *
from Tick_VPIN import *
from ib_insync import *
from History_tick import *




if __name__=='__main__':
    ib = IB()
    ib.connect('127.0.0.1', 7496, clientId=15)
    dat = pd.read_csv('GOOG.csv')

    time_bucket_list, bucket_price, vpin_norm_list, high_list, low_list, time_list, price_list, diff_list, bar_remain, \
    bucket_remain, std_price, volume_per_bar = vpin_combine(dat, bars_per_bucket=30, buckets_per_day=1836,
                                                            support_window=0.0478)
    VPIN_data = pd.DataFrame({'VPIN': vpin_norm_list, 'price': bucket_price}, index=time_bucket_list)
    plot(VPIN_data)
    start = pd.to_datetime(dat.index[-1])
    while True:
        end = datetime.now(tz=timezone.utc)
        contracts = [Forex(pair) for pair in ('EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF', 'USDCAD', 'AUDUSD')]
        Tick_data = his_tick_extract(start, end, contracts)
        new_time_bucket_list, new_bucket_price, new_vpin_norm_list, high_list, low_list, time_list, time_bucket_list, \
        bucket_price, vpin_norm_list, bar_remain, bucket_remain, std_price, volume_per_bar = vpin_tick_caculation_update(Tick_data,
                                                                                                                        time_bucket_list,
                                                                                                                        bucket_price,
                                                                                                                        vpin_norm_list,
                                                                                                                        high_list,
                                                                                                                        low_list,
                                                                                                                        time_list,
                                                                                                                        price_list,
                                                                                                                        diff_list,
                                                                                                                        bar_remain,
                                                                                                                        bucket_remain,
                                                                                                                        std_price,
                                                                                                                        volume_per_bar)
        new_VPIN_data = pd.DataFrame({'VPIN':new_vpin_norm_list,'price':new_bucket_price},index = new_time_bucket_list)
        plot(new_VPIN_data)
        start = pd.to_datetime(new_VPIN_data.index[-1])