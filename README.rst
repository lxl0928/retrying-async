async_retrying
==============

:info: Simple retrying for asyncio

Installation
------------

.. code-block:: shell

    pip install retrying-async==2.0.0 -i https://pypi.org/pypi

Usage
-----

.. code-block:: python

    import asyncio

    from retrying_async import retry

    counter = 0

    @retry(attempts=3, delay=3)
    async def fn():
        global counter

        counter += 1

        if counter == 1:
            raise RuntimeError

    async def main():
        await fn()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    assert counter == 2

    loop.close()


Python 3.5+ is required
