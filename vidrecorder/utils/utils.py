def bytesto(bytes, to, bsize=1024):
    '''convert bytes tp megabytes, etc.
        sample code:
            print(f'mb= {str(bytesto(314575262000000,'mb'))}')
        sample output:
            mb= 300002347.946
    '''
    a = {'kb': 1,'mb': 2,'gb': 3, 'tb': 4, 'pb': 5, 'eb': 6}
    return float(bytes) / bsize ** a[to]