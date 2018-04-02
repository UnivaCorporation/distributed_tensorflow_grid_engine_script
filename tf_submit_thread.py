#!/opt/unicloud/bin/python

import sys
import os
import commands
import threading
import Queue
import time

# thread class to run a command - used to run worker jobs
class Thread(threading.Thread):
    def __init__(self, cmd, queue):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.queue = queue

    def run(self):
        # execute the command, queue the result
        (status, output) = commands.getstatusoutput(self.cmd)
        self.queue.put((self.cmd, output, status))

##--------------------------------------------------------
## Verify if the wrapper script is able to run
##--------------------------------------------------------

# parsing UGE environment variables
job_id = os.environ.get('JOB_ID')
pe_hostfile=os.environ.get('PE_HOSTFILE')
pe_slot=os.environ.get('NSLOTS')
pe_hostname=os.environ.get('HOSTNAME')

if str(job_id)=="NONE" or str(pe_hostfile)=="NONE" or str(pe_slot)=="NONE" or str(pe_slot)=="1" or str(pe_hostname)=="NONE":
        print "tf_script needs to be run under UGE qsub/qrsh parallel environment..."
        sys.exit(2)

# verifying required arguments
if len(sys.argv)<3:
        print " Missing commands or parameters..."
        sys.exit(2)

# parsing parameters to get port (-p) and tensorflow script
if sys.argv[1]==u'-p':
	try:
		port=int(sys.argv[2])
	except ValueError:
		print("Port value is invalid...")
		sys.exit(2)
else:
	print("tf_submit.py -p <port>")
	print("Missing parameter...")
	sys.exit(2)

# Get the Tensor flow script and its parameters
tf_script=" ".join(str(e) for e in sys.argv[3:]) 	# The rest of argument assumes TF script & its parameters

##------------------------------------------------------------
## Constructing TF Cluster Topology list from UGE PE_HOSTFILE
##------------------------------------------------------------

worker_list=[]
master_host=""

# parsing PE_HOSTFILE to get list of master and slave nodes that are allocated by UGE.
try:
        for lines in tuple(open(pe_hostfile,'r')):
                host=str(lines).split(" ")[0]
                num=int(str(lines).split(" ")[1])
                for i in range(num):
                        worker_list.append(host+":"+str(port))
                        port=port+1

except Exception as e:
        print e
master_host=worker_list[0]	# First node will be used as master
worker_list.pop(0)
worker_str=",".join(str(x) for x in worker_list)	# Keep the list of workers in string

print "Initial ps task..."

# Define qrsh -inherit ... command
command='$SGE_BINARY_PATH/qrsh -inherit '+master_host.split(":")[0]+' python '+str(tf_script)+' -s '+master_host+' -w '+worker_str+' --job_name="ps" --task_index=0 &'
os.system(command)	## Starting ps...
os.system('sleep 1')
print command		

cmds=[]
print "Initial worker task..."
for i in range(int(pe_slot)-1):
	command='$SGE_BINARY_PATH/qrsh -inherit '+str(worker_list[i].split(":")[0])+' python '+str(tf_script)+' -s '+master_host+' -w '+worker_str+' --job_name="worker" --task_index='+str(i)	
	cmds.append(command)
	print command
result_queue = Queue.Queue()
print "------------------------------------------------------------"

# define the commands to be run in parallel, run them
for cmd in cmds:
    thread = Thread(cmd, result_queue)
    thread.start()
    os.system('sleep 1')

# print results as we get them
while threading.active_count() > 1 or not result_queue.empty():
    while not result_queue.empty():
        (cmd, output, status) = result_queue.get()
        print "%s:" %cmd
        print output
        print '='*60
    time.sleep(1)
