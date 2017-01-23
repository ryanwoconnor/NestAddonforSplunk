import splunk.admin as admin
import splunk.entity as en
import urllib, json

class ConfigApp(admin.MConfigHandler):
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['code','oauth2_client_id']:
                self.supportedArgs.addOptArg(arg)

    def handleList(self, confInfo):
        inputDict = self.readConf("inputs")
        confInfo['default'].append('oauth2_client_id', inputDict['box://myboxinput']['oauth2_client_id'])
        confInfo['default'].append('code','')

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs

        inputDict = self.readConf("inputs")

        for stanza, setting in inputDict.items():
            if stanza == 'box://myboxinput':
                client_id = setting['oauth2_client_id']
                client_secret = setting['oauth2_client_secret']
                endpoint = setting['oauth2_refresh_url']

                code = self.callerArgs.data['code'][0]

                params = {}
                params['grant_type'] = 'authorization_code'
                params['code'] = code
                params['client_id'] = client_id
                params['client_secret'] = client_secret

                p = urllib.urlencode(params)
                f = urllib.urlopen(endpoint, p)
                codes = json.loads(f.read())

                output = { 'oauth2_access_token': [], 'oauth2_refresh_token': [] }

                output['oauth2_access_token'].append(codes['access_token'])
                output['oauth2_refresh_token'].append(codes['refresh_token'])

                self.writeConf('inputs', stanza, output )

                confInfo['default'].append('code', '' )

                en.getEntities('data/inputs/box/_reload', sessionKey = self.getSessionKey(), namespace='BoxAppForSplunk', owner='nobody')

admin.init(ConfigApp, admin.CONTEXT_NONE)
