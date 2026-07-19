import dataclasses
import re
from enum import Enum
from typing import Any, cast

from scrapers.parse_js import extract_variable
from scrapers.util import get, memoise

_BASE = "https://comhouse.ch/mmagazin/raetsel/paroli/PA_DE"


class MatrixFieldType(Enum):
	Regular = 0
	Nothing = 1


@dataclasses.dataclass(frozen=True, kw_only=True)
class MatrixField:
	type: MatrixFieldType
	solution_position: int | None = None
	value: str | None = None
	x: int
	y: int


class ParoliDirection(Enum):
	Down = 0
	Across = 1


@dataclasses.dataclass(frozen=True, kw_only=True)
class ParoliGame:
	solution_length: int
	matrix: list[list[MatrixField]]
	matrix_width: int
	matrix_height: int
	words: list[str]


@memoise(ttl=1200)
def _fetch_paroli_page() -> str:
	return get(f"{_BASE}/resource/iframe.php")


_extract_script_url_re = re.compile(
	rf"""
	<script\s*src="(?P<url>
		{_BASE.replace(".", r"\.")}/[^"]+   # _BASE/\d+/iframe.js
	)"[^>]*>\s*</script>
""",
	re.IGNORECASE | re.VERBOSE,
)


def _extract_script_url(page: str) -> str:
	match = _extract_script_url_re.search(page)
	if not match:
		raise Exception("Could not extract script url.")

	return match.group("url")


@memoise(ttl=1200)
def _fetch_script(script_url: str) -> str:
	return get(script_url)


def _coerce_ww_game(ww_game: Any) -> ParoliGame:
	if not isinstance(ww_game, dict):
		raise Exception("Expected ww_game to be a dict.")

	if "lsglength" not in ww_game:
		raise Exception('Missing key "lsglength".')

	solution_length = ww_game["lsglength"]
	if not isinstance(solution_length, int):
		raise Exception(
			f'Expected "lsglength" to be an integer, got {type(solution_length)}.'
		)

	if "matrix" not in ww_game:
		raise Exception('Missing key "matrix".')

	matrix = ww_game["matrix"]
	if not isinstance(matrix, list):
		raise Exception(f"Expected matrix to be a list, got {type(matrix)}.")

	for i, row in enumerate(matrix):
		if not isinstance(row, str):
			raise Exception(f"Expected matrix[{i}] to be a string, got {type(row)}.")

	matrix_parsed: list[list[MatrixField]] = []

	matrix_width = -1

	for y, row_ in enumerate(matrix):
		row: str = cast(str, row_)

		matrix_parsed.append([])

		split = row.split(" ")

		if matrix_width == -1:
			matrix_width = len(split)
		if matrix_width != len(split):
			raise Exception("Received matrix with uneven widths.")

		for x, char in enumerate(split):
			if "0" <= char <= "9":
				matrix_parsed[y].append(
					MatrixField(
						type=MatrixFieldType.Regular,
						solution_position=int(char),
						x=x,
						y=y,
					)
				)
			elif char == "n":
				matrix_parsed[y].append(
					MatrixField(
						type=MatrixFieldType.Nothing,
						x=x,
						y=y,
					)
				)
			elif char == "_":
				matrix_parsed[y].append(
					MatrixField(
						type=MatrixFieldType.Regular,
						x=x,
						y=y,
					)
				)
			elif "A" <= char <= "Z":
				matrix_parsed[y].append(
					MatrixField(
						type=MatrixFieldType.Regular,
						value=char,
						x=x,
						y=y,
					)
				)
			else:
				raise Exception(f'Received unexpected character "{char}" in matrix[{y}].')

	if "worddefinition" not in ww_game:
		raise Exception('Missing key "worddefinition".')

	worddefinition = ww_game["worddefinition"]
	if not isinstance(worddefinition, list):
		raise Exception(
			f"Expected worddefinition to be a list, got {type(worddefinition)}."
		)

	words: list[str] = []

	for i, word in enumerate(worddefinition):
		if not isinstance(word, dict):
			raise Exception(f"Expected worddefinition[{i}] to be a dict, got {type(word)}.")

		if "word" not in word:
			raise Exception(f'Missing key "word" in worddefinition[{i}].')

		word_ = word["word"]  # ty:ignore[invalid-argument-type]
		if not isinstance(word_, str):
			raise Exception(
				f'Expected worddefinition[{i}]["cy"] to be a string, got {type(word_)}.'
			)

		words.append(word_)

	return ParoliGame(
		solution_length=solution_length,
		matrix=matrix_parsed,
		matrix_height=len(matrix_parsed),
		matrix_width=matrix_width,
		words=words,
	)


