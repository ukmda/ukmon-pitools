#!/bin/bash
#
# Script to gather the logfiles and upload them for debugging & analysis
# Copyright (C) 2018-2023 Mark McIntyre
#
myself=$(readlink -f $0)
here="$( cd "$(dirname "$myself")" >/dev/null 2>&1 ; pwd -P )"

TMPDIR=$HOME/gatherlogtmp
cd $HOME
[ -d $TMPDIR ] && rm -Rf $TMPDIR
mkdir -p $TMPDIR
cd $TMPDIR

source $here/ukmon.ini

if [ ! -d $HOME/source/Stations ] ; then
    rootdir=$HOME/source/RMS
    CAMIDS=$(grep stationID $rootdir/.config | awk '{print $2}')
    if [ "$CAMIDS" == "XX0001" ] ; then
        echo "Unable to find valid camera ID"
    fi 
    singlecam=1
else
    rootdir=$HOME/source/Stations
    if [ "$1" == "" ] ; then 
        echo "Multicam setup, gathering data on all cameras"
        CAMIDS=$(ls $rootdir -1)
    else
        CAMIDS=$1
    fi
    singlecam=0
fi
echo "Processing $CAMIDS"

# find the RMS config and log location

for CAM in $CAMIDS ; do
    if [ $singlecam -eq 1 ] ; then 
        echo cfgdir is $rootdir
        rmscfg=$rootdir/.config
        rmsplt=$rootdir/platepar_cmn2010.cal
    else
        echo cfgdir is $rootdir/$CAM
        rmscfg=$rootdir/$CAM/.config
        rmsplt=$rootdir/$CAM/platepar_cmn2010.cal
    fi 
    datadir=$(python -c "import configparser,os;cfg=configparser.ConfigParser();cfg.read('$rmscfg');print(os.path.expanduser(cfg['Capture']['data_dir']))")
    logdir=$datadir/logs
    echo logdir is $logdir
    # gather the RMS config and logs
    cp $rmscfg $TMPDIR/${CAM}.config
    cp $rmsplt $TMPDIR/${CAM}.cal
    ls -1tr $logdir/log*.log* | tail -5 | while read i; do cp $i $TMPDIR ; done
    ls -1tr $logdir/uk*.log* | tail -5 | while read i; do cp $i $TMPDIR ; done
done
journalctl --boot --no-hostname --no-pager > $TMPDIR/system.log
crontab -l > $TMPDIR/crontab.txt
cp $here/ukmon.ini $TMPDIR
if [ -f $here/cameras.ini ] ; then 
    cp $here/cameras.ini $TMPDIR
    loc=$(python -c "import configparser;cfg=configparser.ConfigParser();cfg.read('cameras.ini');stns=cfg.items('cameras');print(stns[0][1])")
else
    loc=$(grep LOCATION ukmon.ini | awk -F= '{print $2}')
fi

# create a tarball and upload to the server
echo "uploading logs"
ZIPFILE=/tmp/${loc}_logs.tgz
tar czf $ZIPFILE *
sftp -i $UKMONKEY -q logupload@$UKMONHELPER << EOF
cd logs
progress
put $ZIPFILE 
exit
EOF
cd ..
rm -Rf $TMPDIR
echo "done"