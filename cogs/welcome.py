

import discord
from discord.ext import commands



from modules import cache_get as cache

guild_ids = [704255331680911402]



class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_cache = cache.get_guild(member.guild.id)
        if guild_cache["toggle"]["welcomer"]:
            if guild_cache["welcome"]["join"]["channel"]:
                channel = self.bot.get_channel(guild_cache["welcome"]["join"]["channel"])
                if not channel:
                    guild_cache["welcome"]["join"]["channel"] = None
                    guild_cache["welcome"]["join"]["message"] = None
                    cache.update_guild(guild_cache)
                    
                else:
                    await channel.send(guild_cache["welcome"]["join"]["message"][0].replace("{user.mention}", member.mention).replace("{user.display}", f"{member.display_name}#{member.discriminatior}").replace("{guild.name}", member.guild.name))
            if guild_cache["welcome"]["join"]["private"]:
                message = guild_cache["welcome"]["join"]["private"].replace("{user.mention}", member.mention).replace("{user.display}", f"{member.display_name}#{member.discriminatior}")
                await member.send(message)
        if guild_cache["toggle"]["autorole"]:
            if guild_cache["welcome"]["join"]["role"]:
                role = discord.utils.get(member.guild.roles, id=guild_cache["welcome"]["join"]["role"])
                if role is None:
                    guild_cache["welcome"]["join"]["role"] = None
                    cache.update_guild(guild_cache)
                await member.add_roles(role)
                
    @commands.Cog.listener()
    async def on_member_leave(self, member):
        guild_cache = cache.get_guild(member.guild.id)
        if guild_cache["toggle"]["welcomer"]:
            if guild_cache["welcome"]["leave"]["channel"]:
                channel = self.bot.get_channel(guild_cache["welcome"]["leave"]["channel"])
                if not channel:
                    guild_cache["welcome"]["leave"]["channel"] = None
                    guild_cache["welcome"]["leave"]["message"] = None
                    cache.update_guild(guild_cache)
                    
                else:
                    await channel.send(guild_cache["welcome"]["leave"]["message"][0].replace("{user.display}", f"{member.display_name}#{member.discriminatior}").replace("{guild.name}", member.guild.name))












def setup(bot):
    bot.add_cog(Welcome(bot))
    
