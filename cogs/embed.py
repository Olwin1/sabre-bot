import json
import socket
import threading
import asyncio
import aiohttp
import requests
from discord import Embed, Permissions
from discord.ext import commands
from colored import fg, bg, attr
from modules import cache_get as cache
import json

#from modules import cache_get as cache

guild_ids = [704255331680911402]




class Embeder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        x = threading.Thread(target=self.entrypoint)
        x.start()
        
    def entrypoint(self):
        asyncio.run(self.server_program())
        

    async def server_program(self):
        print(f"{fg(197)}Embed API Initiating{attr('reset')}")
        # get the hostname
        host = "localhost"
        print(host)
        port = 63432  # initiate port no above 1024
        
        
        
        async def getUserGuilds(token):
            async with aiohttp.ClientSession() as session:
                async with session.get('https://discord.com/api/v9/users/@me/guilds', headers={"Authorization": token}) as response:

                    print("Status:", response.status)
                    print("Content-type:", response.headers['content-type'])
                    if response.status == 429:
                        return await getUserGuilds(token)
                    else:
                        return await response.json()

        server_socket = socket.socket()  # get instance
        # look closely. The bind() function takes tuple as argument
        server_socket.bind((host, port))  # bind host address and port together

        # configure how many client the server can listen simultaneously
        print(1)
        server_socket.listen(2)
        print(2)
        while True:
            conn, address = server_socket.accept()  # accept new connection
            print(3)
            print("Connection from: " + str(address))
            while True:
                # receive data stream. it won't accept data packet greater than 1024 bytes
                data = conn.recv(1024).decode()
                if not data:
                    # if data is not received break
                    break
                print("from connected user: " + str(data))
                data = json.loads(str(data))
                typ = data["type"]
                data = json.loads(str(data["data"]))
                print("josn below")
                print(data)
                print("-----------")
                retval = {}
                if typ == "sendEmbed":
                    embed = {}
    
                    for k,v in data.items():
                        if v == "":
                            data[k] = Embed.Empty
                        else:
                            print(k,v)
                    embed=Embed(title=data["title"], url=data["url"], description=data["desc"], color=int(data["colour"].replace("#", ""), 16))
                    embed.set_author(name=data["a"], url=data["a_url"])
                    for i, v in enumerate(data["fields"]):
                        embed.add_field(name=data["fields_t"][i], value=v, inline=False)
                    embed.set_image(url=data["img"])
                    embed.set_footer(text=data["footer"])
                    embed.set_thumbnail(url=data["a_ico"])
                    channel = self.bot.get_channel(746500764633006150)
                    if data["content"] == Embed.Empty:
                        self.bot.loop.create_task(channel.send(embed=embed))
                    else:
                        self.bot.loop.create_task(channel.send(embed=embed,content=data["content"]))
                    retval["result"] = "success"
                        
                        
                elif typ == "getGuilds":


                    guilds = data["guilds"]
                    retval["guilds"] = []

                    for i in guilds:
                        perms = Permissions(int(i["permissions"]))
                        if perms.manage_guild:
                            y = {"id": i["id"], "name": i["name"], "icon": i["icon"]}
                            if cache.get_guildExists(i["id"]):
                                y["hasSabre"] = True
                            else:
                                y["hasSabre"] = False
                            retval["guilds"].append(y)
                                
                            
                    
                    


                conn.send(json.dumps(retval).encode())  # send data to the client

            conn.close()  # close the connection













def setup(bot):
    bot.add_cog(Embeder(bot))
    