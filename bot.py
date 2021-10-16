import discord
from discord.ext import commands
import os
from discord_slash import SlashCommand, SlashContext

"""
This Is The Rewrite Version Of Sabre Bot. It Is A Development Version So It Is Buggy.
The Ultimate Aim It To Create a More Customisable, Compatible and Safe Discord Bot. 

Documentation:
    http://discordpy.readthedocs.io/en/rewrite/api.html
Rewrite Commands Documentation:
    http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html

"""
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot, sync_commands=True)
guild_ids = [704255331680911402]


@slash.slash(name="test", guild_ids=guild_ids)
async def test(ctx: SlashContext):
    #embed = discord.Embed(title="Embed Test")
    await ctx.send("success!")







@bot.event
async def on_ready():
    """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""

    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    # Changes our bots Playing Status. type=1(streaming) for a standard game you could remove type and url.
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Visual Studio Code'))
    print(f'Successfully logged in and booted...!')









for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        
with open("token.key") as f:
    token = f.read()
    f.close()
bot.run(token, bot=True, reconnect=True)