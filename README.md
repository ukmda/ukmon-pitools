# Toolset for RMS pi meteor cameras
Version 2026.01.04

These tools manage uploads of RMS data to the UK Meteor Data Archive and to the livestream. There are two parts:  
* The post-processing job that runs after RMS to send data to the archive.  
* The realtime job that uploads detections to the livestream..  

There is more information about RMS and the toolset in the wiki [here](https://github.com/ukmda/ukmon-pitools/wiki "UKMON Wiki")

## INSTALLATION

###  installation
The first steps are for single-station *or* multistatoin setups.

* Login to your pi using VNC or AnyDesk or TeamViewer, open a Terminal window from the Accessories menu, then type the following
``` bash
cd $HOME/source  
git clone https://github.com/ukmda/ukmon-pitools.git  
```

#### Single-station Configuration 
Open a terminal window and type the following, replacing UKxxxxx with your RMS camera ID eg UK12345
``` bash
cd ukmon-pitools  
./setupUkmon.sh  UKxxxxx
```
* When prompted, copy the SSH public key. 
* Email the key to newcamera@ukmeteornetwork.org along with your location (eg the name of your town or village), your GMN camera ID eg UK12345 and the rough direction your camera points in eg SW, S, NE. 

* We will add your key to our server and send you instructions on how to complete the setup. 

### Multistation Configuratoin
First make sure all your cameras are working correctly with RMS. You should have a folder for each camera in ~/source/Stations, and a data
folder for each camera in ~/RMS_data.
Now open a terminal window and type the following, replacing UKxxxxx with your RMS camera ID eg UK12345
``` bash
cd ukmon-pitools  
./setupUkmon.sh  UKxxxxx
```
* When prompted, copy the SSH public key.
* Repeat the last step for each camera you have on this machine. So if you had three cameras, you'd run `setupUkmon.sh` three times and end up with three different SSH keys. 
* Email the keys to newcamera@ukmeteornetwork.org, indicating which RMS ID each one relates to, your location (name of your town or village), and the rough direction your camera points in eg SW, S, ENE.
* We will then send you ukmon IDs and instructions on how to finish the setup.

HOW THE TOOLS WORK
==================

ukmonPostProc.py
================
This uses the RMS post-processing hook to creates JPGs and other data, then upload to the UK Meteor Network archive. The script has three optional capabilities: 


MP4s
------------------
The script can create MP4s of each detection.
To enable these, edit ukmon.ini and set DOMP4S to 1
``` bash
DOMP4S=1
```
Running an Additional Script of your own
----------------------------------------
If you want to run an additional Python script after this one finishes, create a file named "extrascript"  in the same folder, containing a single line with the full path to the script. For example to enable the feed to istrastream, you could open a Terminal window and type the following:  
``` bash
echo "$HOME/source/mystuff/myscript.py" > $HOME/source/ukmon-pitools/extrascript  
```
This should create file called 'extrascript' in the ukmon-pitools folder, containing one line "$HOME/source/mystuff/myscript.py"

The script must contain a function rmsExternal with the following definition
``` python
def rmsExternal(cap_dir, arch_dir, config):
    # do stuff here
```
This will be passed the capture_dir, archive_dir and RMS config object in the same way as RMS passes these to any external script. 

uploadToArchive.py
==================
This does the actual uploading to the UK meteor network archive. Can be called standalone if you want to reupload data:
eg  
``` bash
python uploadToArchive.py UK0006_20210312_183741_206154  
```
this will upload from $HOME/RMS_data/ArchivedFiles/UK0006_20210312_183741_206154

liveMonitor.sh
==============
This script monitors in realtime for detections, then uploads them to the livestream. The script calls a 
python script liveMonitor.py.  

There are two configuration parameters that you can set in ukmon.ini to control how this works: 
* UKMFBINTERVAL: how frequently the process checks whether there's a request for fireball data. Default 1800 seconds. Set to zero to disable the fireball upload feature completely.  
* UKMMAXAGE: How far back to look for events to upload. Default 1800 seconds. Each time the software is restarted, it will look for events in the log. This parameter avoids too much reuploading of old events.  

You shouldn't really need to set these but if you do, then for example edit ukmon.ini and add  
``` bash
export UMFBINTERVAL=900
``` 
to set the check interval to 900 seconds. Note there must be no spaces around the equals sign, and that
export must be in lowercase.  

sendToLive.py
-------------
Part of liveMonitor, this python script does the actual uploading. You can use it manually as follows:  
``` bash
python sendToLive.py capture-dir ff-file-name 
```
refreshTools.sh
===============
Updates the UKMON RMS Toolset to the latest version. After first run, this will run automatically
every time your Pi reboots. You can also run it manually. 

refreshTools reads from a configuration file that is specific to your camera. We will send
you this file when you onboard to the network. The file contains your location ID and the
details of our sftp server used to distribute security keys. 

Questions
=========
Any questions, concerns or suggestions:
* Check the wiki here https://github.com/markmac99/ukmon-pitools/wiki
* Join our group on Groups.io https://groups.io/g/ukmeteornetwork/topics
* As a last resort, email us via newcamera@ukmeteornetwork.org

Copyright
=========
All code Copyright (C) 2018-2023 Mark McIntyre
