# tests for uploadToArchive

import boto3
import os
import shutil
from uploadToArchive import readKeyFile, manualUpload, readIniFile, checkMags, getLatestKeys, keyfilename
from ukmonInstaller import updateHelperIp

basedir = os.path.realpath(os.path.dirname(__file__))
tmpdir = os.path.join(basedir, 'output')
if not os.path.isdir(tmpdir):
    os.makedirs(tmpdir)
shutil.copyfile(os.path.join(basedir, '../ukmon.ini'),os.path.join(basedir,'ukmon.ini'))
updateHelperIp(basedir, helperip='batchserver.ukmeteors.co.uk')
getLatestKeys(basedir, None)


def test_checkMags():
    inifvals = readIniFile(os.path.join(basedir,'ukmon.ini'), None)
    maglim = 6
    if 'MAGLIM' in inifvals:
        maglim = float(inifvals['MAGLIM'])
    arch_dir = os.path.join(basedir, 'ukmarch','sampledata', 'UK0006_20220914_185543_087124')
    daydir = 'UK0006_20220914_185543_087124'
    validffs = checkMags(arch_dir, 'FTPdetectinfo_{}.txt'.format(daydir), maglim)
    print(validffs)
    assert 'FF_UK0006_20220914_200343_841_0101120.jpg' in validffs


def test_readIniFile():
    inifs = readIniFile(os.path.join(basedir,'ukmon.ini'), None)
    assert inifs['LOCATION'] is not None


def test_readKeyFile():
    inifs = readIniFile(os.path.join(basedir,'ukmon.ini'), None)
    vals = readKeyFile(os.path.join(basedir,keyfilename), inifs)
    assert vals['S3FOLDER'] is not None 


def test_uploadOneFile():
    targdir = 'test'
    manualUpload(targdir, None, sciencefiles=True)
