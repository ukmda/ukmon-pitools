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

from uploadToArchive import uploadToArchive, readIniFile, updateExtrascript


ukmlog = logging.getLogger("ukmonlogger")
ukmlog.setLevel(logging.INFO)

versionid = "2026.9.2"


def setupLogging(logpath, prefix):
    print('about to initialise logger')
    logdir = os.path.expanduser(logpath)
    os.makedirs(logdir, exist_ok=True)

    logfilename = os.path.join(logdir, prefix + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S.%f') + '.log')
    handler = logging.handlers.TimedRotatingFileHandler(logfilename, when='D', interval=1) 
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s-%(levelname)s-%(module)s-line:%(lineno)d - %(message)s', 
        datefmt='%Y/%m/%d %H:%M:%S')
    handler.setFormatter(formatter)
    ukmlog.addHandler(handler)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    formatter = logging.Formatter(fmt='%(asctime)s-%(levelname)s-%(module)s-line:%(lineno)d - %(message)s', 
        datefmt='%Y/%m/%d %H:%M:%S')
    ch.setFormatter(formatter)
    ukmlog.addHandler(ch)

    ukmlog.setLevel(logging.INFO)

    purgeOldLogs(logdir, prefix)

    ukmlog.info('logging initialised')
    return 


def purgeOldLogs(logdir, logpref, days=30):
    reftime = time.time() - 86400*days
    for logf in glob.glob(os.path.join(logdir, logpref + '*.log*')):
        if os.path.getmtime(logf) < reftime:
            ukmlog.debug('removing old log', logf)
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
    ukmlog.info(f'ukmon external script started, version {versionid}')
    
    rebootlockfile = os.path.join(config.data_dir, config.reboot_lock_file)
    with open(rebootlockfile, 'w') as f:
        f.write('1')

    ukmlog.info('uploading key science files to archive')
    keys = uploadToArchive(arch_dir, config.stationID, sciencefiles=True)
    # create jpgs from the potential detections
    ukmlog.info('creating JPGs')
    try:
        bff2i.batchFFtoImage(arch_dir, 'jpg', True)
    except Exception:
        bff2i.batchFFtoImage(arch_dir, 'jpg')

    myloc = os.path.split(os.path.abspath(__file__))[0]
    updateExtrascript(os.path.join(myloc, 'ukmon.ini'), myloc)
    inifvals = readIniFile(os.path.join(myloc, 'ukmon.ini'), config.stationID)
    if not inifvals or inifvals['LOCATION']=='NOTCONFIGURED':
        return False
    ukmlog.info('app home is {}'.format(myloc))
    if 'DOMP4S' in inifvals and int(inifvals['DOMP4S']) == 1: 
        # generate MP4s of detections
        ukmlog.info('generating MP4s')
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
        ukmlog.info('mp4 creation not enabled')
    
    ukmlog.info('uploading remaining files to archive')
    uploadToArchive(arch_dir, config.stationID, keys=keys)

    if inifvals['EXTRASCRIPT']:
        try:
            ukmlog.info('running additional script {:s}'.format(inifvals['EXTRASCRIPT']))
            sloc, sname = os.path.split(inifvals['EXTRASCRIPT'])
            sys.path.append(sloc)
            scrname, _ = os.path.splitext(sname)
            print('about to import extl module')
            ukmlog.info('about to import extl module')
            nextscr=impmod(scrname)
            ukmlog.info('launching {} from {}'.format(scrname, sloc))
            nextscr.rmsExternal(cap_dir, arch_dir, config)
        except Exception as e:
            ukmlog.warning('problem calling external script')
            ukmlog.warning(e)
    else:
        ukmlog.info('additional script not called')

    if os.path.isfile(rebootlockfile):
        os.remove(rebootlockfile)
    ukmlog.info('ukmon done')
    print('ukmon done')
    # clear log handlers again
    #for handler in ukmlog.handlers[:]:
    #    ukmlog.removeHandler(handler)
    #    handler.close()
    return True


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Run ukmon postprocessing script.")
    arg_parser.add_argument('-d', '--dir_path', nargs=1, metavar='DIR_PATH', type=str,
        help='Path to CapturedFiles folder to process. Defaults to latest.')

    arg_parser.add_argument( '-c', '--config', nargs=1, metavar='CONFIG_PATH', type=str,
        help="Path to the RMS config file. Defaults to working it out from dir_path")
    
    cml_args = arg_parser.parse_args()

    if not cml_args.config and not cml_args.dir_path:
        print('Must supply either --dir_path or --config parameters')
        exit(1)

    if cml_args.dir_path:
        arch_dir = os.path.normpath(cml_args.dir_path[0])
        if not os.path.isdir(arch_dir):
            print(f'Target path {arch_dir} not found.')
            exit(1)
        rms_cfg_file = os.path.join(arch_dir, '.config')
        if not os.path.isfile(rms_cfg_file):
            print(f'Target path {arch_dir} does not contain an RMS config file.')
            exit(1)
        rmscfg = cr.loadConfigFromDirectory([rms_cfg_file], 'notused')

    else: # cml_args.config was supplied
        rms_cfg_file = cml_args.config[0]
        if not os.path.isfile(rms_cfg_file):
            print(f'Config file {rms_cfg_file} not found.')
            exit(1)
        rmscfg = cr.loadConfigFromDirectory([rms_cfg_file], 'notused')
        if rmscfg.stationID == 'XX0001':
            print(f'Station not configured in {rms_cfg_file}')
            exit(1)
        base_dir = os.path.join(rmscfg.data_dir, 'ArchivedFiles')
        archdirs = glob.glob(f'{base_dir}/*')
        archdirs = [x for x in archdirs if '.bz2' not in x]
        archdirs.sort()
        arch_dir = archdirs[-1]

    cap_dir = arch_dir.replace('ArchivedFiles','CapturedFiles')
    print(f'processing {arch_dir}')
    rmsExternal(cap_dir, arch_dir, rmscfg)
