#!/bin/bash

# re-mount data drives

MNT1='/data_local/dcp/data/dd1'
MNT2='/data_local/dcp/data/dd2'
DEV1='/dev/sdb'
DEV2='/dev/sdc'

# create directories, format data drives
mkdir -p $MNT1 $MNT2
mkfs.ext4 -F $DEV1 
mkfs.ext4 -F $DEV2

# re-label data drives, mount via label in /etc/fstab
e2label $DEV1 DCP_DATA_01
e2label $DEV2 DCP_DATA_02
mount -a
