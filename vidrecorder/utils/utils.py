import os
import re

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
    

def validate_ip(ip, run_ping_test=False, ping_timeout_sec=1):
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
        response = os.system(f'ping -c 1 -w {ping_timeout_sec} {ip} > /dev/null 2>&1')
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