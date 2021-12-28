import discord
import discord.utils
import requests
from discord.ext import commands
from discord_slash import cog_ext

guild_ids = [704255331680911402]



class bcolours:
    HEADER = '\033[95m'
    OKBLUE = '\033[34m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[0;31m'
    ENDC = '\033[0m'
print(f"{bcolours.OKBLUE} API Commands Initiating...")


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="urban", guild_ids=guild_ids)
    async def _urban(self, ctx, *,  query:str):
        query = query.replace(" ", "+")
        url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

        querystring = {"term":query}

        headers = {
            'x-rapidapi-key': "9c9db506e4msh143be28c405924bp155af3jsn90a03f937362",
            'x-rapidapi-host': "mashape-community-urban-dictionary.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)
        dictdump = response.json()

        embed = discord.Embed(title = f'Urban Dictionary - {dictdump["list"][0]["word"]}', description = f'{dictdump["list"][0]["definition"]}', color = 0xffb6f2)
        embed.set_thumbnail(url = "https://i.imgur.com/k8hRmNl.png")
        embed.add_field(name = "Example", value=dictdump["list"][0]["example"], inline = False)
        embed.set_footer(text = f'Definiton by {dictdump["list"][0]["author"]}')
        await ctx.send(embed=embed)


    @cog_ext.cog_slash(name="covid", guild_ids=guild_ids)
    async def _covid(self, ctx):
        url = "https://covid-19-tracking.p.rapidapi.com/v1"
        headers = {
            'x-rapidapi-key': "9c9db506e4msh143be28c405924bp155af3jsn90a03f937362",
            'x-rapidapi-host': "covid-19-tracking.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers)
        dictdump = response.json()
        dictdump = dictdump[0]

        embed = discord.Embed(title = f'Covid-19 Statistics (Global)', color = 0xffb6f2)
        embed.add_field(name = "Total Cases", value=dictdump["Total Cases_text"], inline = False)
        embed.add_field(name = "Total Active Cases", value=dictdump["Active Cases_text"], inline = False)
        embed.add_field(name = "New Cases", value=dictdump["New Cases_text"], inline = False)
        embed.add_field(name = "Total Deaths", value=dictdump["Total Deaths_text"], inline = False)
        embed.add_field(name = "New Deaths", value=dictdump["New Deaths_text"], inline = False)
        embed.add_field(name = "Total Recovered", value=dictdump["Total Recovered_text"], inline = False)
        embed.set_footer(text = f'Last Update On {dictdump["Last Update"]}')
        await ctx.send(embed=embed)




def setup(bot):
    bot.add_cog(Misc(bot))
