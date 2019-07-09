# Required packages
import pandas as pd
import numpy as np
import os
import csv
import datetime
import re
import codecs
import requests
from scipy.stats import norm
from math import erf
from math import sqrt
from datetime import datetime

#we assume that the tick data only have two useful columns-price and volume, the index for the data is datetime for the tick data
#we assume that transaction is ongoing for the whole day,and the data is sequential
#the volume per bucket is the culmulate volume/number of total buckets(the average volume per day)
#Define the function the extract the today data and previous data
def data_preprocessing(data):
    n = len(data)
    #firstly we split the data with previous data and most recent data(today data)
    Time = data.index
    MC = pd.to_datetime(data.index[-1]) #the most recent data
    TS = pd.datetime(MC.year,MC.month,MC.day,0,0) # the start time for today
    data_today = data[pd.to_datetime(data.index) >= TS]
    data_before = data[pd.to_datetime(data.index)< TS]
    return data_today,data_before

#Define the function to get roughly volume for each bar
def get_average_volume(data_before, bars_per_bucket = 30,buckets_per_day=1836):
    cumulative_volume = np.sum(data_before.volume)
    days_num = len(np.unique(pd.to_datetime(data_before.index).date))#number of days in the data
    total_bars = days_num * buckets_per_day * bars_per_bucket #estimate total bars for the data
    volume_per_bar = int(cumulative_volume/total_bars)
    return total_bars,days_num,volume_per_bar

#get norminal price of each bar(we use the mean price of the bar  as the paper refered)
#define a function to construct bars
#get norminal price of each bar(we use the mean price of the bar  as the paper refered)
#define a function to construct bars
def construct_bars(data,volume_per_bar):
    n = len(data)
    price = data.price.values
    volume = data.volume.values
    temp_volume = 0
    temp_price = 0
    temp_num = 0
    price_list = []
    time_list = []
    cut_point_list = []
    temp_list=[]
    high_list=[]
    low_list=[]
    for i in range(n):
        temp_list.append(price[i])
        temp_volume += volume[i]
        temp_price += price[i]
        temp_num += 1
        while temp_volume >= volume_per_bar:
            price_list.append(temp_price/temp_num)
            time_list.append(data.index[i])
            cut_point_list.append(i)
            temp_volume -= volume_per_bar
            high_list.append(np.max(temp_list))
            low_list.append(np.min(temp_list))
            if temp_volume > 0:
                temp_price = price[i]
                temp_list=[price[i]]
                temp_num = 1
            else:
                temp_list=[]
                temp_price = 0
                temp_num = 0
    print(temp_volume)
    bar_remain = [temp_volume,temp_price,temp_num]
    return price_list,time_list,cut_point_list,high_list[1:],low_list[1:],bar_remain

#defne the function to get diff list for caculate the vpin
#Parameter for the Bulk Volume Classification (BVC) 𝜈(we use the normal distribution, so the 𝜈 is 0)
def bulk_volume_classification(price_list,time_list,cut_point_list, volume_per_bar):
    bar_num = len(price_list)
    price_change = [price_list[i]-price_list[i-1] for i in range(1,bar_num)]
    std_price = np.std(price_change)
    volume_buy_bar_list = (volume_per_bar * norm.cdf(price_change/ std_price)).astype(int)
    volume_sell_bar_list = volume_per_bar - volume_buy_bar_list
    #diff_list = abs(volume_buy_list-volume_sell_list)
    time_list = time_list[1:]
    cut_point_list = cut_point_list[1:]
    return volume_buy_bar_list,volume_sell_bar_list, time_list, cut_point_list,std_price

#define a function to constuct bucket
def constuct_buckets(volume_buy_bar_list ,volume_sell_bar_list, time_list,cut_point_list,bars_per_bucket = 30):
    n = len(volume_buy_bar_list)
    volume_buy_bucket_list=[]
    volume_sell_bucket_list=[]
    diff_list = []
    time_bucket_list=[]
    cut_point_bucket_list = []
    temp = 0
    temp_buy = 0
    temp_sell = 0
    temp_diff = 0
    for i in range(n):
        temp += 1
        temp_buy += volume_buy_bar_list[i]
        temp_sell += volume_sell_bar_list[i]
        if temp == bars_per_bucket:
            temp_diff = abs(temp_buy-temp_sell)
            diff_list.append(temp_diff)
            volume_buy_bucket_list.append(temp_buy)
            volume_sell_bucket_list.append(temp_sell)
            time_bucket_list.append(time_list[i])
            cut_point_bucket_list.append(cut_point_list[i])
            temp = 0
            temp_buy = 0
            temp_sell = 0
    assert(len(diff_list)==len(time_bucket_list))
    bucket_remain = [temp,temp_buy,temp_sell]
    return diff_list ,time_bucket_list,cut_point_bucket_list,bucket_remain

