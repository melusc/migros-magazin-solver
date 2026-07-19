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
