import logging
import os
import time
import typing
from functools import wraps

import openai
from dotenv import load_dotenv
from rich.progress import track

def retry(
    exceptions: typing.Type[openai.error.RateLimitError], tries: int = 4, delay: int = 3, back_off: int = 2
) -> typing.Callable:
    def deco_retry(f: typing.Any) -> typing.Callable:
        @wraps(f)
        def f_retry(*args, **kwargs):  # type: ignore
            m_retries, m_delay = tries, delay
            while m_retries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = f"🚨 {e} {os.linesep} "
                    logging.warning(msg)
                    for _ in track(range(m_delay), description="⌛ Retrying in ..."):
                        time.sleep(1)
                    m_retries -= 1
                    m_delay *= back_off
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry