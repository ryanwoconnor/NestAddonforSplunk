import splunk


class Send(splunk.rest.BaseRestHandler):

	def handle_POST(self):
		sessionKey = self.sessionKey
		stanza_name = ''
		key = ''

		try:
			payload = str(self.request['payload'])
			self.response.write(payload)
			
			for el in payload.split('&'):
				key, value = el.split('=')
				if 'stanza_name' in key:
					stanza_name = value
				if 'key' in key:
					key = str(value)
				if stanza_name is '':
					self.response.setStatus(400)
					self.response.write('A stanza name  must be provided.')
				else:
					post_path = '/servicesNS/nobody/NestAddonforSplunk/configs/conf-nest_tokens/' + stanza_name
					new_key = {'key': key }
					serverContent = splunk.rest.simpleRequest(post_path,sessionKey=sessionKey,postargs=new_key,method='POST',raiseAllErrors=True)

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
