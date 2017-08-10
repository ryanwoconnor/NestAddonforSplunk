from multiprocessing import Process
from signal import signal, SIGTERM
from time import sleep
import atexit
import requests
import os
import time
import splunk.clilib.cli_common
import json
import sys
import splunk.rest
import re
import logging
import logging.handlers

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


#def logger(message):
    #sys.stderr.write(message.strip() + "\n")


def setup_logger(level):
    logger = logging.getLogger('my_search_command')
    logger.propagate = False  # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        os.environ['SPLUNK_HOME'] + '/var/log/splunk/nest.log', maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

logger = setup_logger(logging.INFO)

def check_splunk(process_id, procs):
    # initialize variables
    splunk_running = True
    devices_running = True

    # keep checking that splunkd and child procs are still alive
    while splunk_running and devices_running:
        # check that the splunk process is alive
        try:
            os.kill(int(process_id), 0)
        # If it's not alive, notify and drop out of the loop
        except OSError:
            logger.error("ERROR detected splunk not running")
            splunk_running = False
            continue
        for p in procs:
            # If any of the child processes isn't running, notify and drop out of the loop
            if not p.is_alive():
                logger.error("ERROR detected child process for devices no longer running")
                devices_running = False
        # If the processes are all running, go back to sleep
        time.sleep(1)
    return True


def get_devices(access_token):
    logger.debug("Beginning REST Call")
    headers = {"Authorization": "bearer ", "Accept": "text/event-stream"}
    sys.stdout = Unbuffered(sys.stdout)
    response_stream = requests.get("https://developer-api.nest.com/?auth=" + access_token, headers=headers, stream=True,
                                   timeout=3600)
    for line in response_stream.iter_lines(3, decode_unicode=None):
        if line == 'event: put':
            continue
        if line == 'event: keep-alive':
            continue
        if line == 'data: null':
            continue
        if "blocked" in line:
            sleep(60)
        logger.debug("Cleaning String..." + "\n")
        output_str = line.replace('data: {"path"', '{"path"')
        cleaned_str = re.sub(r'access_token\":\"([a-z]?.[\w+].[^\",]*)', 'access_token" : "<encrypted>', output_str)
        logger.debug("Done Cleaning String")
        logger.debug("Outputting String")
        sys.stdout.write(cleaned_str)
        sys.stdout.flush()
        logger.debug(output_str)
        logger.debug("Done outputting string")
    return True


def enforce_retention(sessionKey):
    # ensure the Nest Index Retention is only 10 days
    if len(sessionKey) == 0:
        logger.error("ERROR Did not receive a session key. Please enable passAuth in inputs.conf for this script")
        exit(2)

    try:
        nest_input = splunk.rest.simpleRequest('/services/data/inputs/script/.%252Fbin%252Fdevices.py?output_mode=json',
                                               method='GET', sessionKey=sessionKey, raiseAllErrors=True)

        nest_input_json = json.loads(nest_input[1])
        nest_index_name = nest_input_json['entry'][0]['content']['index']

        try:
            nest_index = splunk.rest.simpleRequest('/services/data/indexes/' + nest_index_name + '?output_mode=json',
                                                   method='GET', sessionKey=sessionKey, raiseAllErrors=True)

            nest_json = json.loads(nest_index[1])
            nest_frozen_time = nest_json['entry'][0]['content']['frozenTimePeriodInSecs']
            index_edit_list = nest_json['entry'][0]['links']['edit']

            postArgs = {"frozenTimePeriodInSecs": 864000}
            if nest_frozen_time > 864000:
                logger.warn("INFO nest index retention is too high, adjusting down to 10 days")
                splunk.rest.simpleRequest(index_edit_list, method='POST', sessionKey=sessionKey, raiseAllErrors=True,
                                          postargs=postArgs)

        except Exception:
            logger.error("INFO " + nest_index_name + " index doesn't exist")

    except Exception:
        logger.error("INFO Nest devices.py input doesn't exist")


    return True


def get_access_token(token):
    if len(token) == 146:
        # when the token is access_code, just return this value as-is
        return token
    else:
        logger.error("ERROR token is invalid" + token)
        return False


# set initial veriables
sys.stdout = Unbuffered(sys.stdout)
sys.stdout.flush()
splunk_home = os.path.expandvars("$SPLUNK_HOME")
logger.info("Splunk Home is:" + splunk_home)
splunk_pid = open(os.path.join(splunk_home, "var", "run", "splunk", "conf-mutator.pid"), 'rb').read()

logger.info("Splunk PID is:" + splunk_pid)
sessionKey = sys.stdin.readline().strip()
logger.info("variables initialized: splunk_home=" + splunk_home + " splunk_pid=" + splunk_pid)
# enforce the required retention policy
enforce_retention(sessionKey)

# start the real work
# Read in all Access Tokens from nope.conf

proc = []
keys_dict = {}

try:
    get_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords?output_mode=json'
    serverResponse = splunk.rest.simpleRequest(get_path, sessionKey=sessionKey, method='GET',
                                               raiseAllErrors=True)

    jsonObj = json.loads(serverResponse[1])

    my_app = "NestAddonforSplunk"

    if len(jsonObj['entry']) == 0:
        logger.warn("No credentials found.")
    else:
        for entry in jsonObj['entry']:
            if entry['acl']['app'] != my_app:
                continue
            logger.info('Found a stanza for the Nest Add-on')
            if 'clear_password' in entry['content'] and 'username' in entry['content']:
                keys_dict[entry['content']['username']] = entry['content']['clear_password']


except Exception, e:
    raise Exception("Could not GET credentials: %s" % (str(e)))

for apiKeyName, apiKeyVal in keys_dict.iteritems():
    logger.info("Getting Nest API Keys...!")
    if get_access_token(apiKeyVal):
        token = str(get_access_token(apiKeyVal))
        logger.info("Found Nest token!")
        # Create a new process for each nest key (access_token)
        devices = Process(target=get_devices, args=(token,))
        devices.start()
        proc.append(devices)
    else:
        logger.error("No Token Found for Nest Devices")

def clean_children(proc):
    for p in proc:
        p.terminate()

atexit.register(clean_children, proc)

# Create a Process to Check if Splunk is running and kill all child processes if Splunk dies or Splunk PID Changes
if check_splunk(splunk_pid, proc):
    clean_children(proc)

for sig in (SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, clean_children(proc))

sys.exit()
