import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import psycopg
from cachetools import cached, TTLCache, LRUCache
from datetime import datetime

conn = psycopg.connect(dbname="sabre", user="postgres", password="***REMOVED***", host="localhost")

guild_ids = [704255331680911402]
print("levleing is runnin")
cooldown = TTLCache(maxsize=1024, ttl=20)

class SabreCache(LRUCache):
  def popitem(self):
    cur = conn.cursor()
    if super().currsize == 0:
        return None, None
    key, value = super().popitem()
    print('Key "%s" evicted with value "%s"' % (key, value))
    cur.execute("UPDATE users SET guilds = %s, exp = %s WHERE user_id=%s", (value[0], value[1], key))
    conn.commit()
    return key, value


cache = SabreCache(maxsize=100)


# This Function Gets The User Data From The Cache. IF It Is Not In The Cache It Fetches It and If It Cannot Be Found It Creates It.
def getcache_leveling(key, guild_id):
    selected = cache.get(key)
    if selected is None:
      cur = conn.cursor()
      cur.execute("SELECT guilds,exp FROM users WHERE user_id=%s", (key,))
      selected = cur.fetchone()
      cache[key] = selected
      if selected is None:
          cur.execute("INSERT INTO users (user_id, guilds, exp) VALUES (%s, %s, %s)", (key, [guild_id,], [1,]))
          conn.commit()
          cur.execute("SELECT guilds,exp FROM users WHERE user_id=%s", (key,))
          selected = cur.fetchone()
          cache[key] = selected
    return selected

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="cogt")
    async def _cogt(self, ctx):

    #@cog_ext.cog_slash(name="cogt", guild_ids=guild_ids)
    #async def _cogt(self, ctx: SlashContext):

        user = getcache_leveling(ctx.author.id, ctx.guild.id)
        user = {"guilds": user[0], "exp": user[1]}
        passed = False
        for i in range(len(user["guilds"])):
            if user["guilds"][i] == ctx.guild.id:
                passed = True
                total_exp = user["exp"][i]
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

                member = {"guild": user["guilds"][i], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining
        if not passed:
            print(cache[ctx.author.id][0])
            cache[ctx.author.id][0].append(ctx.guild.id)
            cache[ctx.author.id][1].append(1)
            print(cache[ctx.author.id][0])
            member = {"guild": ctx.guild.id, "level": 1, "total_exp": 1, "total_exp_next_actual": 100, "total_exp_next_display": 100, "remaining": 99, "exp": 1}
        await ctx.send(f'Level is: **{member["level"]}** Exp To Next Level Is: **{member["total_exp_next_display"]}** Remaining Exp is: **{member["remaining"]}** Your Exp Is **{member["exp"]}**')


    @cog_ext.cog_slash(name="cacheclear", guild_ids=guild_ids)
    async def _cacheclear(self, ctx:SlashContext):
        await ctx.send("Clearing Cache...")
        for i in range(cache.currsize):
            print(i)
            cache.popitem()
        print("Popped")


    @cog_ext.cog_slash(name="cache", guild_ids=guild_ids)
    async def _cache(self, ctx:SlashContext):
        await ctx.send("Printing Cache...")
        print(cache)



    @cog_ext.cog_slash(name="cachepop", guild_ids=guild_ids)
    async def _cachepop(self, ctx:SlashContext):
        print(cache)
        await ctx.send("Popping Cache...")
        cache.popitem()



        


def setup(bot):
    bot.add_cog(Slash(bot))