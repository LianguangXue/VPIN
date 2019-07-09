import pandas as pd
from Parallezing_MIR import *
from Tick_VPIN import *


if __name__=='__main__':
#   read data
    #dat1 = pd.read_csv('MSFT_tick.csv', sep=',', index_col=0)
    dat1 = pd.read_csv('MSFT_tick.csv', sep=',', index_col=0)
    dat1.head()

#   Step 1.
    print('Step1')
#   VPIN caculating step
    time_bucket_list,bucket_price,vpin_norm_list,high_list,low_list,time_list,price_list,diff_list,bar_remain,\
    bucket_remain,std_price,volume_per_bar = vpin_combine(dat1,bars_per_bucket = 30,
                                                          buckets_per_day=1836,support_window=0.0478)
#   detect VPIN event
    event_time_list = VPIN_event_detect(vpin_norm_list, time_bucket_list, CDF_threshold=0.99)
#   Construct bars
    bar = {"high": high_list, "low": low_list}
    bar = pd.DataFrame(bar)
    bar.index = pd.to_datetime(time_list)
    bar.index.name = 'time'
    # full dataframe (time, seconds, high_p, low_p, MIR, num)
    df_bar = full_df_bar(bar)
    # df1 removes duplicated time entries
    df1 = df_bar.drop_duplicates(subset='seconds', keep='last')
    df1 = df1.assign(num=list(range(0, len(df1))))


#   Step 2.
    print("Step2")
#   Caculate the MIR list
#   to save time we randomly choose 10000 samples
#   df_sample_sorted chooses 10000 samples
    n_sample = 1000
    df_sample_sorted = df1.sample(n_sample).sort_values('seconds')
    sample_num = np.array(df_sample_sorted.num)
    # Parallelizing using Pool.async()
    pool = mp.Pool(mp.cpu_count())
    start = timeit.default_timer()
    mir_list = [pool.apply_async(multiprocess_MIR, args=(i,df1,df_sample_sorted)) for i in range(len(df_sample_sorted))]
    mir_list = [a.get() for a in mir_list]
    stop = timeit.default_timer()
    print("\n\n\nMIR list)")
    print(np.abs(mir_list)[:100])
    print('\n\n\n')
    print(mir_list)
    print('\n\n\n')
    print('Time: ', stop - start)

#   Step 3.
    print('Step3')
#   Caculate the False Positive Rate
    FPR = fpr(df1, mir_list, event_time_list)
    print("\n\n\n FPR:"+str(FPR))