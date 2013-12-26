#!/usr/bin/env python
# encoding: utf-8

from topaz.timeout import timethis
import time


@timethis
def delaysec(n):
    time.sleep(n)

if __name__ == "__main__":
    print delaysec(5, timeout=1)
