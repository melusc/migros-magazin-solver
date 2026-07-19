# This file is part of Migros Magazin Solver (https://github.com/melusc/migros-magazin-solver)
# Copyright (C) 2026  Luca Schnellmann <oss@lusc.ch>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
