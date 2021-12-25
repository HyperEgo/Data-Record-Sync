#!/bin/bash

# configure data drive mounts

MNT1='/data_local/dcp/data/dd1'
MNT2='/data_local/dcp/data/dd2'

mkdir -p $MNT1 $MNT2
mkfs.ext4 -F /dev/sdb
mkfs.ext4 -F /dev/sdc
cp -ar /etc/fstab /etc/fstab.bak
e2label /dev/sdb DCP_DATA_01
e2label /dev/sdc DCP_DATA_02
echo -e "LABEL=DCP_DATA_01  $MNT1  ext4  defaults,nofail  1 2" >> /etc/fstab
echo -e "LABEL=DCP_DATA_02  $MNT2  ext4  defaults,nofail  1 2" >> /etc/fstab
mount -a
