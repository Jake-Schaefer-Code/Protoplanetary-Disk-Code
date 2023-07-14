import psutil
import time

start_time = time.time()
cur_time = time.time()
while cur_time - start_time <= 86400 or input != 'STOP':
    cur_time = time.time()
    local_time = time.ctime(cur_time)
    mem = psutil.virtual_memory()
    available = mem.available
    available = str(available / (1024**3))
    total = str(mem.total / (1024**3))
    used = str(mem.used / (1024**3))
    active = str(mem.active / (1024**3))
    percent = str(mem.percent)
    """print(' Used memory: ' + used + ' GB')
    print(' Active memory: ' + active + ' GB')
    print(' Total memory: ' + total + ' GB')"""
    print(local_time)
    print(' Available memory: ' + available + ' GB')
    print(' Percent usage: ' + percent + '%')
    time.sleep(3600)




