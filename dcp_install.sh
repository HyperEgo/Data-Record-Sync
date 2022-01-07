#!/bin/bash

# setup and install for DCP media deploy

# constants
OWNER=eacct
PERMS=775
GRP=ibcs
SCRIPTS='/data_local/dcp/artifacts/scripts'
APPHOME="/data_local"

# configure application home directory
echo -e "Copying application files..\nPlease wait, this may take a while.\n"
sudo cp -ar "dcp" $APPHOME
echo -e "Preparing storage disks.\n"
sudo sh $SCRIPTS/mounts.sh
sudo chown -R $OWNER $APPHOME/dcp
sudo chgrp -R $GRP $APPHOME/dcp
sudo chmod -R $PERMS $APPHOME/dcp
echo -e "Installing dependencies.\n"
$SCRIPTS/auto_start.sh
echo -e "DCP Installation Complete.\n"
