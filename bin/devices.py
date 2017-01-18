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
import platform
import subprocess

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)
def check_splunk(process_id,self_pid,procs):
		#Assume Splunk is running
        splunk_running = True
        #Assume devices.py is running
        devices_running = True
        
        #Output message regarding this check
        sys.stderr.write("entering check_splunk")
        
        #While splunk is supposedly running and devices is running, do some stuff
        while splunk_running and devices_running:
        
        #Try to kill the splunk pid to see if it's still alive
		try:
			os.kill(int(process_id), 0)
		#If it's not, notify us and change splunk to not running
		except OSError:
			sys.stderr.write("error: detected splunk not running")
			splunk_running = False
			continue
		#If Splunk isn't running, do some more checks
		else:
			#Assume Splunk is running again
			splunk_running = True
				#For all of the processes in the subprocess list
                for p in procs:
                		#If each process isn't running, detect it's not running and set variable
                        if not p.is_alive():
                            sys.stderr.write("error: detected devices spawn no longer running")
                            devices_running = False
                #If the process is running, go back to sleep
                time.sleep(1)
        #If Splunk isn't running
        if splunk_running is False:
            try:
            	#try to kill some processes
                for p in procs:
                    p.terminate()
            #If can't kill it, assume it's terminated
            except IOError: # proc has already terminated
                pass
        return True
def get_devices(access_token):
    headers = {"Authorization": "bearer ", "Accept": "text/event-stream"}
    response = requests.get("https://developer-api.nest.com/?auth=" + access_token, headers=headers, stream=True, timeout=3600)
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
    return True

#Set stdout to Unbuffered Version
sys.stdout = Unbuffered(sys.stdout)

#Get Splunk Home
splunk_home = os.path.expandvars("$SPLUNK_HOME")
#Create Variable to Track Splunk Pid
splunk_pid = ""

#Create Variable to Track Current Python Script Pid
current_pid = ""
current_pid = os.getpid()

#Get OS
OS = platform.platform()

#True/False statements for various nest stanza settings
nest_index_time_too_high = False
nest_index_time_found = False
nest_index_found = False
nest_index_frozen_setting = 0


#Nest Stanza variable
nest_stanza = '[nest]'

#We need to ensure the Nest Index Retention is only 10 days. This entire section ensures there is a config file that sets the retention time to 10days when Splunk starts.
#We will start out by checking for a nest stanza.
#We will also attempt to build any current nest stanza into the variable nest_stanza in case we simply need to replace the frozentimeperiodinsecs attribute
settings = splunk.clilib.cli_common.readConfFile(splunk_home+"/etc/system/local/indexes.conf")
for item in settings.iteritems():
        #Check if there is a nest stanza in the system local config file
        if item[0]=='nest':
                nest_index_found = True
                for key in item[1].iteritems():
                        nest_stanza+='\n'
                        nest_stanza=nest_stanza+key[0]+'='+key[1]
                        if key[0]=='frozenTimePeriodInSecs':
                                #Check if the frozenTimePeriodInSecs is set correctly or not
                                if int(key[1])>864000:
                                        print 'Setting is too high'
                                        nest_index_time_too_high = True
                                        nest_index_time_found = True
                                        nest_index_frozen_setting = key[1]
                                if int(key[1])==864000:
                                        print 'Setting is Good'
                                        nest_index_time_found = True

#if frozenTimePeriodInSecs found and too high
if nest_index_found and nest_index_time_found and nest_index_time_too_high:
        # Read in the local indeexes file
        f = open(splunk_home+'/etc/system/local/indexes.conf', 'r')
        filedata = f.read()
        f.close()

        # Replace the target string
        newdata = filedata.replace(str(nest_index_frozen_setting), '864000')

        # Write the file out again
        f = open(splunk_home+'/etc/system/local/indexes.conf', 'w')
        f.write(newdata)
        f.close()

#if frozenTimePeriodInSecs not found but the nest stanza was found
if nest_index_found and nest_index_time_found==False:
        # Read in the local indexes file
        f = open(splunk_home+'/etc/system/local/indexes.conf', 'r')
        filedata = f.read()
        f.close()

        # Replace the target string
        newdata = filedata.replace('[nest]', '[nest]\nfrozenTimePeriodInSecs = 864000')

        # Write the file out again
        f = open(splunk_home+'/etc/system/local/indexes.conf', 'w')
        f.write(newdata)
        f.close()

#if nest stanza wasn't found in system local
if nest_index_found==False:
        file = open(splunk_home+'/etc/system/local/indexes.conf', 'a')
        file.write('[nest]')
        file.write('\n')
        file.write('homePath = $SPLUNK_DB/nestdb/db\n')
        file.write('coldPath = $SPLUNK_DB/nestdb/db\n')
        file.write('thawedPath = $SPLUNK_DB/nestdb/db\n')
        file.write('frozenTimePeriodInSecs = 864000\n')
        file.write('maxTotalDataSizeMB = 512000')


#What to do for Macs
if "Darwin" in OS:
	processes = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines() 
	for process in processes:
		try:
			if 'splunkd' in process:
				proc_info = process.split(' ')
				pid = proc_info[6]
				splunk_pid = pid
				break
			else:
					splunk_pid = "SPLUNK NOT RUNNING"
		except IOError: # proc has already terminated
		   continue

	if "SPLUNK NOT" in splunk_pid:
			sys.exit()
#What to do for anything else
else:
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
settings = splunk.clilib.cli_common.readConfFile(splunk_home+"/etc/apps/NestAddonforSplunk/local/nest_tokens.conf")
for item in settings.iteritems():
        for key in item[1].iteritems():
		token = key[1]
		#Create a new process for each access_token
		devices = Process(target=get_devices, args=(token,))
		devices.start()
		proc.append(devices)
#Create a Process to Check if Splunk is running and kill all child processes if Splunk dies or Splunk PID Changes
if check_splunk(splunk_pid,current_pid,proc):
	for p in proc:
		p.terminate()
#If All Subprocesses Die, Kill Python Script
sys.exit()
