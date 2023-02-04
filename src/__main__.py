import asyncio as aio

from checker import Checker


async def main():
    checker = Checker()
    await checker()


if __name__ == "__main__":
    aio.run(main())
