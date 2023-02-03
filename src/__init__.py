__all__ = (
    "STATUS",
    "BOT_TOKEN",
    "PATH",
    "CHECK_URL",
    "ID_URL",
    "TOKENS",
    "PROXIES",
)


STATUS = {
    200: "VALID",
    400: "INVALID",
    401: "INVALID",
    403: "LOCKED",
}

BOT_TOKEN = ""
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECK_URL = "https://discord.com/api/v8/users/@me"
ID_URL = "https://discord.com/api/v9/users/{id}"

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