'''
Originally, information and results from experiment runs were stored
in separate tables (files). This was intended to be transferred to a database
for more professional use. However, this was cut and instead of rewriting 
testLB.py's logging configuration, this program was created for post-processing.

Takes a testInfo.csv file and data.csv file related to the same experiment.
Outputs a combined table with information from each to be used in
results plotting.
'''

import os
import sys
import argparse
from time import time
from statistics import mean, stdev

DEBUG = False # Currently doesn't do anything
CURR_PATH = os.getcwd()

def main():
    init()
    data_dir_path = CURR_PATH + f'/../Data'
    test_dir_path = CURR_PATH + f'/../TestInfo'

    start_time = time()

    print('Combining tables...')
    for test_file_path in os.listdir(test_dir_path):
        test_file = os.path.join(test_dir_path, test_file_path)
        if os.path.isdir(test_file): continue
    
        test_ids, test_avgs, algorithm = fetchTestResults(test_file)

        data_path = data_dir_path + f'/{algorithm}Data.csv'
        data = fetchDataResults(data_path, test_ids, test_avgs, algorithm)

        fileWrite(data, algorithm)

    end_time = time()

    elapsed_time = end_time - start_time
    print(f'That took {round(elapsed_time, 2)} seconds!')

# Receive test_id's with matching num_threads and num_users
def fetchTestResults(test_file):
    # Keys = test_id
    test_ids = {} # Used for cross referencing data samples
    test_lines = {}
    with open(test_file, 'r') as test_file_obj:
        next(test_file_obj)
        lines = test_file_obj.readlines()

        for line in lines:
            line_parsed = line.split(',')
            test_id = line_parsed[0].replace('\n', '')
            num_threads = line_parsed[2].replace('\n', '')
            algorithm = line_parsed[4].replace('\n', '')
            num_users = line_parsed[5].replace('\n', '')
            avg_cpu = line_parsed[7].replace('\n', '')
            stdev_cpu = line_parsed[8].replace('\n', '')

            test_ids[test_id] = [num_threads, num_users]
            test_lines[test_id] = [num_threads, num_users, avg_cpu, stdev_cpu, test_id, algorithm]

    # Collect lists of each run's results
    test_avgs_buff = {}
    for test_id in test_lines:
        num_threads = test_lines[test_id][0]
        num_users = test_lines[test_id][1]
        avg_cpu = test_lines[test_id][2]
        stdev_cpu = test_lines[test_id][3]

        if num_threads not in test_avgs_buff:
            test_avgs_buff[num_threads] = {}
        if num_users not in test_avgs_buff[num_threads]:
            test_avgs_buff[num_threads][num_users] = {}
        if 'avg_cpu' not in test_avgs_buff[num_threads][num_users]:
            test_avgs_buff[num_threads][num_users]['avg_cpu'] = []
        if 'stdev_cpu' not in test_avgs_buff[num_threads][num_users]:
            test_avgs_buff[num_threads][num_users]['stdev_cpu'] = []
        
        test_avgs_buff[num_threads][num_users]['avg_cpu'].append(float(avg_cpu))
        test_avgs_buff[num_threads][num_users]['stdev_cpu'].append(float(stdev_cpu))

    # Average test results in each run, assign to num_threads + num_users
    test_avgs = {}
    for num_threads in test_avgs_buff:
        test_avgs[num_threads] = {}
        for num_users in test_avgs_buff[num_threads]:
            test_avgs[num_threads][num_users] = {}
            test_avgs[num_threads][num_users]['avg_cpu'] = mean(test_avgs_buff[num_threads][num_users]['avg_cpu'])
            test_avgs[num_threads][num_users]['stdev_cpu'] = mean(test_avgs_buff[num_threads][num_users]['stdev_cpu'])

    return test_ids, test_avgs, algorithm

# Create new data table with test info + old data info
def fetchDataResults(data_path, test_ids, test_avgs, algorithm):
    # Key = num_threads, Value = new data line to write
    data = {}

    # Match data entries to test info
    with open(data_path, 'r') as data_file:
        next(data_file)
        lines = data_file.readlines()

        # Iterate through data sample entries in file
        for line in lines:
            line_parsed = line.split(',')
            data_test_id = line_parsed[1]

            # Fetch num_threads and num_users to be used as key
            num_threads = test_ids[data_test_id][0]
            num_users = test_ids[data_test_id][1]

            # Fetch CPU results
            avg_cpu = test_avgs[num_threads][num_users]['avg_cpu']
            stdev_cpu = test_avgs[num_threads][num_users]['stdev_cpu']

            test_str = f'{num_threads},{num_users},{avg_cpu},{stdev_cpu}'
            new_data_str = f'{test_str},{line}'

            if num_threads not in data: data[num_threads] = []
            data[num_threads].append(new_data_str)

    return data

# Write combined data to new files
def fileWrite(data, algorithm):
    for num_threads in data:
        new_data_path = CURR_PATH + f'/../Combined/{algorithm}.csv'
        
        with open(new_data_path, 'w') as new_data_file:
            new_data_file.write('num_threads,num_users,avg_cpu,stdev_cpu,request_id,test_id,type,error,response_time\n')
            for line in data[num_threads]: new_data_file.write(line)

def init():
    global DEBUG

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help = "run a short debug test", action = "store_true")
    args = parser.parse_args()

    if args.debug:
        DEBUG = True
        print('Running in debug mode.')

if __name__ == '__main__': main()