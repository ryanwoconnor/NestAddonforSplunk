import splunk
import splunk.admin as admin
import splunk.rest
import json
import sys
import re
import ast
from collections import namedtuple


class NestApp(admin.MConfigHandler):

    def logger(message):
        sys.stderr.write(message.strip() + "\n")

    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['keys', 'method']:
                self.supportedArgs.addOptArg(arg)


    def handleList(self, confInfo):

        try:

            sessionKey = self.getSessionKey()
            get_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords?output_mode=json'
            serverResponse = splunk.rest.simpleRequest(get_path, sessionKey=sessionKey, method='GET',
                                                           raiseAllErrors=True)

            jsonObj = json.loads(serverResponse[1])

            i = 0

            for realm_key, realm_value in jsonObj.iteritems():
                realm = ''
                clear_password = ''
                props_dict = {}
                if realm_key == "entry":
                    while i < len(realm_value):
                        for entry_key, entry_val in realm_value[i].iteritems():
                            if entry_key == "content":
                                realm = entry_val['realm']
                                for k, v in entry_val.iteritems():
                                    if k != "clear_password":
                                        confInfo[realm].append(k, v)
                                i += 1

        except Exception, e:
            raise Exception("Could not GET credentials: %s" % (str(e)))

        """
        confDict = self.readConf("passwords")

        stanzas = {}

        if None != confDict:
            for stanza in confDict:
                sys.stderr.write("_STANZA: " + str(stanza) + "\n")

                stanza = re.match(r'credential::*([^:]+)', str(stanza)).group(1)
                if stanza != 'keys':
                    confInfo['keys'].append(stanza, "")

            sys.stderr.write("_confInfo: " + str(confInfo['keys']) + "\n")
        """

        """
        if None != confDict:
            for key, val in confDict['api_keys'].items():
                confInfo['keys'].append(key, val)
        """


    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs

        sys.stderr.write("all args: " + str(args))

        method_obj = json.loads(args['method'][0])
        keys = json.loads(args['keys'][0])
        entity_name = keys['apiKeyName']
        method = method_obj['type']

        if method == 'post':

            entity_value = keys['apiKeyValue']

            sys.stderr.write("keys: " + str(keys) + "\n")
            sys.stderr.write("method: " + str(method) + "\n")
            sys.stderr.write("key name: " + str(entity_name) + "\n")
            sys.stderr.write("value name: " + str(entity_value) + "\n")

            try:
                sessionKey = self.getSessionKey()
                post_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords'
                creds = {"name": entity_name, "password": entity_value, "realm": entity_name}
                serverResponse, serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, postargs=creds, method='POST',
                                                          raiseAllErrors=True)
            except Exception, e:
                raise Exception("Could not post credentials: %s" % (str(e)))

        elif method == 'delete':

            entity_url_encode = entity_name.replace(" ", "%20")
            entity = entity_url_encode + ":" + entity_url_encode + ":"

            try:
                sessionKey = self.getSessionKey()
                post_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords/' + entity
                serverResponse, serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, method='DELETE',
                                                          raiseAllErrors=True)
            except Exception, e:
                raise Exception("Could not post credentials: %s" % (str(e)))

        """
        if len(keys) == 0:
            self.writeConf('nest_tokens', 'api_keys', {'keys': '{}'})
        else:
            self.writeConf('nest_tokens', 'api_keys', {'keys': json.dumps(keys)})
        
            try:
                sessionKey = self.getSessionKey()
                post_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords'
                creds = {"name" : last_key, "password" : json.dumps(last_value)}
                serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, postargs=creds, method='POST',
                                                      raiseAllErrors=True)
            except Exception, e:
                raise Exception("Could not post credentials: %s" % (str(e)))
        """


# initialize the handler
admin.init(NestApp, admin.CONTEXT_NONE)
