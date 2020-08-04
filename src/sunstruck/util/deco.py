import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def ambiguous(decorator):
    """ Decorator to allow the decorated function to be called with or without
        parenthesis. Should only be used to decorate other decorator defintions"""

    @functools.wraps(decorator)
    def wrapper(*args, **kwargs):
        if len(args) > 0:
            f = args[0]
        else:
            f = None

        if callable(f):
            return decorator()(f)  # pass the function to be decorated
        else:
            return decorator(*args, **kwargs)  # pass the specified params

    return wrapper


@ambiguous
def safe_convert(return_none_on_error: bool = True) -> Callable:
    """Decorator to suppress errors resulting from type conversion

    Keyword Arguments:
        return_none_on_error {bool} -- If True, return None if an error is raised
            during conversion. Otherwise, return the a tuple of the original args
            and kwargs when an error is raised. (default: True)

    Returns:
        Decorator
    """

    def deco(func) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.debug(f"{func} failed: {e}")
                if return_none_on_error:
                    return None
                else:
                    return args, kwargs

        return wrapper

    return deco
