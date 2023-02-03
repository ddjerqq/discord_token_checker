from __future__ import annotations
import os
import random
import base64
import aiohttp
import asyncio as aio
from ua import signed_header
from rgbprint import gradient_print
from aiohttp_socks import ProxyConnector

from src import *


def decode_token(token: str) -> int | None:
    try:
        token = token.strip()
        token = token.split(".")[0]
        id = base64.b64decode(token)
        id = id.decode()
        return int(id)
    except:
        return None


async def check(token: str) -> bool:
    connector = ProxyConnector.from_url(random.choice(PROXIES)) if PROXIES else None
    async with aiohttp.ClientSession(connector=connector) as sesh:
        status = None
        username = None
        valid = False

        async with sesh.get(
            CHECK_URL, 
            headers=signed_header(token),
        ) as resp:
            status = STATUS.get(resp.status, resp.status)
            valid = resp.status == 200

        if BOT_TOKEN is not None and (id := decode_token(token)) is not None:
            async with sesh.get(
                ID_URL.format(id),
                headers=signed_header(token, authorization=f"Bot {BOT_TOKEN}")
            ) as resp:
                data = await resp.json()
                id = data.get("id")
                name = data.get("username")
                discriminator = data.get("discriminator")
                username = f"({id}) {name}#{discriminator}"
        
    gradient_print(
        f"[{status}] {username} {token}", 
        start_color="red", 
        end_color="yellow"
    )

    return valid


async def main():
    futures = [
        check(token)
        for token in TOKENS
    ]
    valids = await aio.gather(*futures, return_exceptions=True)
    good = [
        token
        for valid, token in zip(valids, TOKENS)
        if valid
    ]
    
    with open("valid.txt", "a+") as f:
        f.writelines(good)
    


if __name__ == "__main__":
    aio.run(main())
