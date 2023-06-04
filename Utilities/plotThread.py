import os
import sys
from math import sqrt
from statistics import mean, stdev
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CURR_PATH = os.getcwd()
CONFIDENCE = 0.95

def main():
    data_dir_path = CURR_PATH + f'/../Combined/ThreadTuning'

    data, user_count = fetchData(data_dir_path)

    plotThreadTime(data, user_count)

def fetchData(data_dir_path):
    # Key = task_type + num_threads + num_users + metric
    # Nested af
    data = {}
    data['GET'] = {}
    data['POST'] = {}
    user_count = []

    for data_file in os.listdir(data_dir_path):
        print(f'Fetching from {data_file}...')
        data_file_path = os.path.join(data_dir_path, data_file)
        thread_count = data_file.replace('.csv', '')
        data['GET'][thread_count] = {}
        data['POST'][thread_count] = {}

        with open(data_file_path, 'r') as file:
            next(file)
            lines = file.readlines()

            for line in lines:
                line_split = line.split(',')

                num_users = int(line_split[1])
                avg_cpu = float(line_split[2])
                stdev_cpu = float(line_split[3])
                task_type = line_split[6]
                error = int(line_split[7])
                response_time = float(line_split[8])

                if int(num_users) not in user_count:
                    user_count.append(int(num_users))

                if num_users not in data[task_type][thread_count]:
                    data[task_type][thread_count][num_users] = {}
                    data[task_type][thread_count][num_users]['avg_cpu'] = avg_cpu
                    data[task_type][thread_count][num_users]['stdev_cpu'] = stdev_cpu
                    data[task_type][thread_count][num_users]['error'] = []
                    data[task_type][thread_count][num_users]['response_time'] = []

                data[task_type][thread_count][num_users]['error'].append(int(error))
                data[task_type][thread_count][num_users]['response_time'].append(int(response_time))

    for task_type in data:
        for thread_count in data[task_type]:
            for num_users in data[task_type][thread_count]:
                samples = data[task_type][thread_count][num_users]

                try:
                    err_len = len(samples['error'])
                except TypeError:
                    print('*** Error ***')
                    sys.exit()

                data[task_type][thread_count][num_users]['avg_error'] = mean(samples['error'])
                data[task_type][thread_count][num_users]['stdev_error'] = stdev(samples['error'])
                data[task_type][thread_count][num_users]['ci_error'] = \
                    CONFIDENCE * (data[task_type][thread_count][num_users]['stdev_error'] / sqrt(err_len))


                time_len = len(samples['response_time'])
                data[task_type][thread_count][num_users]['avg_time'] = mean(samples['response_time'])
                data[task_type][thread_count][num_users]['stdev_time'] = stdev(samples['response_time'])
                data[task_type][thread_count][num_users]['ci_time'] = \
                    CONFIDENCE * (data[task_type][thread_count][num_users]['stdev_time'] / sqrt(time_len))

                resp_times = samples['response_time']
                miss_count = 0
                for time in resp_times:
                    if float(time) > 1000: miss_count += 1
                data[task_type][thread_count][num_users]['deadline_miss'] = \
                    miss_count / len(resp_times)

    data = toList(data)
    user_count.sort()

    return data, user_count

def toList(data_buff):
    data = {}

    for task_type in data_buff:
        data[task_type] = {}

        for thread_count in data_buff[task_type]:
            data[task_type][thread_count] = {}

            for num_users in data_buff[task_type][thread_count]:
                for metric in data_buff[task_type][thread_count][num_users]:
                    data[task_type][thread_count][metric] = []
                break

            for num_users in sorted(data_buff[task_type][thread_count].keys()):
                for metric in data_buff[task_type][thread_count][num_users]:
                    try:
                        sample = data_buff[task_type][thread_count][num_users][metric]
                    except KeyError:
                        print(
                            f'task_type: {task_type}\n'
                            f'thread_count: {thread_count}\n'
                            f'num_users: {num_users}\n'
                            f'metric: {metric}'
                        )
                        sys.exit()
                    
                    if type(sample) is not list:
                        data[task_type][thread_count][metric].append(sample)

    return data

def plotThreadTime(data, user_count):
    plt.rcParams.update({'font.size': 10})

    user_count = [x * 5 for x in user_count]
    user_count = [x / 1000 for x in user_count]
    N = len(user_count)
    width = 0.125

    bar1 = np.arange(N)
    bar10 = [x + width for x in bar1]
    bar20 = [x + width for x in bar10]
    bar30 = [x + width for x in bar20]
    bar40 = [x + width for x in bar30]
    bar50 = [x + width for x in bar40]
    bar60 = [x + width for x in bar50]

    tc_to_bar = {
        '1' : bar1,
        '10' : bar10,
        '20' : bar20,
        '30' : bar30,
        '40' : bar40,
        '50' : bar50,
        '60' : bar60
    }

    bar_color = {
        '1' : '#00C0FF',
        '10' : '#FFC069',
        '20' : '#EE9176',
        '30' : '#BD717D',
        '40' : '#815A72',
        '50' : '#72B8AA',
        '60' : '#4B4453'
    }

    i = 0
    for task_type in data:
        i += 1
        plt.subplot(2, 1, i)

        for thread_count in data[task_type]:
            ci = data[task_type][thread_count]['ci_time']
            x_bar = tc_to_bar[thread_count]
            y_buff = data[task_type][thread_count]['avg_time']
            y_values = [y / 1000 for y in y_buff]

            c = bar_color[thread_count]

            plt.bar(
                x_bar, y_values,
                width = width, label = f'{thread_count} Threads',
                zorder = 3, color = c
            )

        plt.axhline(y = 1, color = 'r', linestyle = '--', label = 'Deadline', zorder = 4)
        plt.title(f'HTTP {task_type} Task Types', x = 0.5, y = 0.8)
        plt.yticks([2, 4, 6, 8], ['2', '4', '6', '8'])
        if i == 1:
            # plt.legend(ncols = 2)
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
        plt.grid(axis = 'y', zorder = 0, alpha = 0.5)
        if i ==1: plt.tick_params(bottom = False, labelbottom = False)
        else: plt.xticks(bar30, user_count)
        if i == 1: plt.xlabel('')
        else: plt.xlabel('Number of Tasks per 60s (x1000)')
        if i == 1: plt.ylabel('')
        else: plt.ylabel('')

    plt.ylabel('Response Time (s) / Request')
    plt.tight_layout()
    fig_path = CURR_PATH + '/../Figures/threadTuning/threadTimes.pdf'
    plt.savefig(fig_path)

if __name__ == '__main__': main()