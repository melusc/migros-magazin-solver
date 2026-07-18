from os import environ

from dotenv import load_dotenv

load_dotenv()


def _read(key: str) -> str:
	if key not in environ or not environ[key]:
		raise Exception(f"Missing env variable {key}")

	return environ[key]


def _read_int(key: str) -> int:
	return int(_read(key))


port = _read_int("PORT")

__all__ = ("port",)
