


class Globals:
    def __init__(self, logger=print):
        self.config = None # reference parsed config file
        self.logger = logger
        self.version = None
        self.dev_mode = False # dev_mode or prod_mode
        self.dev_opts = {}
        self.paths = {
            'exedir': [],
            'viddir': [],
            'sdpdir': [],
            'logdir_runtime': [],
        }

g = Globals()
