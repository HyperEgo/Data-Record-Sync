#!/bin/bash

# DCP artifact installs

ARTS='/data_local/dcp/artifacts'
REPO='/data_local/dcprepo'

# install rpms
mkdir -p $REPO
find $ARTS/archives/rpms -iname "*.rpm" -exec cp -ar '{}' $REPO/. \;
cd $REPO/
#sed -i 's/enabled = 0/enabled = 1/' /etc/yum.repos.d/IBCS-other.repo
createrepo .
yum clean all
yum makecache
yum install -y * --nogpgcheck
#sed -i 's/enabled = 1/enabled = 0/' /etc/yum.repos.d/IBCS-other.repo

# upgrade pip3, install wheels
cd $ARTS/archives/wheels
pip3 install pip-21.1.2-py3-none-any.whl 
pip3 install --no-index --find-links * 

# install python pip archives
cd $ARTS/archives/piparch
pip3 install *

# OSM firewall config
sudo /usr/bin/ansible-playbook $ARTS/plays/firewall.yml
