import os
import sys
from math import sqrt
from statistics import mean, stdev

CONFIDENCE = 0.95

def fetchData(data_dir_path):
    # Each task type has its own dataframe
    user_count = []
    data = {}
    data['GET'] = {}
    data['POST'] = {}

    # Load in all values
    for data_file in os.listdir(data_dir_path):
        print(f'Fetching from {data_file}...')
        data_file_path = os.path.join(data_dir_path, data_file)
        algorithm = data_file.replace('.csv', '')
        data['GET'][algorithm] = {}
        data['POST'][algorithm] = {}

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

                # Add num_users as new key
                if num_users not in data[task_type][algorithm]:
                    data[task_type][algorithm][num_users] = {}
                    data[task_type][algorithm][num_users]['avg_cpu'] = avg_cpu
                    data[task_type][algorithm][num_users]['sdtev_cpu'] = stdev_cpu
                    data[task_type][algorithm][num_users]['error'] = []
                    data[task_type][algorithm][num_users]['response_time'] = []

                # Append metrics to list
                data[task_type][algorithm][num_users]['error'].append(int(error))
                data[task_type][algorithm][num_users]['response_time'].append(int(response_time))

    # Average values for metrics
    for task_type in data:
        for algorithm in data[task_type]:
            for num_users in data[task_type][algorithm]:
                samples = data[task_type][algorithm][num_users]

                # Error
                try:
                    # print(
                    #     f'task_type: {task_type}\n'
                    #     f'algorithm: {algorithm}\n'
                    #     f'num_users: {num_users}'
                    # )
                    err_len = len(samples['error'])
                except TypeError:
                    print('*** Error ***')
                    sys.exit()
                data[task_type][algorithm][num_users]['avg_error'] = mean(samples['error'])
                data[task_type][algorithm][num_users]['stdev_error'] = stdev(samples['error'])
                data[task_type][algorithm][num_users]['ci_error'] = \
                    CONFIDENCE * (data[task_type][algorithm][num_users]['stdev_error'] / sqrt(err_len))

                # Response Time
                time_len = len(samples['response_time'])
                data[task_type][algorithm][num_users]['avg_time'] = mean(samples['response_time'])
                data[task_type][algorithm][num_users]['stdev_time'] = stdev(samples['response_time'])
                data[task_type][algorithm][num_users]['ci_time'] = \
                    CONFIDENCE * (data[task_type][algorithm][num_users]['stdev_time'] / sqrt(time_len))

                # Deadline miss rate
                resp_times = samples['response_time']
                miss_count = 0
                for time in resp_times:
                    if float(time) > 1000: miss_count += 1
                data[task_type][algorithm][num_users]['deadline_miss'] = \
                    miss_count / len(resp_times)

    # Sort dict by num_users key value
    data = toList(data)
    user_count.sort()

    return data, user_count

# Easier to plot with list
def toList(data_buff):
    data = {}

    for task_type in data_buff:
        data[task_type] = {}

        for algorithm in data_buff[task_type]:
            data[task_type][algorithm] = {}

            for num_users in data_buff[task_type][algorithm]:
                for metric in data_buff[task_type][algorithm][num_users]:
                    data[task_type][algorithm][metric] = []
                break # Leave early

            # Sort by num_users key
            for num_users in sorted(data_buff[task_type][algorithm].keys()):
                for metric in data_buff[task_type][algorithm][num_users]:
                    try:
                        sample = data_buff[task_type][algorithm][num_users][metric]
                    except KeyError:
                        print(
                            f'task_type: {task_type}\n'
                            f'algorithm: {algorithm}\n'
                            f'num_users: {num_users}\n'
                            f'metric: {metric}\n'
                        )
                        sys.exit()
                    if type(sample) is not list: # We don't need list metrics
                        data[task_type][algorithm][metric].append(sample)

    return data