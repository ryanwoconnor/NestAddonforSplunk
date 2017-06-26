import splunk
class Send(splunk.rest.BaseRestHandler):

	def handle_POST(self):
		sessionKey = self.sessionKey
		name = ''
		apikey = ''
		args = {}
		try:
			payload = str(self.request['payload'])
			#self.response.write(payload)


			for el in payload.split('&'):
		    		key, value = el.split('=')
		        	if 'name' in key:
                			name = str(value)
        			if 'key' in key:
                			apikey = str(value)
        			else:
                			if name is '' or apikey is '':
						break;
                			args={'name':name,'key':apikey}
					post_path = '/servicesNS/nobody/NestAddonforSplunk/configs/conf-nest_tokens'
					serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, postargs=args, method='POST', raiseAllErrors=True)

		except Exception, e:
			self.response.write(e)

	handle_GET = handle_POST

class Receive(splunk.rest.BaseRestHandler):
	def handle_GET(self):
      		sessionKey = self.sessionKey
        	try:
            		get_path = '/servicesNS/admin/NestAddonforSplunk/configs/conf-nest_tokens?output_mode=json'
			serverResponse, serverContent = splunk.rest.simpleRequest(get_path, sessionKey=sessionKey, method='GET', raiseAllErrors=True)
    			self.response.write(serverContent)
        	except Exception, e:
            		self.response.write(e)
