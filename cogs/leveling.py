import io
import random
import socket
import threading



import discord
from cachetools import TTLCache, cached
from discord import File
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from modules import cache_get as cache
from modules import rank_bg as background
from PIL import Image, ImageDraw, ImageFont




'''
def worker():
    """thread worker function"""
    print('Worker')
    HOST = 'localhost'  # Standard loopback interface address (localhost)
    PORT = 63431        # Port to listen on (non-privileged ports are > 1023)
    
    s = socket.socket()
    s.bind(('', PORT))        
    print ("socket binded to %s" %(PORT))
    
    # put the socket into listening mode
    s.listen(5)    
    print ("socket is listening")           
    
    # a forever loop until we interrupt it or
    # an error occurs
    while True:
    
    # Establish connection with client.
        c, addr = s.accept()    
        print ('Got connection from', addr )
        
    #Get Data From Client
        data = c.recv(1024)
        print(data)
    
    # send a thank you message to the client. encoding to send byte type.
        package = "Thank You For Connecting!" + str(data)
        c.send(package.encode())
    
    # Close the connection with the client
        c.close()
    
    # Breaking once connection closed
        break


threads = []
t = threading.Thread(target=worker)
threads.append(t)
t.start()
'''



guild_ids = [704255331680911402]
print("levleing is runnin")
cooldown = TTLCache(maxsize=1024, ttl=20)








