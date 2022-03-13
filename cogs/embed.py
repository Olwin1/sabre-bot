import json
import socket
import threading
import asyncio
import requests
from discord import Embed
from discord.ext import commands
from colored import fg, bg, attr

#from modules import cache_get as cache

guild_ids = [704255331680911402]




class Embeder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        x = threading.Thread(target=self.server_program)
        x.start()
        

        

    def server_program(self):
        print(f"{fg(197)}Embed API Initiating{attr('reset')}")
        # get the hostname
        host = "localhost"
        print(host)
        port = 63432  # initiate port no above 1024

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
                data = json.loads(str(data["data"]))
                print("josn below")
                print(data)
                print("-----------")
                embed = {}
 
                for k,v in data.items():
                    print("...")
                    if v == "":
                        data[k] = Embed.Empty
                    else:
                        print(k,v)
                    print("****")
                print("end")
                print(data)
                        
                    #print(f["b"]["t"])
#                    
#                    embed=Embed(title=e["b"]["t"], url=e["b"]["u"], description=e["b"]["d"], color=e["b"]["c"])
#                    #embed=Embed(title='e["b"]["t"]', url='e["b"]["u"]', description='e["b"]["d"]', color=0xeb4034)
#
#                    embed.set_author(name=e["a"]["t"], url=e["a"]["u"], icon_url=e["a"]["i"])
#                    for field in e["fi"]:
#                        if not field["v"]:
#                            field["v"] = Embed.Empty
#                        if not field["n"]:
#                            field["n"] = "⠀"
#                        embed.add_field(name=field["n"], value=field["v"], inline=field["i"])
#                    if e["i"]:
#                        embed.set_image(url=e["i"])
#                    if e["t"]:
#                        embed.set_thumbnail(url=e["t"])
#                    
#                    
#                    if e["fo"]["f"] and e["fo"]["t"]:
#                        text = f"{e['fo']['f']}•{e['fo']['f']}"
#                    elif e["fo"]["t"]:
#                        text = e["fo"]["t"]
#                    elif e["fo"]["f"]:
#                        text = e["fo"]["f"]
#                    else:
#                        text = Embed.Empty
#                    if not e["fo"]["i"]:
#                        e["fo"]["i"] = Embed.Empty
#                    embed.set_footer(text=text, icon_url=e["fo"]["i"])
#                    embeds.append(embed.to_dict()) """
#                
                
                #headers = {"Authorization": f"Bot {self.bot.http.token}"}
                #sendData = {"embeds": embeds}
                #r = requests.post(f'https://discord.com/api/v8/channels/{channel_id}/messages', json=sendData, headers=headers)
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
                    


                conn.send(str("r.content").encode())  # send data to the client

            conn.close()  # close the connection













def setup(bot):
    bot.add_cog(Embeder(bot))
    