# coding: utf-8

import time
import asyncio

from retrying_async import retry


@retry(attempts='infinite', delay=3, timeout=60)
async def a():
    await b()
    while True:
        try:
            print(f"{int(time.time())}: Hi...")
            await asyncio.sleep(1)
        except Exception as exception:
            print(type(exception))
            print("Exception encountered")
            raise exception


async def b():
    print("hi")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(a())
    asyncio.run(a())
