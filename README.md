Nest Add-on for Splunk Documentation
====================
System Requirements: This app is tested and working on Ubuntu and OSX 10.11. 

Installation:
---------------------
Installation for this add-on is fairly straight forward and you can be up and running in a matter of minutes. Start out by obtaining an access_token. 

If you need assistance in obtaining an access_token you can use the following instructions or reach out on Splunk Answers. 


### Obtaining a PIN for your Nest Account:

Simply use the following instructions to get started collecting your data in Splunk. 

1. Visit the following URL: https://home.nest.com/login/oauth2?client_id=f4151b70-db18-43ac-a12b-1fbcd5f1cba9&state=STATE
2. Click accept to allow this app to query your device. 
3. Copy the Authorization Code Provided to you by the Nest Website into a new stanza in nest_tokens.conf in the local directory. (See the sample format in default/nest_tokens.conf)
4. Restart Splunk. 
5. Once Splunk restarts it will automatically replace the PIN you entered in nest_tokens.conf with an API Key. 


Configuration:
---------------------

This app should just work and start indexing your data once it's configured. It's main purpose is to get your data into Splunk in a fast and efficient manner. To visualize your data please also install (https://splunkbase.splunk.com/app/3219/)


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
