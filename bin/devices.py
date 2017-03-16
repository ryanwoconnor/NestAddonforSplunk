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
    headers = {"Authorization": "bearer ", "Accept": "text/event-stream"}
    response = requests.get("https://developer-api.nest.com/?auth=" + access_token, headers=headers, stream=True, timeout=3600)
    for line in response.iter_lines():
        if line == 'event: put':
            continue
        if line == 'event: keep-alive':
            continue
        if line == 'data: null':
            continue
        output_str = line.replace('data: {"path"','{"path"')
        sys.stdout.write(output_str)
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

def get_access_token(stanza_name):
    for key in stanza_name[1].iteritems():
        token = key[1]
        if len(token) == 146:
            #token is access_code
            return token
        elif len(token) == 8:
            #token is pincode
            endpoint = 'https://api.home.nest.com/oauth2/access_token'
            client_id = 'f4151b70-db18-43ac-a12b-1fbcd5f1cba9'
            client_secret = 'mdM3hEligo2PfGBsOMsaHFdvI'

            params = {}
            params['client_id'] = client_id
            params['code'] = token
            params['client_secret'] = client_secret
            params['grant_type'] = 'authorization_code'

            p = urllib.urlencode(params)
            f = urllib.urlopen(endpoint, p)
            codes = json.loads(f.read())

            nest_access_token = codes['access_token']
            #update "key" in the appropriate stanza and write to config files - maybe using restapi
            return nest_access_token
        else:
            logger("ERROR key is invalid in stanza" + stanza)
            return False
            

#set initial veriables
sys.stdout = Unbuffered(sys.stdout)
splunk_home = os.path.expandvars("$SPLUNK_HOME")
splunk_pid = open(os.path.join(splunk_home,"var","run", "splunk", "conf-mutator.pid"), 'rb').read()
sessionKey = sys.stdin.readline().strip()
logger("variables initialized: splunk_home="+splunk_home+" splunk_pid="+splunk_pid)

#enforce the required retention policy
enforce_retention(sessionKey)

#start the real work
#Read in all Access Tokens from nest_tokens.conf

proc = []
settings = splunk.clilib.cli_common.getMergedConf("nest_tokens")
for item in settings.iteritems():
    token = get_access_token(item)
    #Create a new process for each nest key (access_token)
    devices = Process(target=get_devices, args=(token,))
    devices.start()
    proc.append(devices)

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