@cached(cache=TTLCache(maxsize=1024, ttl=3600))# Cache To Remember If Needs Re-Ordering Or Not. Only Executes Function Minimum every 60 mins per guild
def order_ranks(key):
    guild = cache.get_guild(key)
    print("creating")
    sorted_list = sorted(guild["members"], key=lambda y: y["exp"], reverse=True)
    guild["members"] = sorted_list
    cache.update_guild(guild)
    return None






  #Each Cog In In The Same File In Order To Share The Cache But They Are Still Individual Cogs And Can Be Enabled & Disabled
  
  #The First One Is The Leveling Cog As Defined In the Class Below.  Everything Inside That Class Is To Do With Leveling
  

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        with open('./other/blocked_words.txt') as f:
            self.blocked_words = f.read().splitlines()
            f.close()
        
        





    @cog_ext.cog_slash(name="rank", guild_ids=guild_ids)
    async def _rank(self, ctx: SlashContext, member: discord.Member=None):
        '''Display Your Rank Card'''
        if member is None:
            author = ctx.author
        else:
            author = member
        guild = cache.get_guild(ctx.guild.id)
        guild, index = cache.find_member(guild, author.id)


        total_exp = guild["members"][index]["exp"]
        exp = total_exp
        x = exp
        y = 0
        level = 0
        while exp > 0:
            x = 5*(level**2)+50*level+100
            y += x
            exp -= x
            level += 1
        #Below Is What Happens After
        total_exp_next_display = x
        total_exp_next_actual = y
        remaining = total_exp_next_actual - total_exp


        lvl_obj = {"level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining
                
 # Below Is Where The Rank Card Image Generation Starts

        percent = lvl_obj["exp"] / lvl_obj["total_exp_next_display"]
        percent = percent * 100
        percent = round(percent)
        percent = int(percent)


        background_image = Image.open(background.fetch(author.id))
        color = background.get_dominant_color(background_image)

        background_image = background_image.convert('RGBA') # add channel ALPHA to draw transparent rectangle
 #            image = Image.open('Cockatoo-min.png')
        AVATAR_SIZE = 256

        # --- duplicate image ----

        image = background_image.copy()


        # --- draw on image ---


        draw = ImageDraw.Draw(image)

 # CREATE YOUR FILL COLOUR HERE (CHANGE TO 245 AT END OF EVENT)
        #color=(202,98,45) HALOWEEN COLOR
 # Draw circle at left of progress bar to round
        x, y, diam = 330, 406, 49
        draw.ellipse([x,y,x+diam,y+diam], fill=color)
        percent = percent + 1
        for iteration in range(percent):
            if iteration < 76:
                x = x + 11
            elif iteration < 100:
                x = x + 13
            else:
                x = x + 21
        draw.line((350, 430) + (x, 430), fill=color, width=50)# Draw The Bar
        if percent == 101:# If Max Reached Add Circle At End To Round The Bar Off
            x, y, diam = 1480, 406, 49
            draw.ellipse([x,y,x+diam,y+diam], fill=color)
            
        #Configuration For Fonts
        path = "other/fonts/Quicksand-Medium.ttf"
        font_60 = ImageFont.truetype(path, 60)
        font_50 = ImageFont.truetype(path, 50)
        font_75 = ImageFont.truetype(path, 75)
        font_90 = ImageFont.truetype(path, 90)
        
        
        # ------ DRAWING OF TEXT ON IMAGE ------



        # Draw User's Name
        
        text_width_name, text_height_name = draw.textsize(str(author.name), font=font_75)
        x = 300
        y = 315
        

        draw.text((x, y), str(author.name), fill=(255,255,255, 255), font=font_75)
        

        draw.text((x + text_width_name, y - 10), f"#{author.discriminator}", fill=(149,149,149, 255), font=font_50)


        # Draw User's Exp

        text_width_exp, text_height = draw.textsize(str(lvl_obj["exp"]), font=font_60)
        x = 1300
        y = 325
        

        draw.text((x, y), str(lvl_obj["exp"]), fill=(255,255,255, 255), font=font_60)
        
        draw.text((x + text_width_exp, y), " / " + str(lvl_obj["total_exp_next_display"]), fill=(149,149,149, 255), font=font_60)


        # Draw User's Level
        x = 1205 + AVATAR_SIZE
        y = 150
        draw.text((x, y), "Level", fill=(149,149,149, 255), font=font_60)


        text_width_level, text_height_level = draw.textsize("Level", font=font_75)
        draw.text((x + text_width_level, y - 30), str(lvl_obj["level"]), fill=(255,255,255, 255), font=font_90)
    
        # Draw User's Rank
        x = 1055 + AVATAR_SIZE
        draw.text((x, y), "#", fill=(149,149,149, 255), font=font_60)

        y += 15
        text_width_level, text_height_level = draw.textsize("#", font=font_60)
        order_ranks(author.guild.id)
        guild = cache.get_guild(author.guild.id)
        guild, index = cache.find_member(guild, author.id)
        draw.text((x + text_width_level, y - 30), str(index + 1), fill=(250,250,250, 250), font=font_75)
        
        
        # --- avatar ---
        # get URL to avatar
        # sometimes `size=` doesn't gives me image in expected size so later I use `resize()`
        avatar_asset = author.avatar_url_as(format='jpg', size=AVATAR_SIZE)

        # read JPG from server to buffer (file-like object)
        buffer_avatar = io.BytesIO(await avatar_asset.read())


        # read JPG from buffer to Image
        thumbnail = Image.open(buffer_avatar)

        # resize it
        thumbnail = thumbnail.resize((AVATAR_SIZE, AVATAR_SIZE)) #
        circle_image = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
        circle_draw = ImageDraw.Draw(circle_image)
        circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        image.paste(thumbnail, (20, 20), circle_image)

        buffer_output = io.BytesIO()
        image.save(buffer_output, format='PNG')

        # move to beginning of buffer so `send()` it will read from beginning
        buffer_output.seek(0)

        # send image
        await ctx.send(file=File(buffer_output, 'card.png'))




    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:# To Make Sure Not Responding To Bot's Own Message
            return

        
        guild = cache.get_guild(message.guild.id)
        
        guild, index = cache.find_member(guild, message.author.id)
        
        
        #START OF AUTOMOD
        if guild["toggle"]["automod"]:
            detected = False
            var = {"links": True, "invites": True, "mass_mention": True, "swears": True}
            
            if guild["automod"]["swears"]:# Auto Mod For Swearing
                msg = message.content.lower()
                msg = msg.replace("cockatoo", "").replace("cockateil", "").replace("cockatiel", "").replace("1", "i").replace("ą", "a").replace("ę", "e").replace("ś", "s").replace("ć", "c").replace("⠀", "")
                for word in self.blocked_words:
                    if word in msg:
                        detected = True
                        break
                if detected:
                    print(f"Message Deleted: '{message.content}'")
                    await message.delete()
                    
            if guild["automod"]["links"]:# Auto Mod For URLS (Except Invite Links)
                if "http://" in message.content or "https://" in message.content:
                    if "https://discord.gg/" in message.content or "http://discord.gg/" in message.content or "https://discord.com/invite" in message.content or "http://discord.com/invite" in message.content:
                        pass
                    else:
                        print(f"Link Has Been Deleted: '{message.content}'")
                        await message.delete()
                        
                        
            if guild["automod"]["invites"]:#Auto Mod For Invite Links
                if "https://discord.gg/" in message.content or "http://discord.gg/" in message.content or "https://discord.com/invite" in message.content or "http://discord.com/invite" in message.content:
                    print(f"Invite Link Has Been Deleted: '{message.content}'")
                    await message.delete()
                    
            if guild["automod"]["mention"]:# Auto Mod For Mass Mentions
                if len(message.raw_mentions) >= 5:# 5 Mentions+ = Mass Mention
                    print(f"Mass Mention Has Been Deleted: '{message.content}'")
                    await message.delete()
            #END OF AUTOMOD

        total_exp = guild["members"][index]["exp"]
        exp = total_exp
        x = exp
        y = 0
        level = 0
        while exp > 0:
            x = 5*(level**2)+50*level+100
            y += x
            exp -= x
            level += 1
        #Below Is What Happens After
        total_exp_next_display = x
        total_exp_next_actual = y
        remaining = total_exp_next_actual - total_exp


        #member = {"guild": guild["members"][index]["g_id"], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining

        x = cooldown.get(message.author.id)
        if x is not None:
            return
        cooldown[message.author.id] = True
        increase = random.randint(15, 20)
        guild["members"][index]["exp"] += increase
        cache.update_guild(guild)
        if increase >= remaining:
            await message.channel.send(f"**{message.author.name}** Has Leveled Up To Level **{level + 1}**!")





def setup(bot):# Here Is Where The Cogs Are Added. All Cog Classes MUST Be Linked Here In Order to Be Added.
    bot.add_cog(Leveling(bot))