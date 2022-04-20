#!/bin/bash

# configure data drive mounts

MNT1='/data_local/dcp/data/dd1'
MNT2='/data_local/dcp/data/dd2'
DEV1='/dev/sdb'
DEV2='/dev/sdc'
LABEL1='DCP_DATA_01'
LABEL2='DCP_DATA_02'

# create directories, format data drives
mkdir -p $MNT1 $MNT2
mkfs.ext4 -F $DEV1 $DEV2

# backup /etc/fstab, do not overwrite if exists
if [ ! -f /etc/fstab.bak ]; then
        cp -ar /etc/fstab /etc/fstab.bak
fi

# label data drives, append to /etc/fstab, mount
e2label $DEV1 $LABEL1
e2label $DEV2 $LABEL2
echo -e "LABEL=$LABEL1  $MNT1  ext4  defaults,nofail  1 2" >> /etc/fstab
echo -e "LABEL=$LABEL2  $MNT2  ext4  defaults,nofail  1 2" >> /etc/fstab
mount -a