#define the function to caculate the vpin
#the parameters are correspond to the paper:
#Nominal price of a bar 𝜋
#Buckets per day (BPD) 𝛽
#Threshold for VPIN 𝜏
#Support window 𝜎
#Event horizon 𝜂
def vpin_caculation(diff_list,time_bucket_list, cut_point_bucket_list,volume_per_bar,bars_per_bucket = 30,buckets_per_day=1836,support_window=0.0478):
    n = len(diff_list)
    volume_per_bucket = volume_per_bar*bars_per_bucket
    bucket_num = int(buckets_per_day * support_window) #the bucket num we need to caculate the vpin
    time_bucket_list = time_bucket_list[bucket_num+1:]
    cut_point_bucket_list = cut_point_bucket_list[bucket_num+1:]
    vpin_list = []
    for i in range(bucket_num+1,n):
        vpin_list.append(np.sum(diff_list[i-bucket_num:i])/(bucket_num*volume_per_bucket))
    return vpin_list,time_bucket_list, cut_point_bucket_list

#define a function to trainsform the vpin list
def normal_transformation(vpin_list):
    vpin_num = len(vpin_list)
    erf_vector= np.vectorize(erf)
    mean_vpin = np.mean(vpin_list)
    std_vpin = np.std(vpin_list)
    vpin_norm_list = 1/2*(1+erf_vector((vpin_list-mean_vpin)/(np.sqrt(2)*std_vpin)))
    return vpin_norm_list

def vpin_combine(data,bars_per_bucket = 30,buckets_per_day=1836,support_window=0.0478):
    data_today,data_before = data_preprocessing(data)
    total_bars,days_num,volume_per_bar = get_average_volume(data_before,bars_per_bucket = bars_per_bucket,
                                                            buckets_per_day= buckets_per_day)
    price_list,time_list,cut_point_list,high_list,low_list,bar_remain=construct_bars(data,volume_per_bar)
    volume_buy_bar_list ,volume_sell_bar_list, time_list,cut_point_list,std_price = bulk_volume_classification(price_list,time_list,
                                                                                                cut_point_list,volume_per_bar)
    diff_list ,time_bucket_list,cut_point_bucket_list,bucket_remain = constuct_buckets(volume_buy_bar_list ,volume_sell_bar_list,
                                                                    time_list, cut_point_list,bars_per_bucket =  bars_per_bucket)
    vpin_list,time_bucket_list, cut_point_bucket_list = vpin_caculation(diff_list,time_bucket_list,
                                                                        cut_point_bucket_list,volume_per_bar,
                                                                        bars_per_bucket = bars_per_bucket,
                                                                        buckets_per_day=buckets_per_day,
                                                                        support_window=support_window)
    vpin_norm_list = normal_transformation(vpin_list)
    bucket_price = data.price.values[cut_point_bucket_list]
    return time_bucket_list,bucket_price,vpin_norm_list,high_list,low_list,time_list,price_list,diff_list, bar_remain,bucket_remain,std_price,volume_per_bar

#define a function to detect the VPIN even t
def VPIN_event_detect(vpin_norm_list,time_bucket_list,CDF_threshold=0.99):
    n = len(vpin_norm_list)
    event_time_list=[]
    for i in range(1,n):
        if vpin_norm_list[i-1] < CDF_threshold and vpin_norm_list[i] >= CDF_threshold:
            print('VPIN event happen! ---'+str(time_bucket_list[i]))
            event_time_list.append(time_bucket_list[i])
    return event_time_list

#######################update##############################
#define a function to update bars
def construct_bars_update(temp_volume,temp_price,temp_num,data,volume_per_bar):
    n = len(data)
    price = data.price.values
    volume = data.volume.values
    price_list = []
    time_list = []
    cut_point_list = []
    temp_list=[]
    high_list=[]
    low_list=[]
    for i in range(n):
        temp_list.append(price[i])
        temp_volume += volume[i]
        temp_price += price[i]
        temp_num += 1
        while temp_volume >= volume_per_bar:
            price_list.append(temp_price/temp_num)
            time_list.append(data.index[i])
            cut_point_list.append(i)
            temp_volume -= volume_per_bar
            high_list.append(np.max(temp_list))
            low_list.append(np.min(temp_list))
            if temp_volume > 0:
                temp_price = price[i]
                temp_list=[price[i]]
                temp_num = 1
            else:
                temp_list=[]
                temp_price = 0
                temp_num = 0
    print(temp_volume)
    bar_remain = [temp_volume,temp_price,temp_num]
    return price_list,time_list,cut_point_list,high_list[1:],low_list[1:],bar_remain

