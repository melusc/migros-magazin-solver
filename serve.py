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

from secrets import token_urlsafe

from flask import Flask, g, render_template
from jinja2 import StrictUndefined

import config
from scrapers.crossword import Arrow, fetch_crossword, layout_crossword
from scrapers.paroli import MatrixFieldType, fetch_and_solve_paroli
from scrapers.quiz import fetch_and_solve_quiz
from scrapers.sudoku import SudokuBorder, fetch_and_parse_sudoku

app = Flask(__name__)
app.config.from_prefixed_env()
app.jinja_env.undefined = StrictUndefined


@app.before_request
def set_nonce():
	g.nonce = token_urlsafe(20)


@app.context_processor
def inject_stage_and_region():
	return {
		"str": str,
		"len": len,
		"int": int,
		"nonce": g.nonce,
		"Arrow": Arrow,
		"isinstance": isinstance,
		"set": set,
		"MatrixFieldType": MatrixFieldType,
		"SudokuBorder": SudokuBorder,
		"enumerate": enumerate,
	}


@app.after_request
def set_headers(response):
	response.headers["Content-Security-Policy"] = "; ".join(
		(
			"default-src 'none'",
			f"style-src-elem 'nonce-{g.nonce}' cdn.jsdelivr.net",
			"style-src-attr 'unsafe-inline'",
		),
	)
	del response.headers["Server"]
	return response


@app.route("/", methods=["GET"])
def index():
	crosswords = None
	crossword_exception = None

	try:
		crosswords = [
			(crossword, *layout_crossword(crossword)) for crossword in fetch_crossword()
		]
	except Exception as e:
		crossword_exception = e

	paroli = None
	paroli_exception = None
	could_solve = False

	try:
		paroli, could_solve = fetch_and_solve_paroli()
	except Exception as e:
		paroli_exception = e

	sudoku = None
	sudoku_exception = None
	try:
		sudoku = fetch_and_parse_sudoku()
	except Exception as e:
		sudoku_exception = e

	quiz_questions = None
	quiz_answers = None
	quiz_exception = None
	try:
		quiz_questions, quiz_answers = fetch_and_solve_quiz()
	except Exception as e:
		quiz_exception = e

	return render_template(
		"index.html",
		crosswords=crosswords,
		crossword_exception=crossword_exception,
		paroli=paroli,
		paroli_solved=could_solve,
		paroli_exception=paroli_exception,
		sudoku=sudoku,
		sudoku_exception=sudoku_exception,
		quiz_questions=quiz_questions,
		quiz_answers=quiz_answers,
		quiz_exception=quiz_exception,
	)


if __name__ == "__main__":
	app.run("127.0.0.1", port=config.port)
