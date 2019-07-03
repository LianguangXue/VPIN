import numpy as np
import pandas as pd
import timeit
import datetime
import time
import multiprocessing as mp
# find the min and max value between i and j index in list P
def find_min_max(P, i, j):
    imin = i
    jmax = i
    pmin = P[i]
    pmax = P[i]
    for k in range(i+1,j):
        if(P[k] < pmin):
            pmin = P[k]
            imin = k
        if(P[k] >= pmax):
            pmax = P[k]
            jmax = k
    return imin, pmin, jmax, pmax

# find min value between i and j in list P
def find_min(P, i, j):
    pmin = P[i]
    for k in range(i+1,j):
        if(P[k] < pmin):
            pmin = P[k]
    return pmin

# find max value between i and j in list P
def find_max(P, i, j):
    pmax = P[i]
    for k in range(i+1,j):
        if(P[k] > pmax):
            pmax = P[k]
    return pmax


# find max intermediate gain between index i and j in list P
def max_intermediate_gain(P, i, j, thr):
    imin, pmin, jmax, pmax = find_min_max(P, i, j)
    res = pmax / pmin - 1

    if (imin <= jmax):
        return res;
    if (res <= thr):
        return 0;

    pmax0 = find_min(P, i, jmax)
    rl = pmax / pmax0 - 1
    if (thr < rl):
        thr = jmax

    pmin1 = find_max(P, imin + 1, j)
    rr = pmin1 / pmin - 1
    if (thr < rr):
        thr = rr

    rm = max_intermediate_gain(P, jmax + 1, imin, thr)
    if (thr < rm):
        thr = rm
    return thr


# compute MIR for a list P
def compute_MIR(P):
    imin, pmin, jmax, pmax = find_min_max(P, 0, len(P))
    thr = pmax / pmin - 1

    if (imin <= jmax):
        return thr

    loss = pmin / pmax - 1
    thr = -loss

    # Group L
    if (jmax == 0):
        pmax0 = P[0]
    else:
        pmax0 = find_min(P, 0, jmax)
    rl = pmax / pmax0 - 1

    if (thr < rl):
        thr = rl

    # Group R
    if (imin + 1 >= len(P)):
        pmin1 = P[-1]
    else:
        pmin1 = find_max(P, imin + 1, len(P))
    rr = pmin1 / pmin - 1
    if (thr < rr):
        thr = rr

    # Group M
    rm = max_intermediate_gain(P, jmax, imin, thr)
    if (thr < rm):
        thr = rm;
    if (thr > -loss):
        return thr;
    else:
        return loss


# extend a df to full form (time(index), seconds, high_p, low_p, volume)
def full_df_bar(df):
    since = datetime.datetime(1970, 8, 15, 6, 0, 0)
    secs = (df.index - since).total_seconds()
    df_len = len(df)
    df_bar = pd.DataFrame(np.random.randn(df_len, 3), columns=['seconds', 'high', 'low'])
    df_bar.seconds = secs
    price_high = np.array(df.high)
    price_low = np.array(df.low)
    df_bar.high = price_high
    df_bar.low = price_low
    df_bar = df_bar.assign(MIR=np.zeros(df_len))
    df_bar.index = df.index

    return df_bar

def compute_MIR_tick(df_bar, k, horizon=768.96):
    # k = 2
    period_k = pd.DataFrame([[df_bar.seconds[k], df_bar.high[k]]], columns = ['seconds', 'price'])
    entry_2 = pd.DataFrame([[df_bar.seconds[k], df_bar.low[k]]], columns = ['seconds', 'price'])
    period_k = period_k.append(entry_2, ignore_index=True)
    # period_k
    j = k+1
    while(df_bar.seconds[j] <= df_bar.seconds[k] + horizon):
        entry_j = pd.DataFrame([[df_bar.seconds[j], df_bar.high[j]]], columns = ['seconds', 'price'])
        entry_j2 = pd.DataFrame([[df_bar.seconds[j], df_bar.low[j]]], columns = ['seconds', 'price'])
        entry_j = entry_j.append(entry_j2)
        period_k = period_k.append(entry_j2, ignore_index=True)
        j += 1
    #print(period_k)
    period_k_price = period_k.price
    mir_k = compute_MIR(np.array(period_k_price))

    return mir_k


# a new bar dataframe df_bar (time secs high low volume)
# a new function to compute MIR of each bar consider high and low prices separately
# horizon eta is the rolling interval


def df_bar_MIR(df_bar, eta= 0.0089):
    horizon = eta * 24 * 60 * 60
    count_bar = len(df_bar)
    sec_init = df_bar.seconds[0]
    sec_last = df_bar.seconds[-1]

    for k in range(count_bar):
        if (df_bar.seconds[k] + horizon <= sec_last):
            mir_k = compute_MIR_tick(df_bar, k, horizon)
            df_bar.loc[df_bar.index[k], 'MIR'] = mir_k
        print(k)

    return df_bar

def multiprocess_MIR(i,df1,df_sample_sorted):

    print(i)
    mir_i = compute_MIR_tick(df1, df_sample_sorted.loc[df_sample_sorted.index[i], 'num'])
    return mir_i


# Using orginal unduplicated list df1, sorted sample list (to calculate +/- threashold for MIR), special events list
# to calculate FPR (false positive rate)
def fpr(df1, mir_list, event_list):
    mir_list = np.array(sorted(mir_list))
    split1 = 0
    while (mir_list[split1] < 0):
        split1 += 1

    split2 = split1
    while (mir_list[split2] <= 0):
        split2 += 1

    neg_list = mir_list[:split1]
    pos_list = mir_list[split2:]
    neg_avg_mir = np.mean(neg_list)
    pos_avg_mir = np.mean(pos_list)
    print('negative average MIR: ', neg_avg_mir)
    print('positive average MIR: ', pos_avg_mir)

    # calculate special events' MIR
    mir_events = pd.DataFrame(np.zeros(len(event_list)), columns=['MIR'])
    temp = 0
    for i in range(len(event_list)):
        while (str(df1.index[temp]) != event_list[i] and temp < len(df1) - 1):
            temp += 1
        mir_events.MIR[i] = compute_MIR_tick(df1, df1.loc[df1.index[temp], 'num'])
    mir_events.index = event_list
    mir_events.name = 'time'
    print(mir_events)

    # fpr = false events/total events
    count = 0
    for mir in mir_events.MIR:
        if (neg_avg_mir < mir < pos_avg_mir):
            print(mir)
            count += 1
    fp_rate = count / len(mir_events)

    return fp_rate