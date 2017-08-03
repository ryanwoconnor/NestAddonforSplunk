import splunk
import splunk.admin as admin
import splunk.rest
import json
import sys


class NestApp(admin.MConfigHandler):

    def logger(message):
        sys.stderr.write(message.strip() + "\n")

    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['keys', 'method']:
                self.supportedArgs.addOptArg(arg)


    def handleList(self, confInfo):

        my_app = "NestAddonforSplunk"

        try:

            sessionKey = self.getSessionKey()
            get_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords?output_mode=json'
            serverResponse = splunk.rest.simpleRequest(get_path, sessionKey=sessionKey, method='GET',
                                                           raiseAllErrors=True)
            jsonObj = json.loads(serverResponse[1])

            i = 0

            for realm_key, realm_value in jsonObj.iteritems():
                if realm_key == "entry":
                    while i < len(realm_value):
                        for entry_key, entry_val in realm_value[i].iteritems():
                            if entry_key == "content":
                                app_context = realm_value[i]["acl"]["app"]
                                sys.stderr.write("APP???: " + str(app_context) + "\n")
                                realm = entry_val['realm']
                                if app_context == my_app:
                                    for k, v in entry_val.iteritems():
                                        if k != "clear_password":
                                            confInfo[realm].append(k, v)
                                i += 1

        except Exception, e:
            raise Exception("Could not GET credentials: %s" % (str(e)))

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs

        sys.stderr.write("POSTed DATA: " + str(args) + "\n")

        method_obj = json.loads(args['method'][0])
        keys = json.loads(args['keys'][0])
        entity_name = keys['apiKeyName']
        method = method_obj['type']

        if method == 'post':

            entity_value = keys['apiKeyValue']

            sys.stderr.write("POSTED args: " +  str(args))

            sys.stderr.write("keys: " + str(keys) + "\n")
            sys.stderr.write("method: " + str(method) + "\n")
            sys.stderr.write("key name: " + str(entity_name) + "\n")
            sys.stderr.write("value name: " + str(entity_value) + "\n")

            try:
                sessionKey = self.getSessionKey()
                post_path = '/servicesNS/nobody/NestAddonforSplunk/storage/passwords?output_mode=json'
                creds = {"name": entity_name, "password": entity_value, "realm": entity_name}
                serverResponse, serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, postargs=creds, method='POST',
                                                          raiseAllErrors=True)

                sys.stderr.write('serverResponse: ' +  str(serverResponse) + "\n")
                sys.stderr.write('serverContent: ' + str(serverContent))


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


# initialize the handler
admin.init(NestApp, admin.CONTEXT_NONE)
