import io
import random
import socket
import threading

import discord
import psycopg
from cachetools import LRUCache, TTLCache
from discord import File
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from PIL import Image, ImageDraw, ImageFont


def worker():
    """thread worker function"""
    print('Worker')
    HOST = 'localhost'  # Standard loopback interface address (localhost)
    PORT = 63431        # Port to listen on (non-privileged ports are > 1023)
    
        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)


threads = []
t = threading.Thread(target=worker)
threads.append(t)
t.start()

conn = psycopg.connect(dbname="sabre", user="postgres", password="jumper123", host="localhost")

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
        
    def __del__(self):
        print("Clearing Cache...")
        for i in range(cache.currsize):
            cache.popitem()
        print("Cache Has Been Emptied!")




    @cog_ext.cog_slash(name="rank", guild_ids=guild_ids)
    async def _rank(self, ctx: SlashContext, member: discord.Member=None):
        if member is None:
            author = ctx.author
        else:
            author = member
        user = getcache_leveling(author.id, ctx.guild.id)
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


                member = {"guild": user["guilds"][i], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining
        if not passed:
            print(cache[author.id][0])
            cache[author.id][0].append(ctx.guild.id)
            cache[author.id][1].append(1)
            print(cache[author.id][0])
            member = {"guild": ctx.guild.id, "level": 1, "total_exp": 1, "total_exp_next_actual": 100, "total_exp_next_display": 100, "remaining": 99, "exp": 1}
        #await ctx.send(f'Level is: **{member["level"]}** Exp To Next Level Is: **{member["total_exp_next_display"]}** Remaining Exp is: **{member["remaining"]}** Your Exp Is **{member["exp"]}**')

        percent = member["exp"] / member["total_exp_next_display"]
        percent = percent * 100
        percent = round(percent)
        percent = int(percent)

        #if user_id == 416617058248425473:
        #    background_image = Image.open("/root/drive/Development/Sabre/cogs/other/bridge.png")
        #else:
        background_image = Image.open("other/haloween.png")
        background_image = background_image.convert('RGBA') # add channel ALPHA to draw transparent rectangle
#            image = Image.open('Cockatoo-min.png')
        AVATAR_SIZE = 256

        # --- duplicate image ----

        image = background_image.copy()


        # --- draw on image ---


        draw = ImageDraw.Draw(image)

# CREATE YOUR FILL COLOUR HERE (CHANGE TO 245 AT END OF EVENT)
        color=(202,98,45)
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

        text_width_exp, text_height = draw.textsize(str(member["exp"]), font=font_60)
        x = 1300
        y = 325
        

        draw.text((x, y), str(member["exp"]), fill=(255,255,255, 255), font=font_60)
        
        draw.text((x + text_width_exp, y), " / " + str(member["total_exp_next_display"]), fill=(149,149,149, 255), font=font_60)


        # Draw User's Level
        x = 1105 + AVATAR_SIZE
        y = 150
        draw.text((x, y), "Level", fill=(149,149,149, 255), font=font_60)


        text_width_level, text_height_level = draw.textsize("Level", font=font_75)
        draw.text((x + text_width_level, y - 30), str(member["level"]), fill=(255,255,255, 255), font=font_90)
        
        
        # --- avatar ---
        # get URL to avatar
        # sometimes `size=` doesn't gives me image in expected size so later I use `resize()`
        avatar_asset = author.avatar_url_as(format='jpg', size=AVATAR_SIZE)

        # read JPG from server to buffer (file-like object)
        buffer_avatar = io.BytesIO(await avatar_asset.read())


        # read JPG from buffer to Image
        avatar_image = Image.open(buffer_avatar)

        # resize it
        avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE)) #
        circle_image = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
        circle_draw = ImageDraw.Draw(circle_image)
        circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
        image.paste(avatar_image, (20, 20), circle_image)

        buffer_output = io.BytesIO()
        image.save(buffer_output, format='PNG')

        # move to beginning of buffer so `send()` it will read from beginning
        buffer_output.seek(0)

        # send image
        await ctx.send(file=File(buffer_output, 'card.png'))




    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        user = getcache_leveling(message.author.id, message.guild.id)
        user = {"guilds": user[0], "exp": user[1]}
        passed = False
        for i in range(len(user["guilds"])):
            if user["guilds"][i] == message.guild.id:
                passed = True
                iteration = i
                total_exp = user["exp"][i]
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


                member = {"guild": user["guilds"][i], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining
        if not passed:

            cache[message.author.id][0].append(message.guild.id)
            cache[message.author.id][1].append(1)
            for i in range(len(cache[message.author.id][0])):
                if cache[message.author.id[0][i]] == message.guild.id:
                    iteration = i

            member = {"guild": message.guild.id, "level": 1, "total_exp": 1, "total_exp_next_actual": 100, "total_exp_next_display": 100, "remaining": 99, "exp": 1}
        x = cooldown.get(message.author.id)
        if x is not None:
            return
        cooldown[message.author.id] = True
        increase = random.randint(15, 20)
        cache[message.author.id][1][iteration] += increase
        if increase >= remaining:
            await message.channel.send(f"**{message.author.name}** Has Leveled Up To Level **{member['level'] + 1}**!")







#Cache Operations Are Below Here
#Please Note that cache.clear() breaks it so do not EVER use. Iterate Through Cache.pop when shutting down.
    @commands.is_owner()
    @commands.command(name="cacheclear")
    async def _cacheclear(self, ctx):
        await ctx.send("Clearing Cache...")
        for i in range(cache.currsize):
            print(i)
            cache.popitem()
        await ctx.send("Cache Has Been Emptied")


    @commands.is_owner()
    @commands.command(name="cache")
    async def _cache(self, ctx):
        await ctx.send("Printing Cache...")
        print(cache)


    @commands.is_owner()
    @commands.command(name="cachepop")
    async def _cachepop(self, ctx):
        print(cache)
        await ctx.send("Popping Cache...")
        cache.popitem()



        


def setup(bot):
    bot.add_cog(Slash(bot))
