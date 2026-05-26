# 
# python script thats called when the nightly run completes to generate jpgs 
# and upload data to the uk meteor data archive
# Copyright (C) 2018-2023 Mark McIntyre
#

import os
import sys
import glob
import time

import Utils.BatchFFtoImage as bff2i
import Utils.GenerateMP4s as gmp4
import RMS.ConfigReader as cr
from importlib import import_module as impmod
import logging
import datetime
import argparse

from uploadToArchive import uploadToArchive, readIniFile


log = logging.getLogger("ukmonlogger")
log.setLevel(logging.INFO)

versionid = '2026.01.04'


def setupLogging(logpath, prefix):
    print('about to initialise logger')
    logdir = os.path.expanduser(logpath)
    os.makedirs(logdir, exist_ok=True)
    log.info('removing any existing log handlers')
    for handler in log.handlers[:]:
        log.removeHandler(handler)

    logfilename = os.path.join(logdir, prefix + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S.%f') + '.log')
    handler = logging.handlers.TimedRotatingFileHandler(logfilename, when='D', interval=1) 
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s-%(levelname)s-%(module)s-line:%(lineno)d - %(message)s', 
        datefmt='%Y/%m/%d %H:%M:%S')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter(fmt='%(asctime)s-%(levelname)s-%(module)s-line:%(lineno)d - %(message)s', 
        datefmt='%Y/%m/%d %H:%M:%S')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    log.setLevel(logging.INFO)

    purgeOldLogs(logdir, prefix)

    log.info('logging initialised')
    return 


def purgeOldLogs(logdir, logpref, days=30):
    reftime = time.time() - 86400*days
    for logf in glob.glob(os.path.join(logdir, logpref + '*.log*')):
        if os.path.getmtime(logf) < reftime:
            log.debug('removing old log', logf)
            os.remove(logf)
    return 


def rmsExternal(cap_dir, arch_dir, config):
    """ Called from RMS to trigger the UKMON specific code  

    Args:  
        cap_dir (str): full path to the night's CapturedFiles folder  
        arch_dir (str): full path to the night's ArchivedFiles folder  
        config (object): an RMS config object.  

    Don't try to call this function directly unless you know how to create
    an RMS config object in Python. 

    """
    setupLogging(os.path.join(config.data_dir, config.log_dir), f'ukmon_log_{config.stationID}_')
    print('ukmon external script started, version ' + versionid)
    log.info('ukmon external script started, version ' + versionid)
    
    rebootlockfile = os.path.join(config.data_dir, config.reboot_lock_file)
    with open(rebootlockfile, 'w') as f:
        f.write('1')

    log.info('uploading key science files to archive')
    keys = uploadToArchive(arch_dir, config.stationID, sciencefiles=True)
    # create jpgs from the potential detections
    log.info('creating JPGs')
    try:
        bff2i.batchFFtoImage(arch_dir, 'jpg', True)
    except Exception:
        bff2i.batchFFtoImage(arch_dir, 'jpg')

    myloc = os.path.split(os.path.abspath(__file__))[0]
    inifvals = readIniFile(os.path.join(myloc, 'ukmon.ini'), config.stationID)
    if not inifvals or inifvals['LOCATION']=='NOTCONFIGURED':
        return False
    log.info('app home is {}'.format(myloc))
    domp4s = 0
    if 'DOMP4S' in inifvals:
        domp4s = int(inifvals['DOMP4S'])
    elif os.path.isfile(os.path.join(myloc, 'domp4s')):
        domp4s = 1
    if domp4s == 1: 
        # generate MP4s of detections
        log.info('generating MP4s')
        ftpdate=''
        if os.path.split(arch_dir)[1] == '':
            ftpdate=os.path.split(os.path.split(arch_dir)[0])[1]
        else:
            ftpdate=os.path.split(arch_dir)[1]
        ftpfile_name="FTPdetectinfo_"+ftpdate+'.txt'
        try:
            maglim = 1
            if 'MAGLIM' in inifvals:
                maglim = float(inifvals['MAGLIM'])
            gmp4.generateMP4s(arch_dir, ftpfile_name, min_mag=maglim)
        except Exception:
            gmp4.generateMP4s(arch_dir, ftpfile_name)
    else:
        log.info('mp4 creation not enabled')
    
    log.info('uploading remaining files to archive')
    uploadToArchive(arch_dir, config.stationID, keys=keys)

    # do not remove reboot lock file if running another script
    # os.remove(rebootlockfile)
    
    if inifvals['EXTRASCRIPT']:
        log.info('running additional script {:s}'.format(inifvals['EXTRASCRIPT']))
        for handler in log.handlers[:]:
            log.removeHandler(handler)
        sloc, sname = os.path.split(inifvals['EXTRASCRIPT'])
        sys.path.append(sloc)
        scrname, _ = os.path.splitext(sname)
        log.info('about to import extl module')
        nextscr=impmod(scrname)
        log.info('launching {} from {}'.format(scrname, sloc))
        nextscr.rmsExternal(cap_dir, arch_dir, config)
    else:
        log.info('additional script not called')
        try:
            os.remove(rebootlockfile)
        except Exception:
            log.info('unable to remove reboot lock file, pi will not reboot')
            pass

    log.info('done')
    print('done')
    # clear log handlers again
    for handler in log.handlers[:]:
        log.removeHandler(handler)
    return True


