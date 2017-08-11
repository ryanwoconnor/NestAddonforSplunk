import splunk.clilib.cli_common
import sys
import splunk.rest
import logging

session_key = sys.stdin.readline().strip()

def get_access_token(stanza_name):
    for key, val in stanza_name[1].iteritems():
        token = val
        if len(token) == 146:
            return token
        else:
            logging.error("ERROR key is invalid in stanza" + str(val))
            return False

def encrypt_tokens():

    try:
        nest_tokens_conf = splunk.clilib.cli_common.getMergedConf('nest_tokens')
    except Exception, e:
        logging.info("No nest_tokens_conf found -- bypassing.")

    for stanza in nest_tokens_conf.iteritems():
        if stanza[0] != 'default':
            if get_access_token(stanza):
                token = str(get_access_token(stanza))
                try:
                    post_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords?output_mode=json'
                    creds = {"name": stanza[0], "password": token, "realm": stanza}
                    splunk.rest.simpleRequest(post_path, sessionKey=session_key, postargs=creds, method='POST',
                                                                              raiseAllErrors=True)
                except Exception, e:
                    raise Exception("Could not post credentials: %s" % (str(e)))

            else:
                sys.stderr.write("No Token Found for Nest Devices \n")

encrypt_tokens()
