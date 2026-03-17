# coding: utf-8

import sys
import time
import asyncio
import traceback
from pathlib import Path

# 将项目根目录加入模块搜索路径，便于直接运行测试
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from retrying_async import retry


@retry(attempts=5, delay=3)
async def request_api_async():
    print(f"{int(time.time())}: 200")
    raise Exception("test")


if __name__ == '__main__':
    try:
        asyncio.run(request_api_async())
    except Exception as e:
        # 单独输出异常信息：直接异常用 str(e)，链式异常（如 RetryError）从 __cause__ 取
        print(f"message: {str(e.__cause__) if e.__cause__ else str(e)}, type: {type(e)}")
        print(traceback.format_exc())

"""
1773714364: 200
1773714367: 200
1773714370: 200
1773714373: 200
1773714376: 200
Exception -> Attempts (5) are over for <function request_api_async at 0x10f2e0220>
Traceback (most recent call last):
  File "/retrying-async/retrying_async.py", line 214, in async_wrapped
    return await ret
           ^^^^^^^^^
  File "/retrying-async/tests/run_example.py", line 18, in request_api_async
    raise Exception("test")
Exception: test

message: test, type: <class 'retrying_async.RetryError'>

Traceback (most recent call last):
  File "/retrying-async/retrying_async.py", line 214, in async_wrapped
    return await ret
           ^^^^^^^^^
  File "/retrying-async/tests/run_example.py", line 18, in request_api_async
    raise Exception("test")
Exception: test

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/retrying-async/tests/run_example.py", line 23, in <module>
    asyncio.run(request_api_async())
  File "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/asyncio/base_events.py", line 684, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/retrying-async/retrying_async.py", line 241, in async_wrapped
    return await _handle_fallback(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/retrying-async/retrying_async.py", line 130, in _handle_fallback
    raise fallback from exc
retrying_async.RetryError
"""