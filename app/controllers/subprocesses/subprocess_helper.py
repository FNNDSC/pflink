import subprocess
"""
A helper module to monitor subprocesses running on the background
"""


def get_process_count(process_name: str, process_args: str):
    process_count = 0
    process_list = subprocess.check_output(f"ps -ef | grep {process_name}", shell=True).decode()
    process_list = process_list.split('\n')

    for process in process_list:
        if process.__contains__(process_args):
            process_count += 1
    return process_count
