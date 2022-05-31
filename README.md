# retrying_async

# Install 

```
 pip install retrying-async==2.0.0 -i https://pypi.org/pypi
```

# Example

```
# coding: utf-8

import time
import asyncio

from retrying_async import retry


@retry(attempts=5, delay=3)
async def request_api_async():
    print(f"{int(time.time())}: 200")
    raise Exception


if __name__ == '__main__':

    asyncio.run(request_api_async())  # retry

```

# Example Output

```
1654007336: 200
1654007339: 200
1654007345: 200
1654007354: 200
1654007366: 200

Exception -> Attempts (5) are over for <function request_api_async at 0x1042e3598>
Traceback (most recent call last):
  File "retrying_async.py", line 101, in wrapped
    ret = yield from ret
  File "retrying_async_test.py", line 12, in request_api_async
    raise Exception
Exception
Traceback (most recent call last):
  File "retrying_async.py", line 101, in wrapped
    ret = yield from ret
  File "retrying_async_test.py", line 12, in request_api_async
    raise Exception
Exception

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "retrying_async_test.py", line 17, in <module>
    asyncio.run(request_api_async())
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/asyncio/runners.py", line 43, in run
    return loop.run_until_complete(main)
  File "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.7/lib/python3.7/asyncio/base_events.py", line 584, in run_until_complete
    return future.result()
  File "retrying_async.py", line 131, in wrapped
    raise fallback from exc
retrying_async.RetryError
```

