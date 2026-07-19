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

import dataclasses
import json
import re
from enum import Enum

from scrapers.util import get, memoise

_BASE = "https://comhouse.ch/mmagazin/raetsel/schwedenraetsel"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Clue:
	x: int
	y: int
	clue: str
	answer: str
	arrow: Arrow


@dataclasses.dataclass(frozen=True, kw_only=True)
class WinningWordField:
	character: str
	x: int
	y: int
	position: int


class Arrow(Enum):
	BELOW_ACROSS = 1
	ABOVE_ACROSS = 2
	RIGHT_ACROSS = 3
	RIGHT_DOWN = 4
	LEFT_DOWN = 5
	BELOW_DOWN = 6


@dataclasses.dataclass(frozen=True, kw_only=True)
class Crossword:
	clues: list[Clue]
	winning_word: str
	winning_word_fields: list[WinningWordField]


@memoise(ttl=1200)
def _fetch_comhouse_page():
	return get(f"{_BASE}/index.php")


_extract_puzzles_array_re = re.compile(
	r"""
	var\s+puzzles\s*=\s*(?P<array>\[   # var puzzles = [
		(?:\s*"[^"]+"\s*,\s*)*           # any string with trailing comma
		(?:\s*"[^"]+"\s*)?               # final string with absent trailing comma
	\])\s*;
""",
	re.VERBOSE | re.IGNORECASE,
)


def _extract_puzzles_array(page: str) -> list[str]:
	match = re.search(_extract_puzzles_array_re, page)
	if not match:
		raise Exception("Could not parse page.")

	array_raw = match.group("array")
	return json.loads(array_raw)


@memoise(ttl=1200)
def _fetch_puzzle_fcs(name: str):
	return get(f"{_BASE}/puzzles/{name}")


def _parse_fcs(content: str) -> Crossword:
	lines = iter(content.splitlines())

	next(lines)

	answer_grid: list[list[str]] = []

	while "\t" in (line := next(lines)):
		answer_grid.append(line.split("\t"))

	clues: list[Clue] = []

	while "\t" in (line := next(lines)):
		fields = line.split("\t")
		x = int(fields[0]) - 1
		y = int(fields[1]) - 1
		clue = fields[2]
		answer = fields[5]
		arrow = fields[6]

		clues.append(
			Clue(
				x=x,
				y=y,
				clue=clue,
				answer=answer,
				arrow=Arrow(int(arrow)),
			)
		)

	winning_word_length = int(line.removeprefix("Gewinnwortlänge:"))
	line = next(lines)
	winning_word = line[-winning_word_length:]

	winning_word_fields: list[WinningWordField] = []

	winning_word_field_offset = 1
	while "\t" in (line := next(lines)):
		fields = line.split("\t")

		winning_word_fields.append(
			WinningWordField(
				character=fields[0],
				x=int(fields[1]) - 1,
				y=int(fields[2]) - 1,
				position=winning_word_field_offset,
			)
		)

		winning_word_field_offset += 1

	return Crossword(
		clues=clues,
		winning_word=winning_word,
		winning_word_fields=winning_word_fields,
	)


def layout_crossword(
	crossword: Crossword,
) -> tuple[set[tuple[(str | Arrow), int, int]], int, int]:
	items: set[tuple[str | Arrow, int, int]] = set()

	for clue in crossword.clues:
		dir_y = (
			1 if clue.arrow in (Arrow.BELOW_DOWN, Arrow.LEFT_DOWN, Arrow.RIGHT_DOWN) else 0
		)
		dir_x = (
			1
			if clue.arrow in (Arrow.ABOVE_ACROSS, Arrow.BELOW_ACROSS, Arrow.RIGHT_ACROSS)
			else 0
		)
		x = clue.x
		y = clue.y

		items.add((clue.clue, x, y))

		if clue.arrow == Arrow.LEFT_DOWN:
			x -= 1
		elif clue.arrow in (Arrow.RIGHT_ACROSS, Arrow.RIGHT_DOWN):
			x += 1
		elif clue.arrow == Arrow.ABOVE_ACROSS:
			y -= 1
		else:
			y += 1

		items.add((clue.arrow, x, y))

		for c in clue.answer:
			items.add((c, x, y))
			x += dir_x
			y += dir_y

	width = max(x for _, x, _ in items) + 1
	height = max(y for _, _, y in items) + 1

	return items, width, height


def fetch_crossword() -> list[Crossword]:
	comhouse_page = _fetch_comhouse_page()
	puzzles_array = _extract_puzzles_array(comhouse_page)

	return [_parse_fcs(_fetch_puzzle_fcs(puzzle)) for puzzle in puzzles_array]


if __name__ == "__main__":
	for puzzle in fetch_crossword():
		print(puzzle)


__all__ = (
	"Crossword",
	"Arrow",
	"WinningWordField",
	"Clue",
	"fetch_crossword",
	"layout_crossword",
)
