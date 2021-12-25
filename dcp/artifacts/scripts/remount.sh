#!/bin/bash

# re-mount data drives

MNT1='/data_local/dcp/data/dd1'
MNT2='/data_local/dcp/data/dd2'

mkdir -p $MNT1 $MNT2
mkfs.ext4 -F /dev/sdb
mkfs.ext4 -F /dev/sdc
e2label /dev/sdb DCP_DATA_01
e2label /dev/sdc DCP_DATA_02
mount -a
