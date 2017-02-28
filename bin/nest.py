import requests
import os
import time
import splunk.clilib.cli_common
import json
import sys
import platform
import splunk.rest
import logging

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

def do_scheme():
    print SCHEME

def get_config():
    config = {}
    try:
        # read everything from stdin
        config_str = sys.stdin.read()
        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            logging.debug("XML: found configuration")
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    logging.debug("XML: found stanza " + stanza_name)
                    config["name"] = stanza_name
                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        logging.debug("XML: found param '%s'" % param_name)
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            logging.debug("XML: '%s' -> '%s'" % (param_name, data))
        sessn_key = root.getElementsByTagName("session_key")[0]
        if sessn_key and sessn_key.firstChild and \
           sessn_key.firstChild.nodeType == sessn_key.firstChild.TEXT_NODE:
            config["session_key"] = sessn_key.firstChild.data
        if not config:
            raise Exception, "Invalid configuration received from Splunk."
    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)
    return config

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
       logging.error("Did not receive a session key. Please enable passAuth in inputs.conf for this script")
       exit(2)
    
    try:
        nest_input = splunk.rest.simpleRequest('/services/data/inputs/script/.%252Fbin%252Fdevices.py?output_mode=json', method='GET', sessionKey=sessionKey, raiseAllErrors=True)
    except Exception:
        logging.info("Nest devices.py input doesn't exist")

    nest_input_json = json.loads(nest_input[1])
    nest_index_name = nest_input_json['entry'][0]['content']['index']
    
    #index will be passed in from stdin: <input><configuration><stanza name="nest://<name>"><param name="index">index</param>
    #sourcetype will probably be passed in from stdin: <input><configuration><stanza name="nest://<name>"><param name="sourcetype">sourcetype</param>
    
    try:
        nest_index = splunk.rest.simpleRequest('/services/data/indexes/' + nest_index_name  + '?output_mode=json', method='GET', sessionKey=sessionKey, raiseAllErrors=True)
    except Exception:
        logging.info(nest_index_name + " index doesn't exist")
    
    nest_json = json.loads(nest_index[1])
    nest_frozen_time = nest_json['entry'][0]['content']['frozenTimePeriodInSecs']
    index_edit_list = nest_json['entry'][0]['links']['edit']
    
    postArgs = {"frozenTimePeriodInSecs": 864000}
    if nest_frozen_time > 864000:
        logging.info("nest index retention is too high, adjusting down to 10 days")
        splunk.rest.simpleRequest(index_edit_list, method='POST', sessionKey=sessionKey, raiseAllErrors=True, postargs=postArgs)
    
    return True

# set up logging suitable for splunkd consumption
logging.root
logging.root.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s %(message)s')
handler = logging.StreamHandler(stream=sys.stderr)
handler.setFormatter(formatter)
logging.root.addHandler(handler)

#set initial veriables
sys.stdout = Unbuffered(sys.stdout)
splunk_home = os.path.expandvars("$SPLUNK_HOME")
splunk_pid = open(os.path.join(splunk_home,"var","run", "splunk", "conf-mutator.pid"), 'rb').read()

SCHEME = """<scheme>
    <title>Nest</title>
    <description>Get data from Nest Learning Thermostat and/or Nest Protect.</description>
    <streaming_mode>simple</streaming_mode>

    <endpoint>
        <args>
            <arg name="name">
                <title>Resource name</title>
                <description>The Nest resource name without the leading nest://.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="nest_access_token">
                <title>Nest Access Token</title>
                <description>The Nest access token - this is usually filled in automatically</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="nest_client_id">
                <title>Nest client_id</title>
                <description>This is usually filled in automatically, unless you need to override it</description>
                <required_on_edit>true</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="nest_client_secret">
                <title>Nest client_secret</title>
                <description>This is usually filled in automatically, unless you need to override it</description>
                <required_on_edit>true</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
            <arg name="nest_code">
                <title>Nest code</title>
                <description><![CDATA[Your Nest code. Get the Nest code from here: <a href="https://home.nest.com/login/oauth2?client_id=clientIDstate=STATE">https://home.nest.com/login/oauth2?client_id=clientId&state=STATE</a>]]></description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>
        </args>
    </endpoint>
</scheme>
"""

logging.info("variables initialized")

#process arguments
if len(sys.argv) > 1:
    if sys.argv[1] == "--scheme":
        do_scheme()
        sys.exit(0)
else:
    config = get_config()
    sessionKey = config["session_key"]
    #start the real work
    #enforce the required retention policy
    enforce_retention(sessionKey)
    #Read in all Access Tokens from nest_tokens.conf
    settings = splunk.clilib.cli_common.getMergedConf("nest_tokens")
    for item in settings.iteritems():
        for nest_access_token in item[1].iteritems():
            token = nest_access_token[1]
            devices = get_devices(token)

sys.exit()
