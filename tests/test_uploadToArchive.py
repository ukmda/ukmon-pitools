# tests for uploadToArchive

import boto3
import os
import shutil
from uploadToArchive import readKeyFile, uploadOneFile, manualUpload, \
    readIniFile, checkMags, updateLocation, getLatestKeys, keyfilename
from ukmonInstaller import updateHelperIp

basedir = os.path.realpath(os.path.dirname(__file__))
tmpdir = os.path.join(basedir, 'output')
if not os.path.isdir(tmpdir):
    os.makedirs(tmpdir)
shutil.copyfile(os.path.join(basedir, '../ukmon.ini'),os.path.join(basedir,'ukmon.ini'))
updateHelperIp(basedir, helperip='batchserver.ukmeteors.co.uk')
updateLocation(basedir, 'testpi4')
getLatestKeys(basedir, 'testpi4')


def test_checkMags():
    inifvals = readIniFile(os.path.join(basedir,'ukmon.ini'), 'testpi4')
    maglim = 6
    if 'MAGLIM' in inifvals:
        maglim = float(inifvals['MAGLIM'])
    arch_dir = os.path.join(basedir, 'ukmarch','sampledata', 'UK0006_20220914_185543_087124')
    daydir = 'UK0006_20220914_185543_087124'
    validffs = checkMags(arch_dir, 'FTPdetectinfo_{}.txt'.format(daydir), maglim)
    print(validffs)
    assert 'FF_UK0006_20220914_200343_841_0101120.jpg' in validffs


def test_readIniFile():
    inifs = readIniFile(os.path.join(basedir,'ukmon.ini'), 'testpi4')
    assert inifs['LOCATION']=='testpi4'


def test_readKeyFile():
    inifs = readIniFile(os.path.join(basedir,'ukmon.ini'), 'testpi4')
    vals = readKeyFile(os.path.join(basedir,keyfilename), inifs)
    assert vals['S3FOLDER'] in  ['test/uploads/main','archive/Tackley']


def test_readKeyfileIni():
    vals = readIniFile(os.path.join(basedir,'ukmon.ini'), 'testpi4')
    assert vals['RMSCFG'] in ['~/source/Stations/UK0006/.config', '/root/source/RMS/.config', '~/source/RMS/.config']


def test_uploadOneFile():
    inifs = readIniFile(os.path.join(basedir,'ukmon.ini'), 'testpi4')
    keys = readKeyFile(os.path.join(basedir,keyfilename), inifs)
    reg = keys['ARCHREGION']
    conn = boto3.Session(aws_access_key_id=keys['AWS_ACCESS_KEY_ID'], aws_secret_access_key=keys['AWS_SECRET_ACCESS_KEY']) 
    s3 = conn.resource('s3', region_name=reg)
    targf = keys['S3FOLDER']
    arch_dir = os.path.join(basedir, 'ukmarch','testpi4_20230401')
    dir_file = 'test.json'
    file_ext = '.json'
    uploadOneFile(arch_dir, dir_file, s3, targf, file_ext, keys)
    outf = os.path.join(basedir, 'output', 'foobar.txt')
    testkey = '{}/testpi4/2023/202304/20230401/test.json'.format(targf)
    s3.meta.client.download_file(keys['ARCHBUCKET'], testkey, outf)
    lis = open(outf,'r').readlines()
    assert lis[0].strip() == '{ "foo": "bar" }'
    os.remove(outf)


"""
def test_manualUpload():
    targ_dir = 'test'
    updateLocation(os.path.join(basedir,'..'), 'testpi4')
    updateHelperIp(os.path.join(basedir,'..'), 'batchserver.ukmeteors.co.uk')
    getLatestKeys(os.path.join(basedir,'..'), 'testpi4')
    assert manualUpload(targ_dir, 'uk0006') is True
    targ_dir = os.path.join(basedir, 'ukmarch','testpi4_20230401')
    # create some dummy sample files
    testfilelist = ['FF_test_20230401.fits','FF_test_20230401.jpg','FF_test_20230401.mp4','mask.bmp',
                    'platepars_all_recalibrated.json',
                    'FTPdetectinfo_testpi4_20230401.txt',
                    'stack_.jpg','calib.jpg', '.config'
                    ]
    for fil in testfilelist:
        open(os.path.join(targ_dir, fil), 'w').write('{"test":"potato"}')
    assert manualUpload(targ_dir, None)
    #updateLocation(basedir, 'NOTCONFIGURED')
    for fil in testfilelist:
        os.remove(os.path.join(targ_dir, fil))
"""