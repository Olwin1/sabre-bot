import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import psycopg
from cachetools import cached, TTLCache
from datetime import datetime

conn = psycopg.connect(dbname="sabre", user="postgres", password="***REMOVED***", host="localhost")

guild_ids = [704255331680911402]
print("levleing is runnin")
cooldown = TTLCache(maxsize=1024, ttl=20)

cache = TTLCache(maxsize=100, ttl=10)


# This Function Gets The User Data From The Cache. IF It Is Not In The Cache It Fetches It and If It Cannot Be Found It Creates It.
def getcache_leveling(key, guild_id):
    selected = cache.get(key)
    if selected is None:
      cur = conn.cursor()
      cur.execute("SELECT guilds,exp FROM users WHERE user_id=%s", (key,))
      selected = cur.fetchone()
      if selected is None:
          cur.execute("INSERT INTO users (user_id, guilds, exp) VALUES (%s, %s, %s)", (key, [guild_id,], [1,]))
          conn.commit()
          cur.execute("SELECT guilds,exp FROM users WHERE user_id=%s", (key,))
          selected = cur.fetchone()
    return selected

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




    @cog_ext.cog_slash(name="cogt", guild_ids=guild_ids)
    async def _cogt(self, ctx: SlashContext):

        user = getcache_leveling(ctx.author.id, ctx.guild.id)
        user = {"guilds": user[0], "exp": user[2]}
        passed = False
        for i in range(user["guilds"]):
            if user["guilds"][i] == ctx.guild.id:
                passed = True
                total_exp = user["exp"]
                exp = total_exp
                x = exp
                y = 0
                level = 0
                while exp > 0:
                    x = 5*(level**2)+50*level+100
                    y += x
                    exp -= x
                    print(x, level)
                    level += 1
                #Below Is What Happens After
                total_exp_next_display = x
                total_exp_next_actual = y
                remaining = total_exp_next_actual - total_exp
                print("final", total_exp_next_display, level, total_exp_next_actual, remaining)

                member = {"guild": user["guilds"][i], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining}
        
        await ctx.send(user["guilds"][0])



        


def setup(bot):
    bot.add_cog(Slash(bot))