import os
import time

def DeletingOldLogs(directory='logs', days=7):
    with scandir(directory) as it:
        for entry in it:
            f=os.path.join(directory,entry.name)
            if os.stat(f).st_mtime < time.time() - days * 86400:
                os.remove(f)
    pass
