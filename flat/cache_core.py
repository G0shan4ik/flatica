from ast import literal_eval
from functools import cache

import diskcache
from loguru import logger


class CacheCore:
    def __init__(self, cache_name: str = 'flatica'):
        self.cache = diskcache.Cache(cache_name)

    def add_unique_data(self, url: str, data: dict) -> bool:
        if url in self.cache:
            logger.warning(f'THIS  --- Flat URL ---  already exists;  { url }')
            return False

        self.cache[url] = data
        logger.success(f'ADD UNIQUE DATA;  { url }')
        return True

    def get_full_cache_info(self):
        mass: list[dict] = []

        for url in self.cache:
            add_dct = dict()
            for k, v in self.cache[url].items():
                add_dct[k] = v
            mass.append(
                {
                    url: add_dct
                }
            )

        return mass

    def get_all_urls(self) -> list[str]:
        _mass = []
        for url in self.cache:
            _mass.append(url)
        return _mass

    def get_len_cache(self) -> int:
        try:
            cnt = 0
            for _ in self.cache:
                cnt += 1

            return cnt
        except:
            return -1

    def delete_data(self, url: str) -> bool:
        if url in self.cache:
            del self.cache[url]
            logger.success(f'DATA DELETED; {url}')
            return True
        else:
            logger.warning(f'DATA NOT FOUND; {url}')
            return False