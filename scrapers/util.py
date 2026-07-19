import functools
from collections.abc import Callable
from time import monotonic
from typing import ParamSpec, TypeVar

import requests


def get(url: str) -> str:
	return requests.get(
		url,
		headers={
			# Blend in with Firefox
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"Accept-Language": "de-CH,en;q=0.9",
			"Referer": "https://magazine.migros.ch/",
			"Sec-Fetch-Dest": "iframe",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "cross-site",
			"Sec-Fetch-Storage-Access": "none",
			"Sec-GPC": "1",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
		},
	).text


P = ParamSpec("P")
# TypeVar captures the return type
R = TypeVar("R")


def memoise(*, ttl: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
	def decorator(f: Callable[P, R]) -> Callable[P, R]:
		memo: R | None = None
		memo_time = 0
		last_args = ()
		last_kwargs = {}

		@functools.wraps(f)
		def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
			nonlocal memo, memo_time, last_args, last_kwargs

			now = monotonic()

			if (
				not memo or now - memo_time > ttl or args != last_args or kwargs != last_kwargs
			):
				memo = f(*args, **kwargs)
				memo_time = now
				last_args = args
				last_kwargs = kwargs

			return memo

		return wrapper

	return decorator


__all__ = ("get", "memoise")
