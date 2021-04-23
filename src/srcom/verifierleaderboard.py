#!/usr/bin/env python3.9

import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from operator import attrgetter
from os import chdir
from os.path import dirname
from sys import argv, exit, stderr
from typing import Literal

from utils import *

USAGE: Literal[str] = (
	"Usage: `+verifierleaderboard [GAME] [GAME (Optional)]`\n"
	+ "Example: `+verifierleaderboard mkw mkwextracategories`"
)


class Moderator:
	def __init__(self, name: str) -> None:
		self.name = name
		self.examined = 0

	def __eq__(self, other) -> bool:
		return self.name == other.name

	def __ne__(self, other) -> bool:
		return not self.__eq__(other)

	def __hash__(self) -> int:
		return hash(self.name)


def routine(mod: Moderator) -> None:
	# Got to stay safe
	cmd = shlex.join(["./verified", mod.name, *argv[1:]]).split()

	result = subprocess.run(cmd, capture_output=True, text=True)
	if result.returncode != EXIT_SUCCESS:
		error_and_die(result.stderr)

	mod.examined = int(result.stdout.split()[1])


def get_examined(mods: set[Moderator]) -> None:
	"""
	Get the amount of runs examined by each moderator.
	"""
	with ThreadPoolExecutor(max_workers=len(mods)) as executor:
		result = executor.map(routine, mods)


def get_mods() -> set[str]:
	"""
	Get all the moderators for the given games and return them in a set.
	"""
	mods: set[Moderator] = set()
	for abbrev in argv[1:]:
		r = api_get(
			f"{API}/games",
			params={"abbreviation": abbrev, "embed": "moderators"},
		)
		try:
			mods.update(
				Moderator(mod["names"]["international"])
				for mod in r["data"][0]["moderators"]["data"]
			)
		except IndexError:
			error_and_die(f"Game with abbreviation '{abbrev}' not found.")

	return mods


def check_args() -> None:
	"""
	Check to ensure that the right arguments have been passed.
	"""
	if (argc := len(argv)) == 1:
		usage(USAGE)

	if argc > 3:
		print(
			"Error: Too many games given, you can give a maximum of 2.",
			file=stderr,
		)
		exit(EXIT_FAILURE)

	if argc == 3 and argv[1] == argv[2]:
		print("Error: The same game cannot be provided twice.", file=stderr)
		exit(EXIT_FAILURE)


def main() -> int:
	check_args()
	if len((mods := get_mods())) == 0:
		printf("```No mods for any game found```")
		return EXIT_SUCCESS

	chdir(dirname(argv[0]))
	get_examined(mods)

	mods = list(mods)
	mods.sort(key=attrgetter("examined"), reverse=True)

	print(
		"WARNING: On large leaderboards this is very likely to be incorrect due to rate limiting"
	)
	print("\n".join(f"{mod.name}: {mod.examined}" for mod in mods))
	return EXIT_SUCCESS


if __name__ == "__main__":
	exit(main())
