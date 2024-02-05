# coding: utf-8
import copy
import inspect
import logging
import asyncio
import random
from functools import wraps

import async_timeout

propagate = ...
forever = ...
__version__ = '2.0.0'
logger = logging.getLogger(__name__)


class RetryError(Exception):
    pass


class ConditionError(Exception):
    pass


def unpartial(fn):
    while hasattr(fn, 'func'):
        fn = fn.func

    return fn


def is_exception(obj):
    return (
            isinstance(obj, Exception) or
            (inspect.isclass(obj) and (issubclass(obj, Exception)))
    )


# https://stackoverflow.com/questions/74345065/attributeerror-module-asyncio-has-no-attribute-coroutine-in-python-3-11
async def callback(attempt, exc, args, kwargs, delay=0.5, *, loop):
    yield from asyncio.sleep(delay, loop=loop)

    return retry


def retry(
        *, fn=None, attempts=3, delay=0.5, max_delay=None, backoff=1, jitter=0, timeout=None, immutable=False,
        callback=callback, fallback=RetryError, retry_exceptions=(Exception,),
        fatal_exceptions=(asyncio.CancelledError,), logger=logger
):
    """

    :param fn: 被装饰的函数
    :param attempts: 设置最大重试次数
    :param delay: 添加每次方法执行之间的等待时间
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param timeout:
    :param immutable:
    :param callback:
    :param fallback: a callable function or a value to return when all attempts are tried.
    :param retry_exceptions:
    :param fatal_exceptions:
    :param logger: 
    :return:
    """
    def wrapper(fn):
        @wraps(fn)
        @asyncio.coroutine
        def wrapped(*fn_args, **fn_kwargs):
            _loop = asyncio.get_event_loop()
            if (
                    timeout is not None and
                    asyncio.TimeoutError not in retry_exceptions
            ):
                _retry_exceptions = (asyncio.TimeoutError,) + retry_exceptions
            else:
                _retry_exceptions = retry_exceptions

            attempt = 1
            _delay = delay
            while True:
                if immutable:
                    _fn_args = copy.deepcopy(fn_args)

                    _fn_kwargs = copy.deepcopy(fn_kwargs)
                else:
                    _fn_args, _fn_kwargs = fn_args, fn_kwargs

                try:
                    ret = fn(*_fn_args, **_fn_kwargs)

                    if timeout is None:
                        if asyncio.iscoroutinefunction(unpartial(fn)):
                            ret = yield from ret
                    else:
                        if not asyncio.iscoroutinefunction(unpartial(fn)):
                            raise ConditionError(
                                'Can\'t set timeout for non coroutinefunction',
                            )

                        with async_timeout.timeout(timeout):
                            ret = yield from ret

                    return ret

                except ConditionError:
                    raise
                except fatal_exceptions:
                    raise
                except _retry_exceptions as exc:
                    _attempts = 'infinity' if attempts is forever else attempts
                    context = {
                        'fn': fn,
                        'attempt': attempt,
                        'attempts': _attempts,
                    }

                    if (
                            _loop.get_debug() or
                            (attempts is not forever and attempt == attempts)
                    ):

                        logger.warning(
                            exc.__class__.__name__ + ' -> Attempts (%(attempt)d) are over for %(fn)r',  # noqa
                            context,
                            exc_info=exc,
                        )
                        if fallback is propagate:
                            raise exc

                        if is_exception(fallback):
                            raise fallback from exc

                        if callable(fallback):
                            ret = fallback(fn_args, fn_kwargs)

                            if asyncio.iscoroutinefunction(unpartial(fallback)):  # noqa
                                ret = yield from ret
                        else:
                            ret = fallback

                        return ret

                    logger.debug(
                        exc.__class__.__name__ + ' -> Tried attempt #%(attempt)d from total %(attempts)s for %(fn)r',
                        # noqa
                        context,
                        exc_info=exc,
                    )

                    ret = callback(
                        attempt, exc, fn_args, fn_kwargs, delay=_delay, loop=_loop,
                    )
                    _delay *= backoff
                    if isinstance(jitter, tuple):
                        _delay += random.uniform(*jitter)
                    else:
                        _delay += jitter
                    if max_delay is not None:
                        _delay = min(_delay, max_delay)
                    attempt += 1

                    if asyncio.iscoroutinefunction(unpartial(callback)):
                        ret = yield from ret

                    if ret is not retry:
                        return ret

        return wrapped

    if fn is None:
        return wrapper

    if callable(fn):
        return wrapper(fn)

    raise NotImplementedError
