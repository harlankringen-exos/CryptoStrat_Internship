
import time
from multiprocessing import Pool
from main import main


if __name__ == "__main__":

    one_hour_start = time.time()
    
    while True:
        toc = time.time()
        if toc - one_hour_start > 60*60:   # if we've gone over an hour tidy up
            break
        else:
            with Pool(3) as p:
                p.map(main, [f'a',f'b',f'c'])
            time.sleep(5*60) # sleep 5 minutes
    print("hour elapsed, work here is done")
