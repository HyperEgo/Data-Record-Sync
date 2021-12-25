# DCP

Data Record Sync or Data Capture Playback [DCP] is a video recording, input streaming and playback application initially designed as a promotional feature demonstration prototype to aid and assist with visual cataloging of user console event actions.  Preliminary concepts were limited to video data however future features adds include audio synchronization, OS and user defined event logs.

## Getting Started

* Execute deployment script:  [Bash Deploy](https://github.com/HyperEgo/Data-Record-Sync/blob/master/dcp_install.sh)
* Start application:  /data_local/dcp/vidrecorder/app.py
* Dependency list:  [Libraries Plugins Installers](https://github.com/HyperEgo/Data-Record-Sync/blob/master/dcp/artifacts/archives_list.txt)

## Testing & Documentation

Consult official documentation for Test Procedures and Operational instructions.

Application is standalone, implemented in python3 script language; no Unit, UI or Integration tests included.

### Source Style Guidelines

Source and style guidelines follow paradigms outlined by Python3 and Open Source Community.

Caveat: source captured from Low Side development environments, exists in this repository for reference only, not for profit or commercial distribution.

## Development & Build Environment
* IDE:  [Visual Studio Code](https://code.visualstudio.com/docs)
* Development OS:  [Ubuntu 20.04.3 LTS (Focal Fossa)](https://releases.ubuntu.com/20.04/)
* Target OS:  [RHEL 7](https://access.redhat.com/products/red-hat-enterprise-linux)
* Source and Build Framework:  [Python 3.8.0](https://www.python.org/downloads/release/python-380/)
* Python3 Plugin Installer:  [PIP 21.2.4](https://pypi.org/project/pip/)
* Video Streamer and Playback:  [VLC for RHEL 7](https://www.videolan.org/vlc/download-redhat.html)

### Authors Contributors

Sofware Engineering, Development Operations, Python3, Linux Open Source Community