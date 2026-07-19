from secrets import token_urlsafe

from flask import Flask, g, render_template
from jinja2 import StrictUndefined

import config
from scrapers.crossword import Arrow, fetch_crossword, layout_crossword
from scrapers.paroli import MatrixFieldType, fetch_and_solve_paroli
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
		"layout_crossword": layout_crossword,
		"set": set,
		"MatrixFieldType": MatrixFieldType,
		"SudokuBorder": SudokuBorder,
	}


@app.after_request
def set_headers(response):
	response.headers["Content-Security-Policy"] = "; ".join(
		(
			"default-src 'none'",
			f"style-src-elem 'nonce-{g.nonce}' cdn.jsdelivr.net",
			"style-src-attr 'unsafe-inline'",
			"img-src data:",
		),
	)
	del response.headers["Server"]
	return response


@app.route("/", methods=["GET"])
def index():
	crosswords = None
	crossword_exception = None

	try:
		crosswords = fetch_crossword()
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

	return render_template(
		"index.html",
		crosswords=crosswords,
		crossword_exception=crossword_exception,
		paroli=paroli,
		paroli_solved=could_solve,
		paroli_exception=paroli_exception,
		sudoku=sudoku,
		sudoku_exception=sudoku_exception,
	)


if __name__ == "__main__":
	app.run("127.0.0.1", port=config.port)
