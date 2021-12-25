import os
import re
from pathlib import Path

def bytesto(bytes, to, bsize=1024):
    '''convert bytes tp megabytes, etc.
        sample code:
            print(f'mb= {str(bytesto(314575262000000,'mb'))}')
        sample output:
            mb= 300002347.946
    '''
    a = {'kb': 1,'mb': 2,'gb': 3, 'tb': 4, 'pb': 5, 'eb': 6}
    return float(bytes) / bsize ** a[to]

def bytesto_string(bytes, bsize=1024):
    b = float(bytes)
    if b >= (bsize ** 4):
        return f'{bytesto(b, "tb"):.2f} TB'
    elif b >= (bsize ** 3):
        return f'{bytesto(b, "gb"):.2f} GB'
    elif b >= (bsize ** 2):
        return f'{bytesto(b, "mb"):.2f} MB'
    else:
        return f'{bytesto(b, "kb"):.2f} KB'

def find_paths_in(dir,matching_pattern):
    '''Returns list of absolute paths in dir matching the matching_pattern

       note: matching_pattern follows Unix shell rules
       note: results are returned in arbitrary order
       note: tilde is not expanded, use os.path.expanduser for that
    '''
    search_path = os.path.join(dir,matching_pattern)
    path_matches = glob.glob(search_path)
    return path_matches

def str2float(s):
    '''Converts 'str' to float -- returns float if valid, None if not'''
    val = None
    try:
        val = float(s)
    except ValueError as e:
        print(e)
    return val

def str2int(s):
    '''Converts 'str' to int -- returns float if valid, None if not'''
    val = None
    try:
        val = int(s)
    except ValueError as e:
        print(e)
    return val

def str2bool(s,trueStrings=["True","1"]):
    '''Converts 's' to bool -- returns True if member of trueStrings otherwise False'''
    return s in trueStrings

def convert_config_val(config_val,convert2type,default_val,min_max):
    '''Converts to config_val to convert2type, also checks min_max constraints
       if error at any stage will return the default_val
    '''
    v = None
    if convert2type == 'int':
        v = str2int(config_val)
    elif convert2type == 'float':
        v = str2float(config_val)
    elif convert2type == 'bool':
        v = str2bool(config_val)
        return v

    # If numeric validate the min/max
    if (not v) or (min_max[0] and v < min_max[0]) or (min_max[1] and v > min_max[1]):
        v = default_val

    return v

def validate_ip(ip, run_ping_test=False, ping_timeout_sec=1, ping_count=1):
    '''validates ip formatting and with optional ping test'''

    # Make a regular expression for validating an Ip-address
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

    # pass the regular expression and the string in search() method
    valid_ip_format = False
    if(re.search(regex, ip)):
        valid_ip_format = True

    # run the ping test if they want it
    valid_ping = False
    if run_ping_test and valid_ip_format:
        for i in range(ping_count):
            print(f'Pinging {ip} ... try {i+1}')
            response = os.system(f'ping -c 1 -w {ping_timeout_sec} {ip} > /dev/null 2>&1')
        # response = os.system(f'ping -c 1 -w {ping_timeout_sec} {ip} > /dev/null 2>&1')
        valid_ping = response == 0

    return (valid_ip_format, valid_ping)

def timetranslator(sec):
    sec = int(sec)
    hours = int(sec/3600)
    sec %= 3600
    minutes = int(sec/60)
    sec %= 60
    fstring = f'{hours:02}:{minutes:02}:{sec:02}'

    return fstring

def show_vars(*args,**kwargs):
    print(locals())
    
def sort_files_by_creation_time(filelist):
    ''' returns list of tuples sorted by creation time, each tuple is (creation_time, path)'''
    pathlist = [Path(f) for f in filelist]
    clist = [(p.stat().st_ctime,p) for p in pathlist]
    clist.sort()
    return clist 
    # abs_list = [os.path.join(c[1].parent,c[1].name) for c in clist]
    # return abs_list

