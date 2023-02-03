from __future__ import annotations
import os
import random

import aiohttp
from aiohttp_socks import ProxyConnector
import asyncio as aio
from ua import signed_header
from rgbprint import gradient_print


STATUS = {
    200: (lambda token: gradient_print(f"[VALID] {token}", start_color="green", end_color="cyan"), True),
    400: (lambda token: gradient_print(f"[BAD REQUEST] {token}", start_color="red", end_color="pink"), False),
    401: (lambda token: gradient_print(f"[INVALID] {token}", start_color="red", end_color="green"), False),
    403: (lambda token: gradient_print(f"[LOCKED] {token}", start_color="blue", end_color="red"), False),
}


PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_URL = f"https://discord.com/api/v8/users/@me"
TOKENS = [
    line.strip()
    for line in open(os.path.join(PATH, "tokens.txt"))
    if not line.startswith("#")
]
PROXIES = [
    f"http://{line.strip()}"
    for line in open(os.path.join(PATH, "proxy.txt"))
    if not line.startswith("#")
]


async def check(token: str) -> bool:
    if PROXIES:
        connector = ProxyConnector.from_url(random.choice(PROXIES))
    else:
        connector = None
    
    async with aiohttp.ClientSession(connector=connector) as sesh:
        try:
            async with sesh.get(
                CHECK_URL, 
                headers=signed_header(token),
                timeout=15,
            ) as resp:
                status, valid = STATUS.get(resp.status, (None, None))

                if status is not None and valid is not None:
                    status(token)
                    return valid

                else:
                    gradient_print(
                        f"[UNKNOWN STATUS CODE] {token} {resp.status}", 
                        start_color="red", 
                        end_color="yellow"
                    )
        except Exception as e:
            gradient_print(
                f"[UNKNOWN ERROR] {token} {e}",
                start_color="red", 
                end_color="yellow"
            )
        finally:
            return False


async def main():
    futures = [
        check(token)
        for token in TOKENS
    ]
    valids = await aio.gather(*futures)
    good = [
        token
        for valid, token in zip(valids, TOKENS)
        if valid
    ]
    
    with open("valid.txt", "a+") as f:
        f.writelines(good)
    


if __name__ == "__main__":
    aio.run(main())
