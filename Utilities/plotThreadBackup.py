import os
import gc
import sys
import argparse
from statistics import mean, stdev
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DEBUG = False
CURR_PATH = os.getcwd()

def main():
    init()

    data_dir_path = CURR_PATH + f'/../Combined/ThreadTuning'

    data = fetchData(data_dir_path)

    plotThreadTime(data)

def fetchData(data_dir_path):
    # Key = num_threads + num_users + task_type + metric
    # Nested af
    data_buff = {}

    # Claim info from partitioned data files
    for data_file_path in os.listdir(data_dir_path):
        data_file = os.path.join(data_dir_path, data_file_path)
        if os.path.isdir(data_file): continue
        print(f'Claiming data file {data_file_path}.')
        num_threads = data_file_path.replace('.csv', '')

        if num_threads not in data_buff: data_buff[num_threads] = {}

        # Fetch all samples
        data_buff[num_threads] = parseDataFile(data_file)

        # Fetch averages
        # data[num_threads] = fetchDataBuff(data_raw)

    if DEBUG == True: printDataTable(data_buff)

    # Key = task_type + num_threads + num_users + metric
    data = {}
    for num_threads in data_buff:
        for num_users in data_buff[num_threads]:
            for task_type in data_buff[num_threads][num_users]:
                data[task_type] = {}
            break
        break

    return data

# Fetch inidividual run (num_threads) data
def parseDataFile(data_file):
    # Key = num_users + task_type
    data_raw = {}
    data_raw_buff = {} # Used for averaging

    # Parse data file
    with open(data_file, 'r') as data_file_obj:
        next(data_file_obj)
        lines = data_file_obj.readlines()

        # num_threads,num_users,avg_cpu,stdev_cpu,request_id,test_id,type,error,response_time
        for line in lines:
            line = line.replace('\n', '')
            line_parsed = line.split(',')

            # Newline is very persistent on staying
            try:
                num_users = line_parsed[1].replace('\n', '')
                avg_cpu = line_parsed[2].replace('\n', '')
                stdev_cpu = line_parsed[3].replace('\n', '')
                task_type = line_parsed[6].replace('\n', '')
                err = line_parsed[7].replace('\n', '')
                resp_time = line_parsed[8].replace('\n', '')
            except IndexError:
                print(f'File: {data_file}')
                print(f'Line: {line}')
                sys.exit()

            # THIS can be cleaned up
            # If we have not seen a task with these features
            if num_users not in data_raw:
                if DEBUG == True: print(f'New num_users found: {num_users}')
                data_raw[num_users] = {}
            if task_type not in data_raw[num_users]:
                if DEBUG == True: print(f'New task_type found: {task_type}')
                data_raw[num_users][task_type] = {}
            if num_users not in data_raw_buff:
                data_raw_buff[num_users] = {}
            if task_type not in data_raw_buff[num_users]:
                data_raw_buff[num_users][task_type] = {}
            # avg_cpu and stdev_cpu are static values, no nead to list
            if 'avg_cpu' not in data_raw_buff[num_users][task_type]:
                data_raw_buff[num_users][task_type]['avg_cpu'] = 0
            if 'stdev_cpu' not in data_raw_buff[num_users][task_type]:
                data_raw_buff[num_users][task_type]['stdev_cpu'] = 0
            if 'err' not in data_raw_buff[num_users][task_type]:
                data_raw_buff[num_users][task_type]['err'] = []
            if 'resp_time' not in data_raw_buff[num_users][task_type]:
                data_raw_buff[num_users][task_type]['resp_time'] = []

            # Append to data_raw_buff
            # avg_cpu and stdev_cpu get written with every line but oh well
            data_raw_buff[num_users][task_type]['avg_cpu'] = float(avg_cpu)
            data_raw_buff[num_users][task_type]['stdev_cpu'] = float(stdev_cpu)
            data_raw_buff[num_users][task_type]['err'].append(float(err))
            data_raw_buff[num_users][task_type]['resp_time'].append(float(resp_time))

    # Average values across tests
    for num_users in data_raw_buff:
        for task_type in data_raw_buff[num_users]:
            # Was getting long
            data_sample = data_raw_buff[num_users][task_type]
            data_raw[num_users][task_type]['avg_cpu'] = data_sample['avg_cpu']
            data_raw[num_users][task_type]['stdev_cpu'] = data_sample['stdev_cpu']
            data_raw[num_users][task_type]['avg_err'] = mean(data_sample['err'])
            data_raw[num_users][task_type]['stdev_err'] = stdev(data_sample['err'])
            data_raw[num_users][task_type]['avg_resp_time'] = mean(data_sample['resp_time'])
            data_raw[num_users][task_type]['stdev_resp_time'] = stdev(data_sample['resp_time'])

    return data_raw

