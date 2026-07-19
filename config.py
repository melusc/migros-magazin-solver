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

from os import environ

from dotenv import load_dotenv

load_dotenv()


def _read(key: str) -> str:
	if key not in environ or not environ[key]:
		raise Exception(f"Missing env variable {key}")

	return environ[key]


def _read_int(key: str) -> int:
	return int(_read(key))


port = _read_int("PORT")

__all__ = ("port",)
