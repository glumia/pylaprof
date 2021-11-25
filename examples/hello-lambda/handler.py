import time

from pylaprof import S3, profile

storer = S3()


@profile(period=0.001, min_time=6, storer=storer)
def handler(context, event):
    print("handler: received context", context, "and event", event)
    sleepy_task()
    cpu_intens_task()
    print("handler: done")
    return {"some processed": "data"}


def sleepy_task():
    time.sleep(3)  # ~3 seconds (captain obvious)


def cpu_intens_task():
    i = 0
    while i < 10 ** 6:  # ~3 seconds on a i7-1165G7 @ 2.80GHz
        i += 1