def plotThreadTime(data):
    # Number of num_users indices
    N = 0
    user_count = []
    for num_threads in data:
        N = len(data[num_threads].keys())
        for num_users in data[num_threads]:
            user_count.append(num_users)
        break     
    width = 0.25
    # Location of bars on x axis respective to task_type
    bar1 = np.arange(N)
    bar2 = [x + width for x in bar1]

    get = mpatches.Patch(color = 'red', label = 'GET')
    post = mpatches.Patch(color = 'blue', label = 'POST')

    # Use first thread dict entries for testing purposes
    if DEBUG == True: debugPlot(data, bar1, bar2, width, N, user_count)

    plt.rcParams.update({'font.size': 20})

    # Key = task_type
    time_avg_list = {}
    time_stdev_list = {}
    task_types = []
    for num_threads in data:
        for num_users in data[num_threads]:
            print(f'\nnum_users: {num_users}')
            for task_type in data[num_threads][num_users]:
                if task_type not in task_types: task_types.append(task_type)
                if task_type not in time_avg_list: time_avg_list[task_type] = []
                if task_type not in time_stdev_list: time_stdev_list[task_type] = []
                avg_resp_time = data[num_threads][num_users][task_type]['avg_resp_time']
                stdev_resp_time = data[num_threads][num_users][task_type]['stdev_resp_time']
                time_avg_list[task_type].append(avg_resp_time)
                time_stdev_list[task_type].append(stdev_resp_time)

        for task_type in task_types:
            if task_type == 'GET':
                which_bar = bar1
                color = 'red'
            else:
                which_bar = bar2
                color = 'blue'
            plt.bar(
                which_bar, time_avg_list[task_type],
                width = width, label = f'{task_type}', color = color
            )

        plt.title(f'{num_threads} thread(s)')
        plt.legend(handles = [get, post])
        plt.xticks([r + width for r in range(N)], user_count)
        plt.xlabel('Number of Users (request count)')
        plt.ylabel('Average Response Time per Request (ms)')
        plt.title(f'{num_threads} thread(s)')
        plt.grid()

        fig_path = CURR_PATH + f'/../Figures/ThreadTuning/{num_threads}time.pdf'
        plt.savefig(fig_path)

        time_avg_list.clear()
        time_stdev_list.clear()

def printDataTable(data):
    ex_get = {}
    ex_post = {}

    print(f'num_threads: {data.keys()}')
    for num_threads in data:
        print(f'num_users: {data[num_threads].keys()}')
        for num_users in data[num_threads]:
            print(f'task_type: {data[num_threads][num_users].keys()}')
            for task_type in data[num_threads][num_users]:
                print(f'metric: {data[num_threads][num_users][task_type].keys()}')
                break
            break
        break

    count = 0
    for num_threads in data:
        for num_users in data[num_threads]:
            if count == 2: break
            get_resp_time = data[num_threads][num_users]['GET']['avg_resp_time']
            post_resp_time = data[num_threads][num_users]['POST']['avg_resp_time']
            ex_get[num_users] = get_resp_time
            ex_post[num_users] = post_resp_time
        break
    print('\nGET')
    for num_users in ex_get:
        print(f'{num_users}: {ex_get[num_users]}')
    print('\nPOST')
    for num_users in ex_post:
        print(f'{num_users}: {ex_post[num_users]}')

def debugPlot(data, bar1, bar2, width, N, user_count):
    first_thread_value = 0
    for num_threads in data:
        first_thread_value = num_threads
        break

    get_values = []
    post_values = []
    for num_users in data[first_thread_value]:
        get_time = data[first_thread_value][num_users]['GET']['avg_resp_time']
        post_time = data[first_thread_value][num_users]['POST']['avg_resp_time']
        get_values.append(get_time)
        post_values.append(post_time)

    plt.bar(
        bar1, get_values,
        width = width, label = 'GET'
    )
    plt.bar(
        bar2, post_values,
        width = width, label = 'POST'
    )

    plt.xlabel('Number of Users (request count)')
    plt.ylabel('Average Response Time per Request (ms)')
    plt.title(f'HAProxy Performance\n{first_thread_value} Thread(s) Total / 1 Thread per Core')
    plt.xticks([r + width for r in range(N)], user_count)

    plt.legend()
    fig_path = CURR_PATH + '/../Figures/timeDebug.png'
    plt.savefig(fig_path)

    sys.exit()

def init():
    global DEBUG

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help = "run a short debug test", action = "store_true")
    args = parser.parse_args()

    if args.debug:
        DEBUG = True
        print('Running in debug mode.')

if __name__ == '__main__': main()