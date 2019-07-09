import pandas as pd
from Parallezing_MIR import *
from Tick_VPIN import *
from ib_insync import *
from History_tick import *
import plotly
import numpy as np
import plotly.plotly as py
import plotly.tools as tls
import plotly.graph_objs as go


if __name__ == '__main__':
    #History VPIN caculation step
    dat = pd.read_csv('GOOG_tick.csv',sep=',', index_col=0)

    time_bucket_list, bucket_price, vpin_norm_list, high_list, low_list, time_list, price_list, diff_list, bar_remain, \
    bucket_remain, std_price, volume_per_bar = vpin_combine(dat, bars_per_bucket=30, buckets_per_day=1836,
                                                            support_window=0.0478)
    print('Finish VPIN Caculation Step!')
    #plot history VPIN step
    #VPIN_data = pd.DataFrame({'VPIN': vpin_norm_list, 'price': bucket_price}, index=time_bucket_list)
    stream_id = u'8i780q45ku'
    stream_1 = go.scatter.Stream(
        token=stream_id,  # link stream id to 'token' key
     # keep a max of 80 pts on screen
    )
    # Initialize trace of streaming plot by embedding the unique stream_id
    trace1 = go.Scatter(
        x=time_bucket_list[-100:],
        y=vpin_norm_list[-100:],
        mode='lines+markers',
        stream=stream_1  # (!) embed stream id, 1 per trace
    )

    data = [trace1]

    # Add title to layout object
    layout = go.Layout(title='VPIN')

    # Make a figure object
    fig = go.Figure(data=data, layout=layout)

    # Send fig to Plotly, initialize streaming plot, open new tab
    #py.plot(fig, filename='VPIN_plot_test')
    plotly.offline.plot(fig, filename='VPIN_plot_test.html')
    '''
    plot(VPIN_data)
    start = pd.to_datetime(dat.index[-1])
    while True:
        end = datetime.now(tz=timezone.utc)
        contracts = [Forex(pair) for pair in ('EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF', 'USDCAD', 'AUDUSD')]
        Tick_data = his_tick_extract(start, end, contracts)
        new_time_bucket_list, new_bucket_price, new_vpin_norm_list, high_list, low_list, time_list, time_bucket_list, \
        bucket_price, vpin_norm_list, bar_remain, bucket_remain, std_price, volume_per_bar = vpin_tick_caculation_update(
                                                                                                            Tick_data,
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
        new_VPIN_data = pd.DataFrame({'VPIN': new_vpin_norm_list, 'price': new_bucket_price},
                                     index=new_time_bucket_list)
        plot(new_VPIN_data)
        start = pd.to_datetime(new_VPIN_data.index[-1])
    '''