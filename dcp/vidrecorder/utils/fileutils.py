import os
import psutil
import re
import pwd
import grp
from pathlib import Path

def dcp_mkdir(path, group="ibcs", permissions=0o666):
    if not os.path.exists(path):
        os.mkdir(path)
        set_group(path,group)
        set_permissions(path,permissions)
    else:
        print(f'Trying to set credentials on path: {path}')
        print(f'   group: {group}')
        print(f'   chmod: {permissions}')
        dcp_tryto_set_credentials(path,group,permissions)

def dcp_tryto_set_credentials(filepath,group,permissions):
    try_set_group(filepath,group)
    try_set_permissions(filepath,permissions)

def try_set_group(filepath,group):
    success = False
    try:
        set_group(filepath,group)
        success = True
    except:
        print(f"Failed trying to change group on existing path: {filepath}")
    return success

def try_set_permissions(filepath,permissions):
    success = False
    try:
        set_permissions(filepath,permissions)
        success = True
    except:
        print(f"Failed trying to change permissions on existing path: {filepath}")
    return success

def set_group(path,group="ibcs"):
    user = os.environ['USER']
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    # Set the file's group (python defaults to using the user name as the group name)
    os.chown(path,uid,gid)

def set_permissions(path,octval):
    # Set permissions on the file
    os.chmod(path,octval)

def fileparts(path):
    """Returns (dir,filename,extension) of path

    Args:
        path (string): path to file, absoulte or relative

    Returns:
        tuple : (dir,filename,extension) of path, all strings
    """
    dirname = os.path.dirname(path)
    basename_with_ext = os.path.basename(path)
    basename = os.path.basename(basename_with_ext).split('.',1)[0]
    ext = os.path.splitext(path)[1]
    return (dirname,basename,ext) # matlab style,

