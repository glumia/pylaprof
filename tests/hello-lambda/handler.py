import time

from pylaprof import S3, profile

storer = S3(create_bucket=False)


@profile(storer=storer)
def handler(context, event):
    print("handler: received context", context, "and event", event)
    sleepy_task()
    cpu_intens_task()
    print("handler: done")
    return {"some processed": "data"}


def sleepy_task():
    time.sleep(3)  # ...


def cpu_intens_task():
    i = 0
    while i < 10 ** 6:  # Will take ~3 seconds (at least on my laptop)
        i += 1
