"""Collection of decorators for the app."""

import threading


def threadasync(f):
    """Run this function in a separate thread."""
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper
