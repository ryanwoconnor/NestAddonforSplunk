import requests
import os
import time
import splunk.clilib.cli_common
import json
import sys
import platform
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

def do_scheme():
    print SCHEME

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

#set initial veriables
sys.stdout = Unbuffered(sys.stdout)
splunk_home = os.path.expandvars("$SPLUNK_HOME")
splunk_pid = open(os.path.join(splunk_home,"var","run", "splunk", "conf-mutator.pid"), 'rb').read()
sessionKey = sys.stdin.readline().strip()
logger("variables initialized")

SCHEME = """<scheme>
    <title>Nest</title>
    <description>Get data from Nest Learning Thermostat and/or Nest Protect.</description>
    <streaming_mode>simple</streaming_mode>

    <endpoint>
        <args>
            <arg name="name">
                <title>Resource name</title>
                <description>The Nest resource name without the leading nest://.</description>
            </arg>

            <arg name="access_token">
                <title>Next access_token</title>
                <description>Your Nest access_token. See README.md for details</description>
                <validation>validate(match('access_tokeni','^c\.\w{144}$'), "Ensure access_token is correct")</validation>
            </arg>
        </args>
    </endpoint>
</scheme>
"""


#process arguments
if len(sys.argv) > 1:
    if sys.argv[1] == "--scheme":
        do_scheme()
        sys.exit(0)
else:
    #start the real work
    #enforce the required retention policy
    enforce_retention(sessionKey)
    #Read in all Access Tokens from nest_tokens.conf
    settings = splunk.clilib.cli_common.getMergedConf("nest_tokens")
    for item in settings.iteritems():
        for access_token in item[1].iteritems():
            token = access_token[1]
            devices = get_devices(token)

sys.exit()
