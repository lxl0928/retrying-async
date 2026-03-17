retrying-async
==============

可配置的 asyncio 异步重试装饰器，支持指数退避、超时、自定义回调等。

Installation
------------

.. code-block:: shell

    pip install retrying-async -i https://pypi.org/pypi

Quick Start
-----------

.. code-block:: python

    import asyncio
    from retrying_async import retry

    @retry(attempts=3, delay=1)
    async def fetch_data():
        response = await some_api_call()
        return response

    asyncio.run(fetch_data())

Basic Usage
----------

.. code-block:: python

    import asyncio
    from retrying_async import retry

    counter = 0

    @retry(attempts=3, delay=2)
    async def fn():
        global counter
        counter += 1
        if counter < 2:
            raise RuntimeError("retry")
        return "ok"

    result = asyncio.run(fn())
    assert result == "ok"
    assert counter == 2

Infinite Retries
----------------

使用 ``INF_ATTEMPTS`` 实现无限重试：

.. code-block:: python

    from retrying_async import retry, INF_ATTEMPTS

    @retry(attempts=INF_ATTEMPTS, delay=1, timeout=30)
    async def poll_until_ready():
        status = await check_status()
        if status != "ready":
            raise RuntimeError("not ready")
        return status

Propagate Original Exception
----------------------------

重试耗尽后传播原始异常而非抛出 ``RetryError``：

.. code-block:: python

    from retrying_async import retry, PROPAGATE_EXCEPTION

    @retry(attempts=3, delay=1, fallback=PROPAGATE_EXCEPTION)
    async def may_fail():
        raise ConnectionError("connection refused")

    # 将抛出 ConnectionError，而非 RetryError
    asyncio.run(may_fail())

Parameters
---------

- **attempts**: 最大重试次数，默认 3；使用 ``INF_ATTEMPTS`` 表示无限重试
- **delay**: 每次重试前的初始等待时间（秒），默认 0.5
- **max_delay**: 延迟上限，默认无限制
- **backoff**: 延迟倍增因子，默认 1
- **jitter**: 额外随机延迟，可为数值或 ``(min, max)`` 元组
- **timeout**: 单次执行的超时时间（秒），仅对协程有效
- **immutable**: 是否在每次重试时深拷贝参数
- **fallback**: 重试耗尽时的处理：``PROPAGATE_EXCEPTION`` 传播异常，异常类则抛出，callable 则调用，否则直接返回
- **retry_exceptions**: 触发重试的异常类型，默认 ``(Exception,)``
- **fatal_exceptions**: 不重试、直接抛出的异常类型，默认 ``(asyncio.CancelledError,)``

Exceptions
---------

- **RetryError**: 所有重试尝试失败后抛出（当 fallback 为默认值时）
- **ConditionError**: 配置错误，如对非协程函数设置 timeout、attempts 参数非法等

Requirements
-----------

- Python 3.7+
- async-timeout_

.. _async-timeout: https://pypi.org/project/async-timeout/

License
-------

MIT
