"""Fixed API failure categories, selected from transport facts, never error text."""
import asyncio

import aiohttp


def classify_api_failure(exc=None, status=None):
    if type(status) is int and not 200 <= status < 300:
        return 'rate_limit' if status == 429 else 'http_error'
    if isinstance(exc, asyncio.TimeoutError):
        return 'timeout'
    if isinstance(exc, aiohttp.ClientResponseError) and exc.status >= 400:
        return 'rate_limit' if exc.status == 429 else 'http_error'
    if isinstance(exc, (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError, ConnectionError)):
        return 'network'
    return 'other'
