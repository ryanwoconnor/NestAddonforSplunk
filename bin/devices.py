from multiprocessing import Process
from signal import signal, SIGTERM
import atexit
import requests
import os
import time
import splunk.clilib.cli_common
import json
import sys
import platform
import subprocess
import splunk.rest
import urllib

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

def logger(message):
    sys.stderr.write(message.strip() + "\n")

def check_splunk(process_id,procs):
    #initialize variables
    splunk_running = True
    devices_running = True
    
    # keep checking that splunkd and child procs are still alive
    while splunk_running and devices_running:
        #check that the splunk process is alive
        try:
            os.kill(int(process_id), 0)
        #If it's not alive, notify and drop out of the loop
        except OSError:
            logger("ERROR detected splunk not running")
            splunk_running = False
            continue
        for p in procs:
            #If any of the child processes isn't running, notify and drop out of the loop
            if not p.is_alive():
                logger("ERROR detected child process for devices longer running")
                devices_running = False
        #If the processes are all running, go back to sleep
        time.sleep(1)
    return True

def get_devices(access_token):
	logger("trying to get data for " + access_token)
	headers = {"Authorization": "bearer ", "Accept": "text/event-stream"}
	response = requests.get("https://developer-api.nest.com/?auth=" + access_token, headers=headers, stream=True, timeout=3600)
    	for line in response.iter_lines():
		if line == 'event: put':
			continue
		if line == 'event: keep-alive':
			continue
		if line == 'data: null':
			continue
        	#output_str = line.replace('data: {"path"','{"path"')
		#output_str = line.replace('data: {"path"','{"path"')
		output_str = line.replace('data: {"path":"/",','{')
		logger(output_str)
		print(output_str)
	return True

def enforce_retention(sessionKey):
    #ensure the Nest Index Retention is only 10 days
    if len(sessionKey) == 0:
	logger("ERROR Did not receive a session key. Please enable passAuth in inputs.conf for this script")
	exit(2)
    
    try:
        nest_input = splunk.rest.simpleRequest('/services/data/inputs/script/.%252Fbin%252Fdevices.py?output_mode=json', method='GET', sessionKey=sessionKey, raiseAllErrors=True)
    except Exception:
        logger("INFO Nest devices.py input doesn't exist")

    nest_input_json = json.loads(nest_input[1])
    nest_index_name = nest_input_json['entry'][0]['content']['index']
    nest_sourcetype = nest_input_json['entry'][0]['content']['sourcetype']
    
    try:
        nest_index = splunk.rest.simpleRequest('/services/data/indexes/' + nest_index_name  + '?output_mode=json', method='GET', sessionKey=sessionKey, raiseAllErrors=True)
    except Exception:
        logger("INFO " + nest_index_name + " index doesn't exist")
    
    nest_json = json.loads(nest_index[1])
    nest_frozen_time = nest_json['entry'][0]['content']['frozenTimePeriodInSecs']
    index_edit_list = nest_json['entry'][0]['links']['edit']
    
    postArgs = {"frozenTimePeriodInSecs": 864000}
    if nest_frozen_time > 864000:
        logger("INFO nest index retention is too high, adjusting down to 10 days")
        splunk.rest.simpleRequest(index_edit_list, method='POST', sessionKey=sessionKey, raiseAllErrors=True, postargs=postArgs)
    
    return True

def get_access_token(token):
    if len(token) == 146:
        #when the token is access_code, just return this value as-is
        sys.stderr.write("Successfully found token \n")
        return token
    else:
        sys.stderr.write("ERROR token is invalid" + token)
        return False

#set initial veriables
sys.stdout = Unbuffered(sys.stdout)
splunk_home = os.path.expandvars("$SPLUNK_HOME")
print(splunk_home)
splunk_pid = open(os.path.join(splunk_home,"var","run", "splunk", "conf-mutator.pid"), 'rb').read()
print(splunk_pid)
sessionKey = sys.stdin.readline().strip()
logger("variables initialized: splunk_home="+splunk_home+" splunk_pid="+splunk_pid)
#enforce the required retention policy
enforce_retention(sessionKey)

#start the real work
#Read in all Access Tokens from nest_tokens.conf

proc = []
settings = splunk.clilib.cli_common.getMergedConf('nest_tokens')
keys_str = settings['api_keys']['keys']
keys = json.loads(keys_str)

for apiKeyName, apiKeyVal in keys.iteritems():
    token = str(get_access_token(apiKeyVal))
    if token:
        sys.stderr.write("found token: :" + token + "\n")
        #Create a new process for each nest key (access_token)
        devices = Process(target=get_devices, args=(token,))
        devices.start()
        proc.append(devices)
    else:
        sys.stderr.write("No Token Found for Nest Devices \n")

def clean_children(proc):
    for p in proc:
        p.terminate()

atexit.register(clean_children, proc)

#Create a Process to Check if Splunk is running and kill all child processes if Splunk dies or Splunk PID Changes
if check_splunk(splunk_pid,proc):
    clean_children(proc)

for sig in (SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, clean_children(proc))

sys.exit()
