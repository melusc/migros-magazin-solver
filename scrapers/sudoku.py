import dataclasses
import re
from enum import Enum
from typing import Any

from scrapers.parse_js import extract_variable
from scrapers.util import get, memoise

_BASE = "https://comhouse.ch/mmagazin/raetsel"


@memoise(ttl=1200)
def _fetch_sudoku_page() -> str:
	return get(f"{_BASE}/index-sudoku-de.php")


_script_url_re = re.compile(r"<script\s+src=\"(?P<url>sudoku/[^\"]+)\"", re.IGNORECASE)


def _extract_script_url(page: str) -> str:
	match = _script_url_re.search(page)

	if not match:
		raise Exception("Could not extract script url from sudoku page.")

	return match.group("url")


@memoise(ttl=1200)
def _fetch_script(script_url: str) -> str:
	return get(f"{_BASE}/{script_url}")


class SudokuBorder(Enum):
	Top = 0
	Left = 1
	Bottom = 2
	Right = 3


@dataclasses.dataclass(frozen=True, kw_only=True)
class SudokuCell:
	value: int
	x: int
	y: int
	is_winning_field: bool
	thick_borders: set[SudokuBorder]


@dataclasses.dataclass(frozen=True, kw_only=True)
class Sudoku:
	dim_x: int
	dim_y: int
	cells: list[list[SudokuCell]]


def _coerce_sudoku(ww_game: Any) -> Sudoku:
	if not isinstance(ww_game, dict):
		raise Exception(f'Expected "ww_game" to be a dict, got {type(ww_game)}.')

	if "dimx" not in ww_game:
		raise Exception('Missing key "dimx" in ww_game.')

	dim_x_raw = ww_game["dimx"]
	if not isinstance(dim_x_raw, str):
		raise Exception(f"Expected dimx to be a string, got {type(dim_x_raw)}.")

	try:
		dim_x = int(dim_x_raw)
	except ValueError:
		raise Exception(f"Expected dimx to be a string-encoded integer, got {dim_x_raw}.")

	if "dimy" not in ww_game:
		raise Exception('Missing key "dimy" in ww_game.')

	dim_y_raw = ww_game["dimy"]
	if not isinstance(dim_y_raw, str):
		raise Exception(f"Expected dimy to be a string, got {type(dim_y_raw)}.")

	try:
		dim_y = int(dim_y_raw)
	except ValueError:
		raise Exception(f"Expected dimy to be a string-encoded integer, got {dim_y_raw}.")

	if "formmatrix" not in ww_game:
		raise Exception('Missing key "formmatrix" in ww_game.')

	form_matrix = ww_game["formmatrix"]
	if not isinstance(form_matrix, list):
		raise Exception(f"Expected formmatrix to be a list, got {type(form_matrix)}.")

	if len(form_matrix) != dim_y:
		raise Exception(
			f"Expected formmatrix to have {dim_y} rows, got {len(form_matrix)} rows."
		)

	form_matrix_parsed: list[list[str]] = []

	for i, row in enumerate(form_matrix):
		if not isinstance(row, str):
			raise Exception(f"Expected formmatrix[{i}] to be a string, got {type(row)}.")

		split = row.split(" ")
		if len(split) != dim_x:
			raise Exception(
				f"Expected formmatrix[{i}] to have {dim_x} columns, got {len(split)} columns."
			)

		form_matrix_parsed.append(split)

	if "matrix" not in ww_game:
		raise Exception('Missing key "matrix" in ww_game.')

	matrix = ww_game["matrix"]
	if not isinstance(matrix, list):
		raise Exception(f"Expected matrix to be a list, got {type(matrix)}.")

	if len(matrix) != dim_y:
		raise Exception(f"Expected matrix to have {dim_y} rows, got {len(matrix)} rows.")

	if "show_Winfields" not in ww_game:
		raise Exception('Missing key "show_Winfields" in ww_game.')

	win_fields_raw = ww_game["show_Winfields"]
	if not isinstance(win_fields_raw, list):
		raise Exception(
			f"Expected show_Winfields to be a list, got {type(win_fields_raw)}."
		)

	win_fields: set[tuple[int, int]] = set()
	for i, item in enumerate(win_fields_raw):
		if not isinstance(item, dict):
			raise Exception(f"Expected show_Winfields[{i}] to be a dict, got {type(item)}.")

		if "x" not in item:
			raise Exception(f'Missing key "x" in show_Winfields[{i}].')

		x = item["x"]  # ty:ignore[invalid-argument-type]
		if not isinstance(x, int):
			raise Exception(
				f'Expected show_Winfields[{i}]["x"] to be an integer, got {type(x)}.'
			)

		if "y" not in item:
			raise Exception(f'Missing key "x" in show_Winfields[{i}].')

		y = item["y"]  # ty:ignore[invalid-argument-type]
		if not isinstance(y, int):
			raise Exception(
				f'Expected show_Winfields[{i}]["y"] to be an integer, got {type(y)}.'
			)

		win_fields.add((x - 1, y - 1))

	sudoku_cells: list[list[SudokuCell]] = []

	for y, row in enumerate(matrix):
		if not isinstance(row, str):
			raise Exception(f"Expected matrix[{i}] to be a string, got {type(row)}.")

		split = row.split(" ")
		if len(split) != dim_x:
			raise Exception(
				f"Expected matrix[{i}] to have {dim_x} columns, got {len(split)} columns."
			)

		sudoku_cells.append([])

		for x, cell in enumerate(iterable=split):
			try:
				cell_parsed = int(cell)
			except ValueError:
				raise Exception(
					f"Expected matrix[{i}][{x}] to be a string-encoded integer, got {cell}."
				)

			cell_form = form_matrix_parsed[y][x]
			thick_borders: set[SudokuBorder] = set()
			if x == 0:
				thick_borders.add(SudokuBorder.Left)
			if x == dim_x - 1 or form_matrix_parsed[y][x + 1] != cell_form:
				thick_borders.add(SudokuBorder.Right)
			if y == 0:
				thick_borders.add(SudokuBorder.Top)
			if y == dim_y - 1 or form_matrix_parsed[y + 1][x] != cell_form:
				thick_borders.add(SudokuBorder.Bottom)

			sudoku_cells[y].append(
				SudokuCell(
					value=cell_parsed,
					x=x,
					y=y,
					is_winning_field=(x, y) in win_fields,
					thick_borders=thick_borders,
				)
			)

	return Sudoku(dim_x=dim_x, dim_y=dim_y, cells=sudoku_cells)


def fetch_and_parse_sudoku() -> Sudoku:
	page = _fetch_sudoku_page()
	script_url = _extract_script_url(page)
	script = _fetch_script(script_url)
	ww_game = extract_variable(script, "ww_game")
	return _coerce_sudoku(ww_game)


if __name__ == "__main__":
	sudoku = fetch_and_parse_sudoku()
	for row in sudoku.cells:
		GREEN = "\033[92m"
		END = "\033[0m"

		print(
			" ".join(
				(
					f"{GREEN}{cell.value}{END}" if cell.is_winning_field else str(cell.value)
					for cell in row
				)
			)
		)

__all__ = ("fetch_and_parse_sudoku", "SudokuBorder")
