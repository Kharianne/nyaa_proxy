import os

try:
    AUTH_TOKEN = os.environ['NYAA_PROXY_AUTH_TOKEN']
except KeyError:
    raise RuntimeError("Env variable missing.")