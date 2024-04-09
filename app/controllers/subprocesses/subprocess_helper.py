import subprocess
"""
A helper module to run and monitor subprocesses running on the background
"""


class Subprocess:
    def __init__(self, name, args):
        self.__process_name: str = name
        self.__process_args: str = args

    def get_process_count(self) -> int:
        process_count = 0

        # get the list of processes matching the process name in the background
        process_list = subprocess.check_output(f"ps -ef | grep {self.__process_name}", shell=True).decode()
        process_list = process_list.split('\n')

        # count the processes containing the desired arguments
        for process in process_list:
            if process.__contains__(self.__process_args):
                process_count += 1
        return process_count

    def run(self) -> str:
        """Run a sub process if and only if no other process exists with the same arguments"""
        proc_count = self.get_process_count()
        if proc_count > 0:
            return f"No subprocess started: {proc_count} already running."
        d_cmd = ["python", self.__process_name, "--data", self.__process_args]
        process = subprocess.Popen(d_cmd)
        return "Subprocess started successfully."
