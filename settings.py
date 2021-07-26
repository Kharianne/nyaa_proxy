import os

try:
    AUTH_TOKEN = os.environ['NYAA_PROXY_AUTH_TOKEN']
except KeyError:
    raise RuntimeError("NYAA_PROXY_AUTH_TOKEN missing.")
