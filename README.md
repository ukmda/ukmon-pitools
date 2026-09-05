# Toolset for RMS pi meteor cameras
Version 2026.9.2

These tools manage uploads of RMS data to the UK Meteor Data Archive and to the livestream. There are two parts:  
* The post-processing job that runs after RMS to send data to the archive.  
* The realtime job that uploads detections to the livestream..  

There is more information about RMS and the toolset in our wiki [here](https://github.com/ukmda/ukmon-pitools/wiki "UKMON Wiki")

## INSTALLATION
*NB: first make sure all your RMS stations are set up and working correctly.*

Login to your pi or Linux box, open a Terminal window from the Accessories menu, then type the following
``` bash
cd $HOME/source  
git clone https://github.com/ukmda/ukmon-pitools.git  
```

Now configure the first station by typing the following, replacing UKxxxxx with your RMS camera ID eg UK12345
``` bash
cd $HOME/source/ukmon-pitools  
./setupUkmon.sh  UKxxxxx
```
When prompted, copy the SSH public key and paste it into a text document for safe-keeping. 

Rerun `setupUkmon.sh` for each camera you have on the Pi or Linux box. So if you had three cameras, you'd run `setupUkmon.sh` three times and end up with three different SSH keys. 

* Email the keys to `newcamera@ukmeteornetwork.org`, indicating which RMS ID each key is for, plus your location (name of your town or village), and the rough direction each camera points in eg SW if the camera points approximately south-west.

* We will then add the keys to our server and send you ukmon IDs and instructions on how to finish the setup.

* *Note that in a multi-cam configuration, the LOCATION and UKMONKEY values in `ukmon.ini` are not used. Location is obtained from `cameras.ini` and the keyfile is determined from the RMSID*

### MIGRATION OF AN EXISTING MULTICAM INSTALLATION
There's no need to make any changes as the toolset will work as before for both single and multi-cam setups. 

However, if you have a multi-cam setup and want to consolidate onto a single instance of the toolset, you can do so as follows: 
* Install a new instance:
``` bash
cd $HOME/source  
git clone https://github.com/ukmda/ukmon-pitools.git  
cd $HOME/source/ukmon-pitools/
```
* Run `setupUkmon.sh` for each camera. As you already have UKMON IDs you won't be asked to send us the keys. 
* Open `cameras.ini` in the ukmon-pitools folder and check the mapping from ukmon ID to RMS ID is correct. It should look something like this:
``` bash
# camera mapping file
# echo add all cameras on this PC or Pi even if you only have one camera
[cameras]
UK12345=myloc_s
UK54321=myloc_ne
``` 

* if there were any mismappings, fix them.
* Once you're happy with `cameras.ini`, rerun `setupUkmon.sh` again for each camera in turn. You should now see several success messages. 
* So, if you've got three cameras, you will have run the setup routine six times in total. 

* In a terminal window type `crontab -e` and remove any rows relating to the old versions of the toolset. Be careful not to remove rows for the new installation. 
* Finally, run `refreshTools.sh` and confirm that you get one general success message and one individual message per camera. 

Let the system run normally for a few days before deleting the folders containing the old camera-specific toolsets. 

## Optional Settings

The toolset has three optional capabilities that can be configured via `ukmon.ini`:

* DOMP4S: create short videos of each detection. Default is enabled, set to zero to disable. 
* MAGLIM: magnitude limit below which images won't be uploaded to the server. This is to save space. It does *not* prevent the science data being uploaded, only the images. Default is 1
* EXTRASCRIPT: the full path to a python script that will run after the ukmon tools. See below for more info.


### Running an Additional Script of your own
If you want to run an additional Python script after the ukmon toolset finishes, update EXTRASCRIPT with the full path and name of the python script. For example:
``` bash
export EXTRASCRIPT=/home/rms/source/mystuff/myscript.py
```

The script must contain a function with the following definition
``` python
def rmsExternal(cap_dir, arch_dir, config):
    # do stuff here
```
This function will be passed the capture_dir, archive_dir and RMS config object in the same way as RMS passes these to any external script. So, if you want to do something camera-specific, you can check the config.StationID field. 

### Manually Uploading to UKMON
If you'd like to rerun the daily upload for a given day you can do so in a Terminal window as follows:

``` bash
cd $HOME/source/ukmon-pitools  
python ukmonPostProc.py -d /full/path/to/CapturedFiles/ -c /full/path/to/config-file

```
where `/full/path/to/CapturedFiles/` is the full path to the folder that you want to reprocess eg `~/RMS_data/UK0006/CapturedFiles/UK0006_20210312_183741_206154`  
and `/full/path/to/config-file` is the full path to the RMS config file for the camera eg `~/source/Stations/UK0006/.config`

Rerunning Uploads to the Livestream
-----------------------------------
You can force-restart the uploader by typing
```bash 
cd $HOME/source/ukmon-pitools  
./restartLiveMon.sh force
```
By default, the script will scan the last 30 minutes of the log and upload any events it finds. If you need to scan a longer window, you can do so by setting an environment variable first. For example to scan the last hour do this:

```bash 
export UKMMAXAGE=3600
cd $HOME/source/ukmon-pitools  
./restartLiveMon.sh force
```
## Updating the Toolset
The toolset adds an entry to the system scheduled jobs (crontab) which executes `refreshTools.sh` at boot time. So, on most Raspberry Pi stations the toolset will be updated daily.

If you're running on a Linux box or Pi that is not rebooting each night, I recommend you add a cron entry to force an update at around noon each Sunday, similar to the below. 
``` bash
1 12 * * SUN /home/rms/source/ukmon-pitools/refreshTools.sh > /home/rms/RMS_Data/logs/refreshTools.log 2>&1
```

You can also run the script at any time to force an update immediately.  

Questions
=========
Any questions, concerns or suggestions:
* Check the wiki here https://github.com/ukmda/ukmon-pitools/wiki
* Join our group on Groups.io https://groups.io/g/ukmeteornetwork/topics
* As a last resort, email us via newcamera@ukmeteornetwork.org

Copyright
=========
All code Copyright (C) 2018-2023 Mark McIntyre
