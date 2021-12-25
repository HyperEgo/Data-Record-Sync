# DCP

Data Capture Playback [DCP] is a video recording, input streaming and playback application initially designed as a promotional feature demonstration prototype to aid and assist with visual cataloging of user event actions at each EOC workstation.  Preliminary concepts were limited to video however additional features such as audio recordings and event logging have been added to complete the total Warfighter operational picture.

## Getting Started

Execute script 'dcp_install.sh' for application deployment to RHEL 7 environment.  Start DCP application /data_local/dcp/vidrecorder/app.py

### Pre-requisites & Installation

Dependencies required are listed in /data_local/dcp/artifacts/dcp_archives.txt

## Testing & Documentation

Consult official documentation for Test Procedures and Operations.

### Unit, Functional & Integration Tests

DCP Application is standalone and implemented in python3 script language.  No Unit testing or integration test necessary.

### Documentation and Support Materials

Refer to official documentation link for support and operation.

### Source & Style Guidelines

DCP source, style and guideline architecture follow rules outlined in Python3 Open Source Community

## Deployment

DCP application deployment is initiated for executing dcp_install.sh

## Development, Build & Target Environment

DCP development teams conduct initial feature work in Low Side environments, test and deploy to RHEL 7 systems, then proceed to push code and support materials to High Side environments for final testing and release.  

### Dev and Build Env
* [Visual Studio Code](https://code.visualstudio.com/docs) - IDE
* [Ubuntu 20.04.3 LTS (Focal Fossa)](https://releases.ubuntu.com/20.04/) - operating system
* [Python 3.8.0](https://www.python.org/downloads/release/python-380/) - source and build framework
* [PIP 21.2.4](https://pypi.org/project/pip/) - plugin installer
* [VLC RHEL 7](https://www.videolan.org/vlc/download-redhat.html) - video streamer and playback

### Target Test Env
* [RHEL 7](https://access.redhat.com/products/red-hat-enterprise-linux) - Red Hat Enterprise Linux 7

## Authors, Contributors and Acknowledgments

Sofware Engineers, Development Operations, Python3 Open Source Community