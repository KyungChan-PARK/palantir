from cachetools import LRUCache


def get_cache(size=128):
    return LRUCache(maxsize=size)