#define a function to update buy and sell list
def bulk_volume_classification_update(std_price,price_list, volume_per_bar):
    bar_num = len(price_list)
    price_change = [price_list[i]-price_list[i-1] for i in range(1,bar_num)]
    volume_buy_bar_list = (volume_per_bar * norm.cdf(price_change/ std_price)).astype(int)
    volume_sell_bar_list = volume_per_bar - volume_buy_bar_list
    #diff_list = abs(volume_buy_list-volume_sell_list)
    return volume_buy_bar_list ,volume_sell_bar_list


#define a function to update buckets
def constuct_buckets_update(temp,temp_buy,temp_sell,volume_buy_bar_list ,volume_sell_bar_list,
                            time_list,cut_point_list,bars_per_bucket = 30):
    n = len(volume_buy_bar_list)
    volume_buy_bucket_list=[]
    volume_sell_bucket_list=[]
    diff_list = []
    time_bucket_list=[]
    cut_point_bucket_list = []
    temp_diff = 0
    for i in range(n):
        temp += 1
        temp_buy += volume_buy_bar_list[i]
        temp_sell += volume_sell_bar_list[i]
        if temp == bars_per_bucket:
            temp_diff = abs(temp_buy-temp_sell)
            diff_list.append(temp_diff)
            volume_buy_bucket_list.append(temp_buy)
            volume_sell_bucket_list.append(temp_sell)
            time_bucket_list.append(time_list[i])
            cut_point_bucket_list.append(cut_point_list[i])
            temp = 0
            temp_buy = 0
            temp_sell = 0
    assert(len(diff_list)==len(time_bucket_list))
    bucket_remain = [temp,temp_buy,temp_sell]
    return diff_list ,time_bucket_list,cut_point_bucket_list,bucket_remain


# define a fucntion to update vpin list
def vpin_caculation_update(old_diff_list, new_diff_list, volume_per_bar, bars_per_bucket=30, buckets_per_day=1836,
                           support_window=0.0478):
    bucket_num = int(buckets_per_day * support_window)  # the bucket num we need to caculate the vpin
    new_diff_list = old_diff_list[-bucket_num:] + new_diff_list
    n = len(new_diff_list)
    volume_per_bucket = volume_per_bar * bars_per_bucket

    vpin_list = []
    for i in range(bucket_num, n):
        vpin_list.append(np.sum(new_diff_list[i - bucket_num:i]) / (bucket_num * volume_per_bucket))
    return vpin_list


#define a function to cobine to update programs
def vpin_tick_caculation_update(new_data,
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
                                volume_per_bar):
    temp_volume = bar_remain[0]
    temp_price =  bar_remain[1]
    temp_num = bar_remain[2]
    new_price_list,new_time_list,new_cut_point_list,new_high_list,new_low_list,bar_remain = construct_bars_update(temp_volume,
                                                                                              temp_price,
                                                                                              temp_num,new_data,
                                                                                              volume_per_bar)
    end_price = price_list[-1]
    price_list += new_price_list
    new_price_list = [end_price] + new_price_list
    time_list += new_time_list
    high_list += new_high_list
    low_list += new_low_list
    std_price = np.std(price_list)
    new_volume_buy_bar_list ,new_volume_sell_bar_list = bulk_volume_classification_update(std_price,
                                                                                          new_price_list,
                                                                                          volume_per_bar)
    temp = bucket_remain[0]
    temp_buy = bucket_remain[1]
    temp_sell = bucket_remain[2]
    new_diff_list ,new_time_bucket_list,new_cut_point_bucket_list,bucket_remain = constuct_buckets_update(temp,temp_buy,temp_sell,
                                                                                              new_volume_buy_bar_list ,
                                                                                              new_volume_sell_bar_list,
                                                                                              new_time_list,new_cut_point_list,
                                                                                              bars_per_bucket = 30)
    time_bucket_list += new_time_bucket_list
    vpin_list = vpin_caculation_update(diff_list,new_diff_list,volume_per_bar,bars_per_bucket = 30,
                                       buckets_per_day=1836,support_window=0.0478)
    diff_list += new_diff_list
    new_vpin_norm_list = normal_transformation(vpin_list)
    vpin_norm_list = list(vpin_norm_list)
    vpin_norm_list += list(new_vpin_norm_list)
    new_bucket_price = new_data.price.values[new_cut_point_bucket_list]
    bucket_price = list(bucket_price)
    bucket_price += list(new_bucket_price)
    print(new_vpin_norm_list)
    print(new_time_bucket_list)
    return new_time_bucket_list,new_bucket_price,new_vpin_norm_list,high_list,low_list,time_list,time_bucket_list,\
           bucket_price,vpin_norm_list,bar_remain,bucket_remain,std_price,volume_per_bar


