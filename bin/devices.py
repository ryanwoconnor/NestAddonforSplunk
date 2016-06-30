from multiprocessing import Process
import requests
import requests.auth
import os
import time
import datetime
import splunk.clilib.cli_common
import json
import ast
import signal
import sys

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
def check_splunk(process_id,self_pid,devices):
        splunk_running = True
        while splunk_running:
		try:
			os.kill(int(process_id), 0)
		except OSError:
			splunk_running = False
			continue
		else:
			splunk_running = True
                time.sleep(1)
        if splunk_running is False:
        	pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
                for pid in pids:
                        try:
				cmd = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
				if 'devices' in cmd:
					#print "Found python running"
					os.kill(int(pid), signal.SIGTERM)
				#else:
					#print ""
#					os.kill(int(self_pid), signal.SIGTERM)
			except IOError: # proc has already terminated
                                continue
def get_devices(access_token):
    headers = {"Authorization": "bearer ", "Accept": "text/event-stream"}
    response = requests.get("https://developer-api.nest.com/?auth=" + access_token, headers=headers, stream=True)
    for line in response.iter_lines():
		#ts = time.time()
		#st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		if line == 'event: put':
			continue
		if line == 'event: keep-alive':
			continue
		if line == 'data: null':
			continue
		output_str = line.replace('data: {"path"','{"path"')
		#print(str(output_str))
		sys.stdout.write(output_str)
    return true

#Set stdout to Unbuffered Version
sys.stdout = Unbuffered(sys.stdout)

#Get Splunk Home
splunk_home = os.path.expandvars("$SPLUNK_HOME")
#Create Variable to Track Splunk Pid
splunk_pid = ""

#Create Variable to Track Current Python Script Pid
current_pid = ""
current_pid = os.getpid()

#Get All Current Pids
pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

#Check if Splunk is Running and Die if not
for pid in pids:
    cmd = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
    try:
        if 'splunkd' in cmd:
                splunk_pid = pid
                break
        else:
                splunk_pid = "SPLUNK NOT RUNNING"
    except IOError: # proc has already terminated
       continue

if "SPLUNK NOT" in splunk_pid:
        sys.exit()

#Read in all Access Tokens from Homeview.conf
proc = []
settings = splunk.clilib.cli_common.readConfFile(splunk_home+"/etc/apps/NestAppforSplunk/local/nest_tokens.conf")
for item in settings.iteritems():
        for key in item[1].iteritems():
		token = key[1]
		#Create a new process for each access_token
		devices = Process(target=get_devices, args=(token,))
		devices.start()
		proc.append(devices)
#Create a Process to Check if Splunk is running and kill all child processes if Splunk dies or Splunk PID Changes
splunk_checker = Process(target=check_splunk, args=(splunk_pid,current_pid,devices))
splunk_checker.start()
for p in proc:
	devices.join()
#If All Subprocesses Die, Kill Python Script
sys.exit()
