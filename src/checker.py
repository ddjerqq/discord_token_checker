from __future__ import annotations

import os
import enum
import base64
import asyncio as aio

import aiohttp
from aiohttp_socks import ProxyConnector
from rgbprint import gradient_print

from ua import signed_header


class TokenStatus(enum.Enum):
    __data__: int | Exception
    VALID = "VALID"
    BAD_REQUEST = "BAD REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    LOCKED = "LOCKED"
    UNKNOWN = "UNKNOWN"
    THROTTLED = "THROTTLED"
    ERROR = "ERROR"

    def print(self, token: str) -> bool:
        if self == TokenStatus.VALID:
            gradient_print(f"[{self.value}] {token}", start_color="green", end_color="yellow")
            return True
        else:
            gradient_print(f"[{self.value}] {token}", start_color="red", end_color="yellow")

        return False


class IdStatus(enum.Enum):
    __data__: str | int | Exception = ""
    BOT_TOKEN_NOT_FOUND = "BOT TOKEN NOT FOUND"
    VALID = "VALID"
    INVALID_TOKEN = "INVALID TOKEN"
    BAD_REQUEST = "BAD REQUEST"
    THROTTLED = "THROTTLED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

    def print(self, token: str) -> bool:
        if self == IdStatus.VALID:
            gradient_print(f"[{self.value}] {token} {self.__data__}", start_color="green", end_color="yellow")
            return True
        else:
            gradient_print(f"[{self.value}] {token} {self.__data__}", start_color="red", end_color="yellow")

        return False


class Checker:
    _PROXY = None  # "YOUR PROXY HERE"
    _BOT_TOKEN = None  # "YOUR BOT TOKEN HERE"
    _CHECK_URL = f"https://discord.com/api/v8/users/@me"
    _ID_URL = "https://discord.com/api/v8/users/{id}"

    def __init__(self) -> None:
        # find tokens.txt in the current dir, or one dir up, or two dirs up
        # if not found, raise FileNotFoundError

        for i in range(3):
            path = os.path.join(*([".."] * i + ["tokens.txt"]))
            if os.path.exists(path):
                token_path = path
                break
        else:
            raise FileNotFoundError("tokens.txt not found. does it exist?")

        self.tokens: list[str] = [
            line.strip()
            for line in open(token_path)
            if not line.startswith("#")
        ]

    @staticmethod
    def _decode_token(token: str) -> int | None:
        try:
            token = token.strip()
            token = token.split(".")[0]
            id = base64.b64decode(token)
            id = id.decode()
            return int(id)
        except:
            return None

    async def _check_token(self, session: aiohttp.ClientSession, token: str) -> TokenStatus:
        try:
            async with session.get(self._CHECK_URL, headers=signed_header(token)) as resp:
                if resp.status == 200:
                    return TokenStatus.VALID
                elif resp.status == 400:
                    return TokenStatus.BAD_REQUEST
                elif resp.status == 401:
                    return TokenStatus.UNAUTHORIZED
                elif resp.status == 403:
                    return TokenStatus.LOCKED
                elif resp.status == 429:
                    return TokenStatus.THROTTLED
                else:
                    status = TokenStatus.UNKNOWN
                    status.__data__ = resp.status
                    return status
        except Exception as e:
            status = TokenStatus.ERROR
            status.__data__ = e
            return status

    async def _check_id(self, session: aiohttp.ClientSession, token: str) -> IdStatus:
        id = self._decode_token(token)

        if id is None:
            return IdStatus.BOT_TOKEN_NOT_FOUND

        url = self._ID_URL.format(id=id)
        headers = signed_header(token, authorization=f"Bot {self._BOT_TOKEN}")

        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    status = IdStatus.VALID

                    data = await resp.json()
                
                    id = data.get("id", None)
                    name = data.get("username", "bot account")
                    discriminator = data.get("discriminator", None)

                    if id is None or discriminator is None:
                        status.__data__ = name
                    else:
                        status.__data__ = f"({id}) {name}#{discriminator}"

                    return status

                elif resp.status == 400:
                    return IdStatus.INVALID_TOKEN
                
                elif resp.status == 429:
                    return IdStatus.THROTTLED
                
                else:
                    status = IdStatus.UNKNOWN
                    status.__data__ = resp.status
                    return status

        except Exception as e:
            status = IdStatus.ERROR
            status.__data__ = e
            return status

    async def check(self, token: str) -> bool:
        connector = ProxyConnector.from_url(self._PROXY)
        async with aiohttp.ClientSession(connector=connector) as sesh:
            token_status = await self._check_token(sesh, token)
            valid = token_status.print(token)

            if self._BOT_TOKEN is not None:
                id_status = await self._check_id(sesh, token)
                id_status.print(token)

            return valid

    async def __call__(self) -> None:
        futures = [self.check(token) for token in self.tokens]
        valids = await aio.gather(*futures, return_exceptions=True)

        good = [token for valid, token in zip(valids, self.tokens) if valid]
        errs = [err for err in valids if isinstance(err, Exception)]

        gradient_print(f"success: {len(good)}", start_color="green", end_color="yellow")
        for err in errs:
            gradient_print(f"[ERROR]: {err}", start_color="red", end_color="yellow")

        with open("valid.txt", "w") as f:
            f.write("\n".join(good) + "\n")
        
        gradient_print("saved valid tokens to valid.txt", start_color="green", end_color="yellow")
