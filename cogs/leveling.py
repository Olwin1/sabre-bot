import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import psycopg
from cachetools import cached, TTLCache
from datetime import datetime

conn = psycopg.connect(dbname="sabre", user="postgres", password="jumper123", host="localhost")

guild_ids = [704255331680911402]
print("levleing is runnin")
cooldown = TTLCache(maxsize=1024, ttl=20)

cache = TTLCache(maxsize=100, ttl=10)


# This Function Gets The User Data From The Cache. IF It Is Not In The Cache It Fetches It and If It Cannot Be Found It Creates It.
def getcache_leveling(key, guild_id):
    selected = cache.get(key)
    if selected is None:
      cur = conn.cursor()
      cur.execute("SELECT guilds,levels,exp FROM users WHERE user_id=%s", (key,))
      selected = cur.fetchone()
      if selected is None:
          cur.execute("INSERT INTO users (user_id, guilds, levels, exp) VALUES (%s, %s, %s, %s)", (key, [guild_id,], [0,], [0,]))
          conn.commit()
          cur.execute("SELECT guilds,levels,exp FROM users WHERE user_id=%s", (key,))
          selected = cur.fetchone()
    return selected

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




    @cog_ext.cog_slash(name="cogt", guild_ids=guild_ids)
    async def _cogt(self, ctx: SlashContext):
        print(2)
        cache = getcache_leveling(ctx.author.id, ctx.guild.id)
        print(3)
        if cache is None:
            cache = "Empty :("
        await ctx.send(str(cache))
        print(type(cache))


        


def setup(bot):
    bot.add_cog(Slash(bot))