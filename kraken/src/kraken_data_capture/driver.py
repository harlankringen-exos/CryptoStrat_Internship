
# proc1: subscribes to the book-100 and trade data to get the snapshot message followed by 100 book-100 or trade
# messages in a new file each time, disconnects, sleeps for 5 min, awakens, repeats until an hour has passed at which point it is dead

import time
from multiprocessing import Process
from main import main


if __name__ == "__main__":

    one_hour_start = time.time()
    ctr = 0
    procs = []
    WAIT = 2
    TOTAL_RUNTIME = 20
    
    for i in range(3):
        p  = Process(target=main, args=(time.time(), 'trade',f'{i}'), name = ('process_' + str(i+1)))
        procs.append(p)
        p.start()
        time.sleep(1)
        print( 'starting', p.name)

    while True:
        toc = time.time()
        if toc - one_hour_start > TOTAL_RUNTIME*60:   # if we've gone over TOTAL_RUNTIME hours tidy up
            print("breaking")
            break
        else:
            main(one_hour_start, 'book', f'{ctr}')
            time.sleep(WAIT*60) # sleep WAIT minutes
            ctr += 1
    print("hour elapsed, work here is done")
