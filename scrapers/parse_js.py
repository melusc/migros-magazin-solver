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

import ast
import re
from typing import Any


def extract_variable(script: str, variable: str) -> Any:
	_var_declaration = re.compile(rf"var {variable}\s*=\s*")
	start = _var_declaration.search(script)
	if not start:
		raise Exception(f"Could not find var {variable} declaration.")

	offset = start.end()

	def parse_string():
		nonlocal offset

		start = offset
		offset += 1

		while script[offset] != script[start]:
			offset += 1

		eat(script[start])
		end = offset

		eat_unused()

		return ast.literal_eval(script[start:end])

	def eat(expected: str):
		nonlocal offset

		if script[offset] != expected:
			raise Exception(f'Expected "{expected}" but got "{script[offset]}".')

		offset += 1

	def eat_unused():
		start = -1

		while offset != start:
			start = offset

			eat_comment()
			eat_whitespace()

	def eat_whitespace():
		nonlocal offset

		while script[offset].strip() == "":
			offset += 1

	def eat_comment():
		nonlocal offset

		if script[offset] == script[offset + 1] == "/":
			offset += 2

			while script[offset] not in ("\n", "\r"):
				offset += 1

			eat_whitespace()

	def parse_float():
		nonlocal offset

		start = offset
		offset += 1

		while "0" <= script[offset] <= "9" or script[offset] == ".":
			offset += 1

		eat_unused()

		return ast.literal_eval(script[start:offset])

	def parse_array():
		nonlocal offset

		result = []

		eat("[")
		eat_unused()

		while script[offset] != "]":
			result.append(parse_literal())

			eat_unused()
			if script[offset] == ",":
				eat(",")
				eat_unused()

		eat("]")
		eat_unused()

		return result

	def parse_object():
		nonlocal offset

		result = {}

		eat("{")

		eat_unused()
		while script[offset] != "}":
			key = ""

			if script[offset] in ('"', "'"):
				key = parse_string()
			else:
				start = offset

				while script[offset].strip() not in ("", ":"):
					offset += 1

				key = script[start:offset]

			eat_unused()
			eat(":")
			eat_unused()

			result[key] = parse_literal()

			eat_unused()
			if script[offset] == ",":
				eat(",")
				eat_unused()

		eat("}")

		return result

	def parse_literal():
		eat_whitespace()

		char = script[offset]
		if char in ('"', "'"):
			return parse_string()

		if char == "{":
			return parse_object()

		if char == "[":
			return parse_array()

		if "0" <= char <= "9":
			return parse_float()

		raise Exception(f'Unknown literal "{char}".')

	eat_unused()
	return parse_literal()


__all__ = ("extract_variable",)
