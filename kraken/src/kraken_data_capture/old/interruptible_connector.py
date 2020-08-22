 
# proc1: subscribes to the book-100 and trade data to get the snapshot message followed by 100 book-100 or trade
# messages in a new file each time, disconnects, sleeps for 5 min, awakens, repeats until an hour has passed at which point it is dead

import asyncio
import time
from multiprocessing import Process, Queue
from main import main
import random

def send_kill(q, pid):
    print("putting", pid)
    q.put(pid)
    #print("waiting")
    #response = q.get(block=True) # should be pretty fast
    #return response

if __name__ == "__main__":

    one_hour_start = time.time()
    ctr = 0
    procs = []
    killQ = []
    WAIT_SEC = 2
    TOTAL_RUNTIME_MIN = 5
    forced_sleep_interval_sec = 30 

    for i in range(3):
        killQ.append(Queue())
        p  = Process(target=main, args=(time.time(), killQ[i], 'trade',f'{i}'), name = ('process_' + str(i+1)))
        procs.append(p)
        p.start()
        print( 'starting', p.name)

    while (time.time() - one_hour_start) < TOTAL_RUNTIME_MIN * 60:
        print(time.time() - one_hour_start)
        
        dead = random.randint(0,10)
        if dead % 2 == 0:
            procsecuted = random.randint(0,2)
            send_kill(killQ[procsecuted], procs[procsecuted].pid)
            # procs[procsecuted].terminate()
            print("killed proc!", procs[procsecuted])
            procs.remove(procs[procsecuted])

            asyncio.sleep(forced_sleep_interval_sec - 10)
            
            newproc = Process(target=main, args=(time.time(), killQ[procsecuted], 'trade',f'{procsecuted}'), name = ('process_' + str(procsecuted)))
            procs.append(newproc)
            newproc.start()
            print("started new proc")
        print("sleeping")
        asyncio.sleep(forced_sleep_interval_sec)
           
    print("that's time")
    for idx,p in enumerate(procs):
        send_kill(killQ[idx], p.pid)
        p.terminate()
        p.join()
            
