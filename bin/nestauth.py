import splunk.admin as admin
import splunk.entity as en
import urllib, json

class ConfigApp(admin.MConfigHandler):
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['code', 'nest_client_id']:
                self.supportedArgs.addOptArg(arg)

    def handleList(self, confInfo):
        inputDict = self.readConf("inputs")
        if None != confDict:
            for stanza, settings in confDict.items():
                for key, val in settings.items():
                    if key in ['nest_client_id'] and val in [None, '']:
                        val = ''
                    if key in ['nest_client_secret'] and val in [None, '']:
                        val = ''
                    if key in ['nest_access_token'] and val in [None, '']:
                        val = ''
                    confInfo[stanza].append(key, val)

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs

        client_id = setting['nest_client_id']
        client_secret = setting['nest_client_secret']
        access_token = setting['nest_access_token']

        endpoint = 'https://api.home.nest.com/oauth2/access_token'

        code = self.callerArgs.data['code'][0]

        params = {}
        params['client_id'] = client_id
        params['code'] = code
        params['client_secretclient_secret'] = 'STATE'
        params['grant_type'] = 'authorization_code'

        p = urllib.urlencode(params)
        f = urllib.urlopen(endpoint, p)
        codes = json.loads(f.read())

        output = { 'nest_access_token': [], 'nest_refresh_token': [] }

        output['nest_access_token'].append(codes['access_token'])

        self.writeConf('inputs', stanza, output)

        en.getEntities('data/inputs/nest/_reload', sessionKey = self.getSessionKey(), namespace='NestAddonforSplunk', owner='nobody')

admin.init(ConfigApp, admin.CONTEXT_NONE)
