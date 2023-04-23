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

# enable intents
intents = discord.Intents.default()

# create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# create the SlashCommand instance
slash = SlashCommand(bot, sync_commands=True)

# specify the guild IDs to use with the slash commands
guild_ids = [704255331680911402]

# define the "test" slash command
@slash.slash(name="test", guild_ids=guild_ids)
async def test(ctx: SlashContext):
    await ctx.send("success!")

# event handler for when the bot is ready
@bot.event
async def on_ready():
    """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""

    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    
    await bot.wait_until_ready()

    # set the bot's playing status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Visual Studio Code'))
    
    print(f'Successfully logged in and booted...!')

# event handler for when a component callback raises an error
@bot.event
async def on_component_callback_error(ctx: SlashContext, ex):
    await print("OH NOES!", ex)
    await ctx.send(ex)

# event handler for when a slash command raises an error
@bot.event
async def on_slash_command_error(ctx: SlashContext, ex):
    await print("OH NOES!", ex)
    await ctx.send(ex)

# event handler for when a basic command raises an error
@bot.event
async def on_command_error(ctx, error):
    print("OH NOES (basic)!", error)
    await ctx.send(error)

# load all the cogs (extensions) in the "cogs" folder
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        
# read the bot token from a file and run the bot
with open("token.key") as f:
    token = f.read()
    f.close()
bot.run(token, bot=True, reconnect=True)
