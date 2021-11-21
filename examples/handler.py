import time

import requests


def handler(context, event):
    sleepy_task()
    cpu_intensive_task()
    io_task()
    return {"some processed": "data"}


def sleepy_task():
    time.sleep(3)  # ~3 seconds (captain obvious)


def cpu_intensive_task():
    operation = [
        lambda n, x: n.__add__(x),
        lambda n, x: n.__sub__(x),
        lambda n, x: n.__mul__(x),
        lambda n, x: n.__truediv__(x),
    ]
    iterations = 17 ** 6  # ~3 seconds on a i7-1165G7 @ 2.80GHz

    n = 42
    for i in range(iterations):
        op = operation[i % 4]
        n = op(n, i)


def io_task():
    requests.get("http://localhost:8000")  # ~3 seconds (check server.py)
