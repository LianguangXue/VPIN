import plotly
import numpy as np
import pandas as pd
import plotly.plotly as py
import plotly.tools as tls
import plotly.graph_objs as go
import datetime
import time

tls.set_credentials_file(username='lxue10',api_key="F29SN8EVwOJKhZBoT3wG")

#stream_ids = tls.get_credentials_file()['stream_ids']
#print(stream_ids)
stream_ids = [u'8i780q45ku',u'tnc2io6pay',u'v2icvduevy']

# Get stream id from stream id list
stream_id0 = stream_ids[0]
stream_id1 = stream_ids[1]
stream_id2 = stream_ids[2]
# Make instance of stream id object
stream_0 = go.scatter.Stream(
    token=stream_id0,  # link stream id to 'token' key
    maxpoints=400      # keep a max of 80 pts on screen
)

stream_1 = go.scatter.Stream(
    token=stream_id1,  # link stream id to 'token' key
    maxpoints=400      # keep a max of 80 pts on screen
)
stream_2 = go.scatter.Stream(
    token=stream_id2,  # link stream id to 'token' key
    maxpoints=400      # keep a max of 80 pts on screen
)
# input dataframe, draw the VPIN live plot
# Initialize trace of streaming plot by embedding the unique stream_id

# Initialize trace of streaming plot by embedding the unique stream_id
trace0 = go.Scatter(
    x=[],
    y=[],
    mode='lines',
    stream=stream_0         # (!) embed stream id, 1 per trace
)
trace1 = go.Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_1         # (!) embed stream id, 1 per trace
)

trace2 = go.Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_2         # (!) embed stream id, 1 per trace
)


# Add title to layout object
#layout = go.Layout(title='Time Series')

# Make a figure object
fig = tls.make_subplots(rows=2, cols=1)
fig.append_trace(trace0, 1, 1)
fig.append_trace(trace1, 1, 1)
fig.append_trace(trace2, 2, 1)
#fig = go.Figure(data=data, layout=layout)
#fig = go.Figure(data = [trace1, trace2], layout = layout)
#one_more_trace=dict(type='scatter',
                                  # x=[df.index[0],df.index[-1]],
                                   #y=[0.99,0.99],
                                   #mode='lines',
                                   #line=dict(color='red'))
#fig.append_trace(one_more_trace, 1, 1)
# Send fig to Plotly, initialize streaming plot, open new tab
py.plot(fig, filename='python-streaming')


# We will provide the stream link object the same token that's associated with the trace we wish to stream to
s0 = py.Stream(stream_id0)
s1 = py.Stream(stream_id1)
s2 = py.Stream(stream_id2)
# We then open a connection
s0.open()
s1.open()
s2.open()
# (*) Import module keep track and format current time


# Use plotly to draw two subplots with max VPIN, corresponding close price and threshold
def plotly_df(df):
    i = 0  # a counter

    # Delay start of stream by 5 sec (time to switch tabs)
    # time.sleep(5)

    t = 0
    while (i < len(df)):
        x = df.time.values[i]
        y = df.VPIN.values[i]
        z = df['close price'].values[i]
        # y = float(np.random.randn(1))
        i += 1

        # Send data to your plot
        s0.write(dict(x=x, y=0.99))
        s1.write(dict(x=x, y=y))
        s2.write(dict(x=x, y=z))

        #     Write numbers to stream to append current data on plot,
        #     write lists to overwrite existing data on plot

        # plot a point every second
    # Close the stream when done plotting
    # s1.close()
    # s2.close()

