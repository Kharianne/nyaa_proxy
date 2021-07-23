from functools import wraps
import time
import secrets


def constant_time_compare(val1, val2):
    """
    Returns True if the two strings are equal, False otherwise.
    """
    return secrets.compare_digest(val1, val2)


def retry(exceptions, wait=1):
    """
    Modified decorator from this source:
    https://gist.github.com/FBosler/be10229aba491a8c912e3a1543bbc74e

    """
    def retry_decorator(f):
        @wraps(f)
        def func_with_retries(*args, **kwargs):
            try:
                total_tries = kwargs.get('retries') + 1
            except (TypeError, KeyError):
                total_tries = 1

            while total_tries > 0:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    total_tries -= 1
                    if total_tries == 0:
                        raise e
                    time.sleep(wait)
        return func_with_retries
    return retry_decorator
