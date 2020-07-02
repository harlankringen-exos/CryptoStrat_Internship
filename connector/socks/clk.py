
# https://realpython.com/python-timer/#python-timers

from contextlib import ContextDecorator
import functools        
import time

class TimerError(Exception):
    """ """

class Timer(ContextDecorator):
    def __init__(self):
        self._start_time = None

    def start(self):
        if self._start_time:
            raise TimerError(f"Timer is running. Use .stop() to stop")
        self._start_time = time.perf_counter()

    def stop(self):
        if not self._start_time:
            raise TimerError(f"Timer is running. Use .stop() to stop")
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
        return elapsed_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()
