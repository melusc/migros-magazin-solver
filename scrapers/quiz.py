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
from typing import Iterable

from bs4 import BeautifulSoup

from scrapers.german_words import get_words_of_length
from scrapers.util import get, memoise


@memoise(ttl=1200)
def _get_quiz_page() -> str:
	return get("https://comhouse.ch/mmagazin/raetsel/quiz/QU_2024_DE/index.php")


@dataclasses.dataclass(frozen=True, kw_only=True)
class Option:
	key: str
	text: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class Question:
	question: str
	options: list[Option]


def _extract_quiz(page: str) -> list[Question]:
	soup = BeautifulSoup(page, features="html5lib")

	quest = soup.find(id="quest")
	if not quest:
		raise Exception("Could not find element #quest.")

	ol = quest.find("ol")
	if not ol:
		raise Exception("Could not find <ol> element.")

	questions: list[Question] = []

	list_items = ol.find_all("li", recursive=False)
	for q, li in enumerate(list_items):
		question_element = li.find("div", recursive=False)
		if not question_element:
			raise Exception(f"Could not find question #{q}.")
		question = question_element.text.strip()
		if not question:
			raise Exception(f"Question #{q} was empty.")

		options = li.find_all("li")
		# Treat only one or zero as error
		# otherwise be liberal in what we accept
		if len(options) <= 1:
			raise Exception(f'Could not find options to "{question}".')

		options_parsed: list[Option] = []

		for i, option in enumerate(options):
			option_anchor = option.find("a")
			if not option_anchor:
				raise Exception(
					f"Could not find option's anchor in question #{q}, option #{i}."
				)

			children = option_anchor.children
			option_key_element = next(children)
			option_text = next(children)

			if not option_key_element or not option_key_element.text.strip():
				raise Exception(
					f"Could not find option key element in question #{q}, option #{i}."
				)

			option_key_value = option_key_element.text.strip()
			if len(option_key_value) != 1:
				raise Exception(
					f"Option key is not exactly one character in question #{q}, option #{i}."
				)

			if not option_text:
				raise Exception(f"Could not find option text in question #{q}, option #{i}.")

			option_text_value = option_text.text.strip().upper()
			if not option_text_value:
				raise Exception(f"Option value is blank in question #{q}, option #{i}.")

			options_parsed.append(Option(key=option_key_value, text=option_text_value))

		questions.append(
			Question(
				question=question,
				options=options_parsed,
			)
		)

	return questions


def _solve_quiz_prefix(
	prefix: str, questions: list[Question], words: list[str]
) -> Iterable[str]:
	if len(prefix) == len(questions):
		yield prefix
		return

	for option in questions[len(prefix)].options:
		next_prefix = prefix + option.key

		if any(word.startswith(next_prefix) for word in words):
			yield from _solve_quiz_prefix(next_prefix, questions, words)


def _solve_quiz(questions: list[Question]):
	words = get_words_of_length(len(questions))

	# Small optimisation, remove words which don't start
	# with one of the first keys
	first_keys = [option.key for option in questions[0].options]
	words = [word for word in words if word[0] in first_keys]

	answers = list(_solve_quiz_prefix("", questions, words))

	# small hack to still render quiz
	return answers or ["?" * len(questions)]


def fetch_and_solve_quiz() -> tuple[list[Question], list[str]]:
	page = _get_quiz_page()
	questions = _extract_quiz(page)
	return questions, _solve_quiz(questions)


if __name__ == "__main__":
	questions, answers = fetch_and_solve_quiz()

	for a, answer in enumerate(answers):
		if a > 0:
			print()
			print("=" * 10)
			print()

		print(answer + "\n")

		for i, question in enumerate(questions):
			print(question.question)

			for option in question.options:
				if option.key == answer[i]:
					print(f"({option.key}) {option.text}")
				else:
					print(f" {option.key}  {option.text}")

			print()
