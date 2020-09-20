# coding: utf-8

import asyncio
import requests

from retrying_async import retry


def request_api_sync():
    print('正在获取')

    response = requests.get(url="http://www.baidu.com")
    print(response.status_code, response.content)
    raise Exception("异常")


@retry(attempts=3, delay=3)
async def request_api_async():
    print('正在获取')

    response = requests.get(url="http://www.baidu.com")
    print(response.status_code, response.content)
    raise Exception("异常")


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(request_api_async())
