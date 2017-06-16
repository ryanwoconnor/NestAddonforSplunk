Nest Add-on for Splunk Documentation
====================
System Requirements: This app is tested and working on Ubuntu and OSX 10.11. 

Installation:
---------------------
Installation for this add-on is fairly straight forward and you can be up and running in a matter of minutes. 

If you need assistance with the app you can use the following instructions or reach out on Splunk Answers. 


### Obtaining an Authorization Code for your Nest Account:

Simply use the following instructions to get started collecting your data in Splunk. 

1. Visit the following URL: https://home.nest.com/login/oauth2?client_id=f4151b70-db18-43ac-a12b-1fbcd5f1cba9&state=STATE
2. Click accept to allow this app to query your device. 
3. After authorizing this app, you will be granted an APIKey in a JSON Format like the following: {"api_key":"**<api_key>**"}. The <api_key> section in quotes is what you want to copy. 
4. Copy the api_key provided to you into a new stanza in nest_tokens.conf in the $SPLUNK_HOME/etc/apps/NestAddonforSplunk/local directory. (See the sample format in $SPLUNK_HOME/etc/apps/NestAddonforSplunk/default/nest_tokens.conf)
5. Restart Splunk. 
6. Data may take sometime to start populating. It depends on how often you are interacting with your Nest Devices and/or App. 


Configuration:
---------------------

This app should just work and start indexing your data once it's configured. It's main purpose is to get your data into Splunk in a fast and efficient manner. To visualize your data please also install (https://splunkbase.splunk.com/app/3219/)


Deauthorizing an access token
---------------------
If you no longer want the access_token you've created to be able to access your Nest Account, you can follow the instructions here. 

https://developers.nest.com/documentation/cloud/deauthorization-overview


Troubleshooting:
---------------------

1. The following command will allow you to check if the scripted input is running. You may see multiple instances of the python script as there are child processes that run to collect the data and ensure the command exists cleanly when Splunk is shutdown or restarted.
    
    
    ```
    ps -ef | grep devices
    ```


2. Ensure you have your $SPLUNK_HOME variable set. More information on this can be found here: https://wiki.archlinux.org/index.php/Splunk

3. Verify your nest_tokens.conf file is in the directory $SPLUNK_HOME/etc/apps/NestAddonforSplunk/local and follows the format for each Nest Account:

    
    ```
    [stanza_name]
    ```
    ```
    key = api_key
    ```
    

Disclaimer: 
---------------------

Though this Add-on does use REST Streaming Requests to access data from Nest and store it in Splunk, it is not intended to provide real-time alerts regarding the status of your Nest Protect. You should utilize the official [Nest App](https://nest.com/app/) in order to recieve alerts.
