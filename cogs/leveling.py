import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import psycopg
from cachetools import cached, TTLCache
from datetime import datetime

conn = psycopg.connect(dbname="sabre", user="postgres", password="jumper123", host="localhost")




@cached(cache = TTLCache(maxsize=100, ttl=10))
def load_data():
    # run slow data to get all user data
    load_response = "This Was Cached At " + datetime.strftime(datetime.now(), "%d/%m/%Y %H:%M:%S") + "This Is A TTL Cache And Will Change 10 Seconds After Being Created"

    return load_response
class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




    @cog_ext.cog_slash(name="cogt")
    async def _cogt(self, ctx: SlashContext):
        embed = discord.Embed(title=load_data())
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Slash(bot))