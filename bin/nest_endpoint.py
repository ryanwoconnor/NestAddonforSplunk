import splunk
import splunk.bundle as bundle
import splunk.admin as admin
import json


class NestApp(admin.MConfigHandler):

    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['keys']:
                self.supportedArgs.addOptArg(arg)


    def handleList(self, confInfo):
        confDict = self.readConf("nest_tokens")

        if None != confDict:
            for key, val in confDict['api_keys'].items():
                confInfo['keys'].append(key, val)


    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs

        keys = json.loads(args['keys'][0])
        if len(keys) == 0:
            self.writeConf('nest_tokens', 'api_keys', {'keys': '{}'})
        else:
            self.writeConf('nest_tokens', 'api_keys', {'keys': json.dumps(keys)})

# initialize the handler
admin.init(NestApp, admin.CONTEXT_NONE)
