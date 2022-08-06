from time import perf_counter, sleep

from django.core.cache import cache


def value():
    sleep(5)
    return "value"


def test_memcache():
    request_time = perf_counter()
    cache.get_or_set("key", value(), 100)
    return_time = perf_counter()
    assert return_time - request_time > 5

    request_time = perf_counter()
    cached_value = cache.get("key")
    return_time = perf_counter()
    assert return_time - request_time < 5
    assert cached_value == "value"
