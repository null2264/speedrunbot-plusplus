import os
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess, run
from sys import stderr
from typing import Iterable

import discord
from discord.ext import commands
from discord.message import Message

PREFIX: Path = Path(__file__).parent
ROOT_DIR: str = f"{PREFIX}/.."
EXTENSIONS: Iterable[str] = (
	f"cogs.{f[:-3]}" for f in os.listdir(f"{PREFIX}/cogs") if f.endswith(".py")
)


class SRBpp(commands.Bot):
	def __init__(self) -> None:
		super().__init__(
			allowed_mentions=discord.AllowedMentions(
				everyone=False, users=True, roles=False
			),
			case_insensitive=True,
			command_prefix=get_prefix,
			intents=discord.Intents(messages=True, guilds=True),
		)

		for extension in EXTENSIONS:
			try:
				self.load_extension(extension)
			except Exception as e:
				print(e, file=stderr)

		with open(f"{ROOT_DIR}/token", "r") as f:
			self.token = f.read().strip()

	def execv(_, PROG: str, *ARGS: tuple[str, ...]) -> CompletedProcess:
		"""
		Run a program as a subprocess and return its output + exit code.
		"""
		return run(
			(f"{PREFIX}/{PROG}",) + tuple(filter(lambda x: x, ARGS)),
			capture_output=True,
			text=True,
		)

	async def on_ready(self) -> None:
		"""
		Code to run when the bot starts up.
		"""
		self.uptime: datetime = datetime.utcnow()
		GAME: discord.Game = discord.Game("+help / !help")
		await self.change_presence(activity=GAME)

		print(
			f"Bot Name\t\t{self.user.name}\n"
			+ f"Bot ID\t\t\t{self.user.id}\n"
			+ f"Discord Version\t\t{discord.__version__}\n"
			+ f"Time\t\t\t{self.uptime.strftime('%F %T')}"
		)

	async def close(self) -> None:
		"""
		Cleanup before the bot exits.
		"""
		for extension in EXTENSIONS:
			try:
				self.unload_extension(extension)
			except Exception as e:
				print(e, file=stderr)

		await super().close()

	def run(self) -> None:
		"""
		Run the bot.
		"""
		super().run(self.token, reconnect=True)


def get_prefix(bot: SRBpp, message: Message) -> list[str]:
	"""
	Gets the list of prefixes that can be used to call the bot, including
	pinging the bot.
	"""
	PREFIXES: tuple[str, ...] = ("+", "!")
	return commands.when_mentioned_or(*PREFIXES)(bot, message)
