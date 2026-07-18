from secrets import token_urlsafe

from flask import Flask, g, render_template
from jinja2 import StrictUndefined

import config
from scrapers.crossword import Arrow, fetch_crossword, layout_crossword

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
		"nonce": g.nonce,
		"Arrow": Arrow,
		"isinstance": isinstance,
		"layout_crossword": layout_crossword,
		"set": set,
	}


@app.after_request
def set_headers(response):
	response.headers["Content-Security-Policy"] = "; ".join(
		(
			"default-src 'none'",
			f"script-src 'nonce-{g.nonce}'",
			f"style-src-elem 'nonce-{g.nonce}' cdn.jsdelivr.net",
			"style-src-attr 'unsafe-inline'",
			"img-src data:",
			"font-src cdn.jsdelivr.net",
			"connect-src 'self'",
		),
	)
	del response.headers["Server"]
	return response


@app.route("/", methods=["GET"])
def index():
	crosswords = fetch_crossword()

	return render_template("index.html", crosswords=crosswords)


if __name__ == "__main__":
	app.run("127.0.0.1", port=config.port)
