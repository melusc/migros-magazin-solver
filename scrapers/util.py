from collections.abc import Callable
from time import monotonic

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


class Memoize:
	def __init__(self, f: Callable):
		self.f = f
		self.memo = None
		self.memo_time = 0

	def __call__(self):
		if not self.memo or self.memo_time - monotonic() > 300:
			self.memo = self.f()
			self.memo_time = monotonic()

		return self.memo


__all__ = ("get",)
