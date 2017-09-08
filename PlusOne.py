import yaboli
from yaboli.utils import *
import re
import sys



class PointDB(yaboli.Database):
	@yaboli.Database.operation
	def initialize(conn):
		cur = conn.cursor()
		cur.execute((
			"CREATE TABLE IF NOT EXISTS Points ("
				"nick TEXT UNIQUE NOT NULL,"
				"points INTEGER"
			")"
		))
		conn.commit()
	
	@yaboli.Database.operation
	def add_point(conn, nick):
		nick = mention_reduced(nick)
		cur = conn.cursor()
		
		cur.execute("INSERT OR IGNORE INTO Points (nick, points) VALUES (?, 0)", (nick,))
		cur.execute("UPDATE Points SET points=points+1 WHERE nick=?", (nick,))
		conn.commit()
	
	@yaboli.Database.operation
	def points_of(conn, nick):
		nick = mention_reduced(nick)
		cur = conn.cursor()
		
		cur.execute("SELECT points FROM Points WHERE nick=?", (nick,))
		res = cur.fetchone()
		if res is not None:
			return res[0]
		else:
			return 0

class YourBot(yaboli.Bot):
	"""
	Count +1s awarded to users by other users.
	"""
	
	PLUSONE_RE = r"(\+1|:\+1:|:bronze:)"
	
	def __init__(self, db):
		super().__init__("PlusOne")
		
		self.db = db
		
		self.help_general = "/me counts :+1:s."
		self.help_specific = (
			"Counts +1/:+1:/:bronze:s: Simply reply to someone's message to award them a point.\n"
			"!points - show your own points\n"
			"!points <person1> [<person2> ...] - list other people's points\n\n"
			"Github: https://github.com/Garmelon/plusone (complies with botrulez, including !kill and !restart)\n"
			"Created by @Garmy using yaboli (https://github.com/Garmelon/yaboli)"
		)
		self.ping_message = ":bronze!?:"
		
		self.register_callback("points", self.command_points, specific=False)
	
	async def on_connected(self):
		await super().on_connected()
		await self.db.initialize()
	
	async def on_send(self, message):
		await super().on_send(message) # This is where yaboli.bot reacts to commands
		await self.detect_plusone(message)
	
	async def detect_plusone(self, message):
		if re.fullmatch(self.PLUSONE_RE, message.content):
			if not message.parent:
				await self.room.send("You can't +1 nothing...", message.mid)
			else:
				parent_message = await self.room.get_message(message.parent)
				sender = parent_message.sender.nick
				await self.db.add_point(sender)
				await self.room.send("Point registered.", message.mid)
	
	async def command_points(self, message, args):
		if not args:
			points = await self.db.points_of(message.sender.nick)
			await self.room.send(
				f"You have {points} point{'s' if points != 1 else ''}.",
				message.mid
			)
		else:
			response = []
			for arg in args:
				if arg[:1] == "@":
					nick = arg[1:]
					points = await self.db.points_of(nick)
					response.append(f"@{mention(nick)} has {points} point{'' if points == 1 else 's'}.")
				else:
					response.append(f"{arg!r} is not a mention.")
			await self.room.send("\n".join(response), message.mid)

def main():
	if len(sys.argv) == 3:
		db = PointDB(sys.argv[2])
		run_bot(YourBot, sys.argv[1], db)
	else:
		print("USAGE:")
		print(f"  {sys.argv[0]} <room> <pointsdb>")
		return

if __name__ == "__main__":
	main()
