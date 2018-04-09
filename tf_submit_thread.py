#!/usr/bin/env python

from __future__ import print_function

import Queue
import os
import subprocess
import sys
import threading
import time


class Thread(threading.Thread):
    """
    Thread class to run a command - used to run worker jobs

    """
    def __init__(self, cmd, queue):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.queue = queue

    def run(self):
        p = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE)
        output, status = p.communicate()
        self.queue.put((self.cmd, output, status))


class Command(object):
    """
    Command line class.

    """
    def __init__(self, argv):
        # verifying required arguments
        if len(argv) < 3:
            raise Exception(" Missing commands or parameters...")

        # parsing UGE environment variables
        self.job_id = os.environ.get('JOB_ID', 'NONE')
        self.pe_hostfile = os.environ.get('PE_HOSTFILE', 'NONE')
        self.pe_slot = os.environ.get('NSLOTS', 'NONE')
        self.pe_hostname = os.environ.get('HOSTNAME', 'NONE')
        if str(self.job_id) == 'NONE' or str(self.pe_hostfile) == 'NONE' or \
                str(self.pe_slot) == 'NONE' or str(self.pe_slot) == '1' or \
                str(self.pe_hostname) == 'NONE':
            raise Exception(
                'tf_script needs to be run under UGE qsub/qrsh parallel '
                'environment...')

        self.port = self._get_port(argv)
	print (self.port)

        self.tf_script = self._get_tf_script(argv)

        self.worker_list = []
        self._build_worker_list()

        self.master_host = self.worker_list.pop(0)
	print (self.master_host)

        # Keep the list of workers in string
        self.worker_string = ",".join(str(x) for x in self.worker_list)

        self.cmds = []

        self.result_queue = None

    def _get_port(self, argv):
        """
        Parse the port (-p) from argv

        """
        if argv[1] == u'-p':
            try:
                port = int(sys.argv[2])
            except ValueError:
                raise Exception("Port value must be an integer")
        else:
            raise Exception('Missing port parameter: -p <port>')
        return port

    def _get_tf_script(self, argv):
        """
        Parse the tensorflow script from argv

        """
        # The rest of argument assumes TF script & its parameters
        return " ".join(str(e) for e in argv[3:])

    def _build_worker_list(self):
        """
        Constructing TF Cluster Topology list from UGE PE_HOSTFILE

        """
        # parsing PE_HOSTFILE to get list of master and slave nodes that are
        # allocated by UGE.
        port = self.port
        for lines in tuple(open(self.pe_hostfile)):
            host = str(lines).split(" ")[0]
            num = int(str(lines).split(" ")[1])
            for i in range(num):
                self.worker_list.append(host + ":" + str(port))
                port += 1

    def run(self):
        self._initialize_master()
        self._build_worker_commands()
        self._initialize_result_queue()
        self._start_threads()
        self.result_queue.join()

        # print results as we get them
        while threading.active_count() > 1 or not self.result_queue.empty():
            while not self.result_queue.empty():
                (cmd, output, status) = self.result_queue.get()
                print("%s:" % cmd)
                print(output)
                print('=' * 60)
            time.sleep(1)

    def _initialize_master(self):
        print("Initial ps task...")
        # Define qrsh -inherit ... command
        cmd = '$SGE_BINARY_PATH/qrsh -inherit {} python {} -s {} ' \
              '-w {} --job_name="ps" --task_index=0 &'.format(
                  self.master_host.split(":")[0],
                  self.tf_script,
                  self.master_host,
                  self.worker_string
              )
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        print(cmd)

    def _build_worker_commands(self):
        """
        Define the commands to be run in parallel

        """
        print("Initial worker task...")
        for i in range(int(self.pe_slot) - 1):
            cmd = '$SGE_BINARY_PATH/qrsh -inherit {} python {} -s {} ' \
                  '-w {} --job_name="worker" --task_index={}'.format(
                      self.worker_list[i].split(":")[0],
                      self.tf_script,
                      self.master_host,
                      self.worker_string,
                      i
                  )
            self.cmds.append(cmd)
            print(cmd)

    def _initialize_result_queue(self):
        """
        Initialize the results queue.

        """
        self.result_queue = Queue.Queue()

    def _start_threads(self):
        """
        Run the commands as threads.

        """
        for cmd in self.cmds:
            thread = Thread(cmd, self.result_queue)
            thread.start()


if __name__ == '__main__':
    Command(sys.argv).run()
