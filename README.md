Nest Add-on for Splunk Documentation
====================
System Requirements: This app is tested and working on Ubuntu and OSX 10.11. 

The main purpose for this Add-on is to get your data into Splunk in a fast and efficient manner. To visualize your data please also install (https://splunkbase.splunk.com/app/3219/)

Installation:
---------------------
To install this add-on, you can can navigate to “Manage Apps” in your Splunk installation and then “Browse More Apps”. From there you can find the Nest Add-on for Splunk and install it. 

Distributed Environment requirements: In a distributed environment, this Add-on is only needed on your Indexing tier. 


Configuration:
---------------------

From your Splunk installation:

1. Go to Manage Apps
2. Find the the "Setup" link for the Nest Add-on for Splunk. 
3. There you will be provided with a Graphical User Interface for configuring the Add-on. 



Deauthorizing an access token
---------------------
If you no longer want the access_token you've created to be able to access your Nest Account, you can follow the instructions here. 

https://developers.nest.com/documentation/cloud/deauthorization-overview


Troubleshooting:
---------------------

1. The following command will allow you to check if the scripted input is running. You may see multiple instances of the python script as there are child processes that run to collect the data and ensure the command exits cleanly when Splunk is shutdown or restarted.
    
    
    ```
    ps -ef | grep devices
    ```


2. Ensure you have your $SPLUNK_HOME variable set. More information on this can be found here: https://wiki.archlinux.org/index.php/Splunk

3. You can also view internal logs about the Add-on by using the following search:

    
    ```
    index=_internal source=*nest.log
    ```
    

Disclaimer: 
---------------------

Though this Add-on does use REST Streaming Requests to access data from Nest and store it in Splunk, it is not intended to provide real-time alerts regarding the status of your Nest Protect. You should utilize the official [Nest App](https://nest.com/app/) in order to receive alerts.

If you need assistance with the app you can use the instructions above or reach out on Splunk Answers. 
