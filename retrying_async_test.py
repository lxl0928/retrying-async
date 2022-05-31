# coding: utf-8

import time
import asyncio

from retrying_async import retry


@retry(attempts=5, delay=3)
async def request_api_async():
    print(f"{int(time.time())}: 200")
    raise Exception


if __name__ == '__main__':

    asyncio.run(request_api_async())
