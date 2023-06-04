import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from averageData import fetchData, toList

DEBUG = False
MACHINE_CONFIG = None
CURR_PATH = os.getcwd()

def main():
    data_dir_path = CURR_PATH + f'/../Combined/{MACHINE_CONFIG}'

    data, user_count = fetchData(data_dir_path)

    plotAlgorithmTime(data, user_count)
    # plotAlgorithmErr(data, user_count)
    # plotDeadlineMiss(data, user_count)

def plotAlgorithmTime(data, user_count):
    plt.rcParams.update({'font.size': 10})

    user_count = [x * 5 for x in user_count]
    user_count = [x / 1000 for x in user_count]

    line_color = {
        'source' : '#00C0FF',
        'first' : '#FFC069',
        'random' : '#EE9176',
        'uri' : '#BD717D',
        'leastconn' : '#815A72',
        'roundrobin' : '#72B8AA',
        'static-rr' : '#4B4453'
    }

    i = 0
    for task_type in data:
        i += 1
        plt.subplot(2, 1, i)

        for algorithm in data[task_type]:
            ci = data[task_type][algorithm]['ci_time']
            y_buff = data[task_type][algorithm]['avg_time']
            c = line_color[algorithm]
            y_values = [y / 1000 for y in y_buff]

            plt.plot(
                user_count, y_values,
                marker = 'o', label = algorithm, zorder = 3, color = c
            )

            # Plot confidence interval
            # plt.fill_between(
            #     user_count, (y_values - ci), (y_values + ci),
            #     alpha = 0.1
            # )

        plt.axhline(y = 1, color = 'r', linestyle = '--', label = 'Deadline', zorder = 4)
        # plt.title(f'{task_type} Task Types', x = 0.5, y = 0.8)
        plt.title(f'HTTP {task_type} Task Types')
        plt.yticks([50, 100, 150, 200, 250, 300, 350, 400], ['50', '100', '150', '200', '250', '300', '350', '400'])
        #plt.yticks([5, 10, 15, 20, 25, 30, 35], ['5', '10', '15', '20', '25', '30', '35'])
        if i == 1:
            # plt.legend(ncols = 2, fontsize = 8)
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
            plt.tick_params(bottom = False, labelbottom = False)
            plt.xlabel('')
            plt.ylabel('')
        else:
            plt.xlabel('Number of Tasks per 60s (x1000)')
            plt.ylabel('Response Time (s) / Request')

    plt.tight_layout()
    fig_path = CURR_PATH + f'/../Figures/Algorithms/resp_time{MACHINE_CONFIG}.png'
    fig_path = CURR_PATH + f'/../Figures/Algorithms/resp_time{MACHINE_CONFIG}.pdf'
    plt.savefig(fig_path)

def plotAlgorithmErr(data, user_count):
    plt.rcParams.update({'font.size': 10})

    user_count = [x * 5 for x in user_count]
    user_count = [x / 1000 for x in user_count]

    i = 0
    for task_type in data:
        i += 1
        plt.subplot(2, 1, i)

        for algorithm in data[task_type]:
            ci = data[task_type][algorithm]['ci_error']
            y_buff = data[task_type][algorithm]['avg_error']
            y_values = [x * 100 for x in y_buff]

            plt.plot(
                user_count, y_values,
                marker = 'o', label = algorithm, zorder = 3
            )

            # Plot confidence interval
            # plt.fill_between(
            #     user_count, (y_values - ci), (y_values + ci),
            #     alpha = 0.1
            # )

        # plt.title(f'{task_type} Task Types', x = 0.5, y = 0.8)
        plt.title(f'{task_type} Task Types')
        plt.grid(zorder = 0, alpha = 0.5)
        if i == 1:
            # plt.legend(ncols = 2, fontsize = 8)
            plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
            plt.tick_params(bottom = False, labelbottom = False)
            plt.xlabel('')
            plt.ylabel('')
        else:
            plt.xlabel('Number of Tasks (k) per 60s')
            plt.ylabel('Error Rate (%)')

    plt.tight_layout()
    fig_path = CURR_PATH + f'/../Figures/Algorithms/error{MACHINE_CONFIG}.png'
    fig_path = CURR_PATH + f'/../Figures/Algorithms/error{MACHINE_CONFIG}.pdf'
    plt.savefig(fig_path)

def plotDeadlineMiss(data):
    plt.rcParams.update({'font.size': 10})

    data_list, task_types, user_count = toList(data)

    # Each algorithm has its own bar location (relative to previous bar)
    bars = {}
    prev_bar = {}
    width = 0.25

    # 2 x 1 subplot
    for algorithm in data_list:
        if algorithm not in bars:
            bars[algorithm] = {}

        # Find bar index (need to know if first algorithm)
        # Does this need to be ordered?
        idx = list(data_list.keys()).index(algorithm)

        for task_type in data_list[algorithm]:
            y_values = data_list[algorithm][task_type]['deadline_miss']
            y_values = np.array(y_values)
            user_count = [x * 5 for x in user_count]
            user_count = np.array(user_count)
            threshold = 8000
            filt = y_values < 8000

            if task_type not in prev_bar:
                prev_bar[task_type] = 0

            if task_type not in bars[algorithm]:
                bars[algorithm][task_type] = None

            # If first algorithm, set baseline location
            if idx == 0:
                bars[algorithm][task_type] = np.arange(len(y_values[filt]))
            # Else bar location is relative to previous bar
            else:
                bars[algorithm][task_type] = [x + width for x in prev_bar[task_type]]

            prev_bar[task_type] = bars[algorithm][task_type]

            # Which subplot to use
            i = task_types.index(task_type)
            plt.subplot(2, 1, (i + 1)) # Index must start at 1

            plt.bar(
                bars[algorithm][task_type], y_values[filt],
                width = width, label = algorithm
            )

            plt.title(f'{task_type} Requests')
            plt.xlabel('Number of User Requests per 60s')
            plt.ylabel('Deadline Miss Rate (%)')
            plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            # Is this necessary?
            plt.xticks(
                [r + width for r in range(len(y_values[filt]))],
                user_count
            )
            if i == 0: plt.legend()
            plt.grid()

    plt.tight_layout()
    fig_path = CURR_PATH + f'/../Figures/alg-deadline_miss.pdf'
    plt.savefig(fig_path)

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

def init():
    global DEBUG
    global MACHINE_CONFIG

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help = "run a short debug test", action = "store_true")
    parser.add_argument('-m', '--machine', help = 'machine environment', type = str, required = True)
    args = parser.parse_args()

    if args.debug:
        DEBUG = True
        print('Running in debug mode.')

    MACHINE_CONFIG = args.machine
    poss_mconfigs = ['Homogen', 'Heterogen']
    if MACHINE_CONFIG not in poss_mconfigs:
        print(f'Uknown machine configuration.\nPossible configurations: {poss_mconfigs}')
        sys.exit()

if __name__ == '__main__':
    init()
    main()