@dataclasses.dataclass(frozen=True, kw_only=True)
class ParoliSlot:
	x: int
	y: int
	length: int
	direction: ParoliDirection


def _find_slots(paroli: ParoliGame):
	word_lengths = set(len(word) for word in paroli.words)

	slots: list[ParoliSlot] = []

	for direction in ParoliDirection.Across, ParoliDirection.Down:
		x = 0
		y = 0

		while x < paroli.matrix_width and y < paroli.matrix_height:
			local_x = x
			local_y = y

			item = paroli.matrix[y][x]

			while item.type == MatrixFieldType.Nothing:
				if direction == ParoliDirection.Down:
					local_y += 1
				else:
					local_x += 1

				item = paroli.matrix[local_y][local_x]

			length = 0

			start_x = local_x
			start_y = local_y

			while (
				local_y < paroli.matrix_height
				and local_x < paroli.matrix_width
				and paroli.matrix[local_y][local_x].type == MatrixFieldType.Regular
			):
				if direction == ParoliDirection.Down:
					local_y += 1
				else:
					local_x += 1

				length += 1

			if length in word_lengths:
				slots.append(
					ParoliSlot(
						x=start_x,
						y=start_y,
						length=length,
						direction=direction,
					)
				)

			if direction == ParoliDirection.Down:
				x += 1
			else:
				y += 1

	return slots


def solve_paroli(paroli: ParoliGame):
	slots = _find_slots(paroli)

	def undo(changes: list[tuple[int, int]]):
		for x, y in changes:
			old = paroli.matrix[y][x]
			paroli.matrix[y][x] = MatrixField(
				type=old.type,
				solution_position=old.solution_position,
				value=None,
				x=x,
				y=y,
			)

	def check_fit(slot: ParoliSlot, word: str) -> tuple[bool, bool]:
		if len(word) != slot.length:
			return False, False

		has_good_fit = False

		x = slot.x
		y = slot.y
		for c in word:
			value = paroli.matrix[y][x].value
			if value is not None and value != c:
				return False, False

			has_good_fit = has_good_fit or value == c

			if slot.direction == ParoliDirection.Across:
				x += 1
			else:
				y += 1

		return True, has_good_fit

	def place_word(slot: ParoliSlot, word: str) -> list[tuple[int, int]]:
		x = slot.x
		y = slot.y

		changes: list[tuple[int, int]] = []

		for c in word:
			old = paroli.matrix[y][x]
			if old.value is None:
				paroli.matrix[y][x] = MatrixField(
					type=old.type,
					solution_position=old.solution_position,
					value=c,
					x=x,
					y=y,
				)

				changes.append((x, y))

			if slot.direction == ParoliDirection.Across:
				x += 1
			else:
				y += 1

		return changes

	def solve(used_words: set[str]) -> list[tuple[int, int]] | None:
		if len(used_words) == len(paroli.words):
			return []

		next_word = next(word for word in paroli.words if word not in used_words)

		good_fits: list[ParoliSlot] = []
		other_fits: list[ParoliSlot] = []

		for slot in slots:
			fits, good_fit = check_fit(slot, next_word)

			if not fits:
				continue

			if good_fit:
				good_fits.append(slot)
			else:
				other_fits.append(slot)

		for slot in good_fits + other_fits:
			changes = place_word(slot, next_word)

			sub_changes = solve({next_word, *used_words})

			if sub_changes is not None:
				return changes + sub_changes

			undo(changes)

		return None

	return solve(set()) is not None


def extract_winning_word(paroli: ParoliGame) -> str:
	result = [" "] * paroli.solution_length

	for row in paroli.matrix:
		for cell in row:
			if cell.solution_position is not None:
				if cell.value is None:
					raise Exception(f"Unexpected empty value in {cell}")

				result[cell.solution_position - 1] = cell.value

	return "".join(result)


def fetch_and_parse() -> ParoliGame:
	iframe_page = _fetch_paroli_page()
	script_url = _extract_script_url(iframe_page)
	script = _fetch_script(script_url)
	ww_game_object = extract_variable(script, "ww_game")
	return _coerce_ww_game(ww_game_object)


def fetch_and_solve_paroli() -> tuple[ParoliGame, bool]:
	paroli = fetch_and_parse()
	could_solve = solve_paroli(paroli)

	return paroli, could_solve


if __name__ == "__main__":
	paroli, could_solve = fetch_and_solve_paroli()

	if could_solve:
		print("Solved\n")

		for row in paroli.matrix:
			print("  " + "".join((c.value or " " for c in row)))

		print(f"\nWinning word: {extract_winning_word(paroli)}")
	else:
		print("Could not solve")
		print(paroli)

__all__ = ("ParoliGame", "fetch_and_solve_paroli", "MatrixFieldType")
