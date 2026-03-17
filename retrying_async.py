# -*- coding: utf-8 -*-
"""异步重试装饰器，为 asyncio 协程提供可配置的重试机制。"""

import asyncio
import copy
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, Union

import async_timeout

__version__ = '3.0.0'
logger = logging.getLogger(__name__)

# 特殊标记：PROPAGATE_EXCEPTION 表示传播原始异常，INF_ATTEMPTS 表示无限重试
PROPAGATE_EXCEPTION = ...
INF_ATTEMPTS = ...

# 重试继续标记（用于 callback 返回值）
_RETRY_SENTINEL = object()


class RetryError(Exception):
    """所有重试尝试失败后抛出的异常。"""

    pass


class ConditionError(Exception):
    """配置条件错误。"""

    pass


def _unpartial(fn: Callable) -> Callable:
    """解析 functools.partial 包装，获取原始函数。"""
    while hasattr(fn, 'func'):
        fn = fn.func
    return fn


def _is_exception(obj: Any) -> bool:
    """判断对象是否为异常类或异常实例。"""
    return isinstance(obj, Exception) or (
        isinstance(obj, type) and issubclass(obj, Exception)
    )


async def _default_callback(
    attempt: int,
    exc: Exception,
    args: tuple,
    kwargs: dict,
    delay: float = 0.5,
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> object:
    """默认回调：等待指定时间后继续重试。

    Args:
        attempt: 当前尝试次数。
        exc: 捕获的异常。
        args: 被装饰函数的 positional 参数。
        kwargs: 被装饰函数的 keyword 参数。
        delay: 等待秒数。
        loop: 事件循环（已弃用，保留以兼容旧版 callback 签名）。

    Returns:
        _RETRY_SENTINEL 表示继续重试。
    """
    await asyncio.sleep(delay)
    return _RETRY_SENTINEL


def _compute_retry_exceptions(
    timeout: Optional[float],
    retry_exceptions: Tuple[Type[Exception], ...],
) -> Tuple[Type[Exception], ...]:
    """计算实际的重试异常元组（含 TimeoutError）。"""
    if timeout is None or asyncio.TimeoutError in retry_exceptions:
        return retry_exceptions
    return (asyncio.TimeoutError,) + retry_exceptions


def _compute_next_delay(
    delay: float,
    backoff: float,
    jitter: Union[float, Tuple[float, float]],
    max_delay: Optional[float],
) -> float:
    """计算下一次重试的延迟时间。"""
    next_delay = delay * backoff + (
        random.uniform(*jitter) if isinstance(jitter, tuple) else jitter
    )
    return min(next_delay, max_delay) if max_delay is not None else next_delay


def _is_infinite_attempts(attempts: Any) -> bool:
    """判断是否为无限重试（INF_ATTEMPTS）。"""
    return attempts is INF_ATTEMPTS


def _validate_attempts(attempts: Any) -> None:
    """校验 attempts 参数，非法时抛出 ConditionError。"""
    if attempts is INF_ATTEMPTS or isinstance(attempts, (int, float)):
        return
    raise ConditionError(
        f"attempts 必须为整数或 INF_ATTEMPTS，当前值: {attempts!r}"
    )


def _should_stop_retrying(
    attempt: int,
    attempts: Union[int, float, object],
    loop: asyncio.AbstractEventLoop,
) -> bool:
    """判断是否应停止重试（已达最大次数或 debug 模式）。"""
    return (
        loop.get_debug()
        or (not _is_infinite_attempts(attempts) and attempt >= attempts)
    )


async def _handle_fallback(
    fallback: Any,
    fn_args: tuple,
    fn_kwargs: dict,
    exc: Exception,
    fn: Callable,
) -> Any:
    """处理 fallback：传播异常、抛出或返回 fallback 结果。"""
    if fallback is PROPAGATE_EXCEPTION:
        raise exc

    if _is_exception(fallback):
        raise fallback from exc

    if callable(fallback):
        ret = fallback(fn_args, fn_kwargs)
        if asyncio.iscoroutine(ret):
            return await ret
        return ret

    return fallback


def retry(
    *,
    fn: Optional[Callable] = None,
    attempts: Union[int, object] = 3,
    delay: float = 0.5,
    max_delay: Optional[float] = None,
    backoff: float = 1,
    jitter: Union[float, Tuple[float, float]] = 0,
    timeout: Optional[float] = None,
    immutable: bool = False,
    callback: Callable = _default_callback,
    fallback: Any = RetryError,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    fatal_exceptions: Tuple[Type[BaseException], ...] = (asyncio.CancelledError,),
    logger_instance: Optional[logging.Logger] = None,
) -> Callable:
    """为异步函数添加可配置的重试逻辑。

    支持作为无参装饰器 @retry() 或带参装饰器 @retry(attempts=5, delay=1)。

    Args:
        fn: 被装饰的函数（由装饰器自动传入）。
        attempts: 最大重试次数，使用 "INF_ATTEMPTS" 表示无限重试, 任意整数表示最大重试次数。
        delay: 每次重试前的初始等待时间（秒）。
        max_delay: 延迟上限，None 表示无限制。
        backoff: 延迟倍增因子。
        jitter: 额外随机延迟，可为数值或 (min, max) 元组。
        timeout: 单次执行的超时时间（秒），仅对协程有效。
        immutable: 是否在每次重试时深拷贝参数。
        callback: 重试前的回调；返回特定标记表示继续重试，否则提前结束并返回该值。
        fallback: 重试耗尽时的处理：PROPAGATE_EXCEPTION 传播异常，
            Exception 子类则抛出，callable 则调用并返回其结果，否则直接返回。
        retry_exceptions: 触发重试的异常类型。
        fatal_exceptions: 不重试、直接抛出的异常类型。
        logger_instance: 日志记录器，None 则使用模块默认 logger。

    Returns:
        装饰后的函数。

    Raises:
        ConditionError: 对非协程函数设置 timeout 时。
    """

    _validate_attempts(attempts)
    _logger = logger_instance or logger
    _retry_exceptions = _compute_retry_exceptions(timeout, retry_exceptions)
    _callback_is_coro = asyncio.iscoroutinefunction(_unpartial(callback))

    def decorator(wrapped_fn: Callable) -> Callable:
        _wrapped_is_coro = asyncio.iscoroutinefunction(_unpartial(wrapped_fn))
        if timeout is not None and not _wrapped_is_coro:
            raise ConditionError("Can't set timeout for non coroutine function")

        @wraps(wrapped_fn)
        async def async_wrapped(*fn_args: Any, **fn_kwargs: Any) -> Any:
            loop = asyncio.get_running_loop()
            current_attempt, current_delay = 1, delay

            while True:
                _args, _kwargs = (
                    (copy.deepcopy(fn_args), copy.deepcopy(fn_kwargs))
                    if immutable
                    else (fn_args, fn_kwargs)
                )

                try:
                    ret = wrapped_fn(*_args, **_kwargs)
                    if not _wrapped_is_coro:
                        return ret
                    if timeout is None:
                        return await ret
                    async with async_timeout.timeout(timeout):
                        return await ret

                except ConditionError:
                    raise
                except fatal_exceptions:
                    raise
                except _retry_exceptions as exc:
                    context = {
                        'fn': wrapped_fn,
                        'attempt': current_attempt,
                        'attempts': 'INF_ATTEMPTS' if _is_infinite_attempts(attempts) else str(attempts),
                    }

                    if _should_stop_retrying(current_attempt, attempts, loop):
                        _logger.warning(
                            exc.__class__.__name__
                            + ' -> Attempts (%(attempt)d) are over for %(fn)r',
                            context,
                            exc_info=exc,
                        )
                        return await _handle_fallback(
                            fallback, fn_args, fn_kwargs, exc, wrapped_fn
                        )

                    _logger.debug(
                        exc.__class__.__name__
                        + ' -> Tried attempt #%(attempt)d from total %(attempts)s for %(fn)r',
                        context,
                        exc_info=exc,
                    )

                    callback_ret = callback(
                        current_attempt, exc, fn_args, fn_kwargs,
                        delay=current_delay, loop=loop,
                    )
                    current_delay = _compute_next_delay(
                        current_delay, backoff, jitter, max_delay
                    )
                    current_attempt += 1

                    if _callback_is_coro:
                        callback_ret = await callback_ret

                    if callback_ret not in (_RETRY_SENTINEL, retry):
                        return callback_ret

        return async_wrapped

    if fn is None:
        return decorator
    if callable(fn):
        return decorator(fn)
    raise TypeError('retry() requires a callable or None')
