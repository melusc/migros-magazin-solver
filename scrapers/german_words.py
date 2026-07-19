import functools
import unicodedata
from collections.abc import Iterator
from pathlib import Path

from scrapers.util import get

_URL = "https://gist.github.com/MarvinJWendt/2f4f4154b8ae218600eb091a5706b5f4/raw/36b70dd6be330aa61cd4d4cdfda6234dcb0b8784/wordlist-german.txt"


def _download_wordlist() -> str:
	return get(_URL)


def _get_words() -> Iterator[str]:
	words = _download_wordlist()

	for line in words.splitlines():
		word = unicodedata.normalize("NFC", line.strip()).upper()
		if word:
			yield word


_wordlist_directory = Path(__file__).parent.parent / ".wordlists-german"

@functools.cache
def get_words_of_length(length: int) -> list[str]:
	_wordlist_directory.mkdir(exist_ok=True)

	wordlist = _wordlist_directory / f"{length}.txt"

	if wordlist.exists():
		with wordlist.open() as f:
			return list(f)

	result = [word for word in _get_words() if len(word) == length]
	with wordlist.open("w") as f:
		f.write("\n".join(result))

	return result


__all__ = ("get_words", "get_words_of_length")
