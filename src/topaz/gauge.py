#!/usr/bin/env python
# encoding: utf-8
from functools import wraps
import logging
import signal


"""test retry and timeout decorator
"""


class TimeoutException(Exception):
    pass


def gauge(func):
    '''
    Decorator of retry and timeout
    '''

    @wraps(func)
    def wrapper(*args, **kwargs):
        def timeout_handler(signum, frame):
            raise TimeoutException(func.__name__ + " execution time out.")

        signal.signal(signal.SIGALRM, timeout_handler)
        timeout_time = kwargs.pop("timeout", 0)
        max_retries = kwargs.pop("max_retries", 1)
        for i in range(max_retries):
            signal.alarm(timeout_time)  # triger alarm in timeout_time seconds
            try:
                logging.info(func.__name__ + " is running for " + str(i + 1))
                return func(*args, **kwargs)
            except TimeoutException as e:
                logging.error(func.__name__ + ": timeout.")
                if (i + 1 >= max_retries):
                    raise e
            except Exception as e:
                if (i + 1 >= max_retries):
                    raise e
            finally:
                signal.alarm(0)  # cancel the alarm

    return wrapper


if __name__ == "__main__":
    import time

    @gauge
    def test_gauge():
        time.sleep(2)
        print "finish."

    @gauge
    def test_gauge2():
        x = 1 / 0
        print "finish."
        return x

    class GaugeInClass(object):
        @gauge
        def test(self):
            time.sleep(2)
            print "gauge in class"

    import sys

    logger = logging.getLogger()
    formatter = logging.Formatter('[ %(asctime)s ] %(levelname)s %(message)s')

    # add stdout handler
    stdhl = logging.StreamHandler(sys.stdout)
    stdhl.setFormatter(formatter)
    stdhl.setLevel(logging.DEBUG)  # print everything
    logger.addHandler(stdhl)
    logger.setLevel(logging.DEBUG)

    try:
        test_gauge(timeout=1, max_retries=3)
    except Exception as e:
        logging.error("++++++++Catch:+++++++" + repr(e))
    try:
        test_gauge2(max_retries=5)
    except Exception as e:
        logging.error("++++++++Catch:+++++++" + repr(e))
    try:
        gic = GaugeInClass()
        gic.test(timeout=1, max_retries=2)
    except Exception as e:
        logging.error("++++++++Catch:+++++++" + repr(e))
