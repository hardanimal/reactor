import signal
import time
from functools import wraps


class TimeoutException(Exception):
    pass


def timethis(func):
    '''
    Decorator that reports the execution time.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        def timeout_handler(signum, frame):
            raise TimeoutException()

        signal.signal(signal.SIGALRM, timeout_handler)
        timeout_time = kwargs.pop("timeout", 0)
        signal.alarm(timeout_time)   # triger alarm in timeout_time seconds
        try:
            start = time.time()
            result = func(*args, **kwargs)
            eplased = round(time.time()-start, 3)
            return {"result": result, "timeout": False, "eplased": eplased}
        except TimeoutException:
            return {"result": None, "timeout": True, "eplased": None}
        signal.alarm(0)     # cancel the alarm
    return wrapper

if __name__ == "__main__":
    @timethis
    def count(n):
        x = 0
        for i in range(0, n):
            x += i
            i += 1
            time.sleep(0.1)
        return x

    print count(100)
    print count(100, timeout=5)
# {'result': 4950, 'timeout': False, 'eplased': 10.016}
# {'result': None, 'timeout': True, 'eplased': None}