def manualRerun(dated_dir, rmscfg = '~/source/RMS/.config'):
    """This function is used to manually rerun the Ukmon post processing script.  
    To invoke this function, open a Terminal window and run the following:  

    *python ../ukmon-pitools/ukmonPostProc.py dated_dir*  

    Args:
        dated_dir (str): The name of the folder to upload eg UK000F_20210512_202826_913898  

    """
    config = cr.parse(os.path.expanduser(rmscfg))
    cap_dir = os.path.join(config.data_dir, 'CapturedFiles', dated_dir)
    if not os.path.isdir(cap_dir):
        return False
    arch_dir = os.path.join(config.data_dir, 'ArchivedFiles', dated_dir)
    if not os.path.isdir(arch_dir):
        return False
    return rmsExternal(cap_dir, arch_dir, config)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Run ukmon postprocessing script.")
    arg_parser.add_argument('-d', '--dir_path', nargs=1, metavar='DIR_PATH', type=str,
        help='Path to CapturedFiles folder to process. Defaults to latest.')

    arg_parser.add_argument( '-c', '--config', nargs=1, metavar='CONFIG_PATH', type=str,
        help="Path to the RMS config file. Defaults to working it out from dir_path")
    
    arg_parser.add_argument( '-t', '--toolcfg', nargs=1, metavar='TOOL_CFG_PATH', type=str,
        help="Path to the ukmon config file. Defaults to loading ukmon.ini from current directory.")
    
    cml_args = arg_parser.parse_args()

    if not cml_args.config and not cml_args.dir_path:
        print('Must supply either --dir_path or --config parameters or both')
        exit(1)

    if cml_args.config:
        rms_cfg_file = cml_args.config
    else:
        rms_cfg_file = [os.path.expanduser('~/source/RMS/.config')]
    rmscfg = cr.loadConfigFromDirectory(rms_cfg_file, 'notused')
    stationId = rmscfg.stationID
    if stationId == 'XX0001':
        print(f'Station not configured in {rms_cfg_file}')

    datadir = rmscfg.data_dir
    if cml_args.dir_path:
        targdir = cml_args.dir_path[0]
        lastcap = os.path.normpath(os.path.expanduser(targdir))
        if not os.path.isdir(lastcap):
            testpth = os.path.expanduser(os.path.join(datadir, 'CapturedFiles', f'*{targdir}*'))
            capdirs = glob.glob(testpth)
            if len(capdirs) == 0:
                print(f'Capture folder {cml_args.dir_path[0]} not found')
                exit(1)
            else:
                capdirs.sort()
                lastcap = capdirs[-1]
    else:
        capdir = os.path.expanduser(os.path.join(datadir, 'CapturedFiles'))
        recentcaps = os.listdir(capdir)
        recentcaps.sort()
        if len(recentcaps) >0:
            lastcap = recentcaps[-1]
        else:
            print(f'no captured data in {capdir}')
            exit(0)
    lastcap = os.path.split(lastcap)[1]

    cap_dir = os.path.join(datadir, 'CapturedFiles', lastcap)
    arch_dir = os.path.join(datadir, 'ArchivedFiles', lastcap)
    print(f'processing {lastcap}')
    rmsExternal(cap_dir, arch_dir, rmscfg)
