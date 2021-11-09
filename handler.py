import time

import requests


def handler(context, event):
    print("handler: received context", context, "and event", event)
    sleepy_task()
    cpu_intens_task()
    io_task()
    print("handler: done")
    return {"some processed": "data"}


def sleepy_task():
    time.sleep(3)  # ...


def cpu_intens_task():
    i = 0
    while i < 10 ** 8:  # Will take ~3 seconds
        i += 1


def io_task():
    requests.get("http://localhost:8080")  # Will take ~3 seconds
