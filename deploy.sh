#!/bin/bash

# setup, install DCP application files

# constants
OWNER=$USER
PERMS=777
GRP=ibcs
SCRIPTS='/data_local/dcp/artifacts/scripts'
HOME="/data_local"

# deploy application artifacts
echo -e "Copying application files..\nPlease wait, this may take a while.\n"
sudo cp -R "dcp" $HOME
echo -e "Preparing storage disks.\n"
sudo sh $SCRIPTS/mounts.sh
sudo chown -R $OWNER $HOME/dcp
sudo chgrp -R $GRP $HOME/dcp
sudo chmod -R $PERMS $HOME/dcp
echo -e "Installing dependencies.\n"
$SCRIPTS/auto_start.sh
echo -e "DCP Installation Complete.\n"
