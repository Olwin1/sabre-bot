import asyncio
import functools
import io
import itertools
import math
import random
import socket
import threading
import urllib
from asyncio import tasks
from datetime import datetime, timedelta

import async_timeout
import discord
import psycopg
import youtube_dl
from async_timeout import timeout
from cachetools import LRUCache, TTLCache, cached
from discord import File
from discord.ext import commands, tasks
from discord_slash import SlashContext, cog_ext
from PIL import Image, ImageDraw, ImageFont
from youtube_dl.utils import DownloadError

# Silence useless bug reports messages for Music
youtube_dl.utils.bug_reports_message = lambda: ''

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
conn = psycopg.connect(dbname="sabre", user="postgres", password="jumper123", host="localhost")

guild_ids = [704255331680911402]
print("levleing is runnin")
cooldown = TTLCache(maxsize=1024, ttl=20)

class MemberCache(LRUCache):# Handles Deletions Of Member Rows
  def popitem(self):
    cur = conn.cursor()
    if super().currsize == 0:
        return None, None
    key, value = super().popitem()
    print('Key "%s" evicted with value "%s"' % (key, value))
    key = key.split(":")
    cur.execute("UPDATE members SET exp = %s, infraction_description = %s, infraction_date = %s WHERE user_id=%s AND guild_id=%s", (value["exp"], value["infraction_description"], value["infraction_date"], key[0], key[1]))# VALUE 0 IS THE GUILDS IF A NEW ONE REMEMBER TO ADD IT
    conn.commit()
    return key, value


class GuildCache(LRUCache):# Handles Deletions Of Guild Rows
  def popitem(self):
    cur = conn.cursor()
    if super().currsize == 0:
        return None, None
    key, value = super().popitem()
    print('Key "%s" evicted with value "%s"' % (key, value))
    cur.execute("UPDATE guilds SET role_rewards = %s WHERE guild_id=%s", (value["role_rewards"], key))#IF A NEW COLUMN REMEMBER TO ADD IT
    conn.commit()
    return key, value




member_cache = MemberCache(maxsize=100)# Actual Creation Of The Member and Guild Cache
guild_cache = GuildCache(maxsize=100)

@cached(cache=TTLCache(maxsize=1024, ttl=3600))# Cache To Store Member's Rank Compared To Others.  Instead Of Updating Just Deletes It After 60 Mins And Re-Orders It When Needed.
def get_member_rank(key):
    cur = conn.cursor()
    key = key.split(":")
    cur.execute("SELECT user_id FROM members WHERE guild_id=%s ORDER BY exp ASC", (key[1],))
    res = cur.fetchall()
    for i, row in enumerate(res):
        if row[0] == int(key[0]):
            return i + 1
    return 999

# This Function Gets The Member Data From The Cache. IF It Is Not In The Cache It Fetches It and If It Cannot Be Found It Creates It.
def get_member(user_id, guild_id):
    retval = member_cache.get(f"{user_id}:{guild_id}")
    if retval is None:

        cur = conn.cursor()
        cur.execute("SELECT exp, infraction_description, infraction_date FROM members WHERE user_id=%s and guild_id=%s", (user_id,guild_id))
        selected = cur.fetchone()
        if selected is None:# If Member Is Not Found
            cur.execute("SELECT EXISTS(SELECT * FROM users WHERE id=%s)", (user_id,))# If User Is Not Found Create Them.
            res = cur.fetchone()
            if not res[0]:
                cur.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
                
                
            cur.execute("SELECT EXISTS(SELECT * FROM guilds WHERE id=%s)", (guild_id,))#If Guild Is Not Found Create It.
            res = cur.fetchone()
            if not res[0]:
                cur.execute("INSERT INTO guilds (id) VALUES (%s)", (guild_id,))


            cur.execute("INSERT INTO members (user_id, guild_id, exp) VALUES (%s, %s, %s)", (user_id, guild_id, 1))# Create Member.
            conn.commit()
            
            
            cur.execute("SELECT exp, infraction_description, infraction_date FROM members WHERE user_id=%s and guild_id=%s", (user_id, guild_id))
            selected = cur.fetchone()
            retval = {"user_id": user_id, "guild_id": guild_id, "exp": selected[0], "infraction_description": selected[1], "infraction_date": selected[2]}
            member_cache[f"{user_id}:{guild_id}"] = retval
        if selected[0] is None:# If EXP Is Not Exist
            cur.execute("UPDATE members SET exp = %s WHERE user_id=%s AND guild_id=%s", (1,user_id,guild_id))
            conn.commit()
            cur.execute("SELECT exp, infraction_description, infraction_date FROM members WHERE user_id=%s and guild_id=%s", (user_id,guild_id))
            selected = cur.fetchone()
            
        retval = {"user_id": user_id, "guild_id": guild_id, "exp": selected[0], "infraction_description": selected[1], "infraction_date": selected[2]}
        member_cache[f"{user_id}:{guild_id}"] = retval

    return retval




def get_guild(guild_id):
    retval = guild_cache.get(guild_id)
    if retval is None:

        cur = conn.cursor()
        cur.execute("SELECT role_rewards, toggle_moderation,  toggle_automod, toggle_welcomer, toggle_autoresponder, toggle_leveling, toggle_autorole, toggle_reactionroles, toggle_music, toggle_modlog, automod_links, automod_invites, automod_mention, automod_swears FROM guilds WHERE id=%s", (guild_id,))
        selected = cur.fetchone()
        if selected is None:# If Guild Is Not Found... Create It
            cur.execute("INSERT INTO guilds (id) VALUES (%s)", (guild_id,))
            conn.commit()
            
            
        retval = {
            "guild_id": guild_id, 
            "role_rewards": selected[0],
            "toggle": {
                "moderation": selected[1], 
                "automod": selected[2], 
                "welcomer": selected[3], 
                "autoresponder": selected[4], 
                "leveling": selected[5], 
                "autorole": selected[6], 
                "reactionroles": selected[7], 
                "music": selected[8], 
                "modlog": selected[9]
                },
            "automod": {
                "links": selected[10],
                "invites": selected[11],
                "mention": selected[12],
                "swears": selected[13]
                }
            }
        guild_cache[guild_id] = retval

    return retval




  #Each Cog In In The Same File In Order To Share The Cache But They Are Still Individual Cogs And Can Be Enabled & Disabled
  
  #The First One Is The Leveling Cog As Defined In the Class Below.  Everything Inside That Class Is To Do With Leveling
class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        with open('./other/blocked_words.txt') as f:
            self.blocked_words = f.read().splitlines()
            f.close()
        
        
    def __del__(self):
        print("Clearing Cache...")
        for i in range(member_cache.currsize):
            member_cache.popitem()
        for i in range(guild_cache.currsize):
            guild_cache.popitem()
        print("Cache Has Been Emptied!")




    @cog_ext.cog_slash(name="rank", guild_ids=guild_ids)
    async def _rank(self, ctx: SlashContext, member: discord.Member=None):
        '''Display Your Rank Card'''
        if member is None:
            author = ctx.author
        else:
            author = member
        member = get_member(author.id, ctx.guild.id)


        total_exp = member["exp"]
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
        draw.text((x + text_width_level, y - 30), str(get_member_rank(f"{author.id}:{author.guild.id}")), fill=(250,250,250, 250), font=font_75)
        
        
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

        member = get_member(message.author.id, message.guild.id)
        
        guild = get_guild(message.guild.id)
        
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

        total_exp = member["exp"]
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


        member = {"guild": member["guild_id"], "level": level, "total_exp": total_exp, "total_exp_next_actual": total_exp_next_actual, "total_exp_next_display": total_exp_next_display, "remaining": remaining, "exp": total_exp_next_display - remaining}
                #guild, level, total_exp, total_exp_next_actual, total_exp_next_display, remaining

        x = cooldown.get(message.author.id)
        if x is not None:
            return
        cooldown[message.author.id] = True
        increase = random.randint(15, 20)
        member_cache[f"{message.author.id}:{message.guild.id}"]["exp"] += increase
        if increase >= remaining:
            await message.channel.send(f"**{message.author.name}** Has Leveled Up To Level **{member['level'] + 1}**!")







  #Cache Operations Are Below Here
  #Please Note that cache.clear() breaks it so do not EVER use. Iterate Through Cache.pop when shutting down.
    @commands.is_owner()
    @commands.command(name="cacheclear")
    async def _cacheclear(self, ctx):
        await ctx.send("Clearing Cache...")
        for i in range(member_cache.currsize):
            member_cache.popitem()
            
        for i in range(guild_cache.currsize):
            guild_cache.popitem()
            
        await ctx.send("Guild and Member Cache Has Been Emptied")


    @commands.is_owner()
    @commands.command(name="cache")
    async def _cache(self, ctx):
        await ctx.send("Printing Cache...")
        print(member_cache)
        print("--- Above Is Member Below Is Guild ---")
        print(guild_cache)
        
    @commands.is_owner()
    @commands.command(name="cachepop")
    async def _cachepop(self, ctx):
        print(member_cache)
        await ctx.send("Popping Cache...")
        member_cache.popitem()



        


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

        self.countdown.start()
           
        self.ban_list = []
        self.ban_time_list = []
        self.ban_guild_list = []
        
        
        self.mute_list = []
        self.mute_time_list = []
        self.mute_guild_list = []
        

    #This is a background process
    @tasks.loop()
    async def countdown(self):

        await self.bot.wait_until_ready()# Do not Start Unless Bot Is Fully Online

        while not self.bot.is_closed():# While Active

            await asyncio.sleep(1)# Wait A Sec


            for day in self.ban_time_list:
                if day <= datetime.now():
                    try:
                        await self.ban_list[self.ban_time_list.index(day)].unban()
                    except:
                        print('Error! User already unbanned!')
                    del self.ban_list[self.ban_time_list.index(day)]# Remove user From Timer
                    del self.ban_guild_list[self.ban_time_list.index(day)]
                    del self.ban_time_list[self.ban_time_list.index(day)]
                    
            for day in self.mute_time_list:
                if day <= datetime.now():
                    try:
                        for role in self.mute_list[self.mute_time_list.index(day)].guild.roles:
                            if role.name == "Muted":
                                await self.mute_list[self.mute_time_list.index(day)].remove_roles(role)
                    except:
                        print('Error! User already unmuted!')
                    del self.mute_list[self.mute_time_list.index(day)]# Remove user From Timer
                    del self.mute_guild_list[self.mute_time_list.index(day)]
                    del self.mute_time_list[self.mute_time_list.index(day)]
                
    #Command starts here
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(ban_members = True)
    async def ban(self, ctx: SlashContext,member:discord.Member, days : int = None, hours : int = None, mins : int = None, reason = "The Ban Hammer Has Spoken!"):
        '''Ban a User'''
        if ctx.author.top_role.position > member.top_role.position:# If Author Has Higher Role Than Person They Are Trying To Ban.  So Mods Can't Ban Admins or Mods Can't Ban Other Mods
            if days or hours or mins:# If Time Is Provided
                try:
                    delay = 0
                    if hours:# Converts Mins, Days and Hours Into A Seconds Total
                        delay += hours * 60 * 60
                    if mins:
                        delay += mins * 60
                    if days:
                        delay += days * 24 * 60 * 60
                        
                        
                    timer = datetime.now()
                    timer += timedelta(seconds=delay)
                    await ctx.guild.ban(member, delete_message_days=0, reason=reason)# Actually Bans The User
                    comma = ""
                    if not days:# Removes The Comma After Days If There Are No Days
                        comma = ""
                    await ctx.send(f'**{member.mention}** Has Been Banned for {f"**{days} day(s)** " if days else ""}{f"{comma} **{hours} hour(s) **" if hours else ""}{f"and **{mins} min(s)**" if mins else ""}.  For **{reason}**.  By **{ctx.author.mention}**')
                    self.ban_list.append(member)# Add Member To The Unban Timer.
                    self.ban_time_list.append(timer)
                    self.ban_guild_list.append(ctx.guild.id)
                except:
                    await ctx.send('Error! Ban Failed')
            else:
                try:
                    await ctx.guild.ban(member, delete_message_days=0, reason=reason)# If No Duration Specified Just Straight Up Ban 'em
                    await ctx.send(f'**{member.mention}** Has Been Banned For **{reason}**')
                except:
                    await ctx.send("Error! Ban Failed")
                    
        else:
            await ctx.send('You do not have permission to ban users!')
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def mute(self, ctx, member: discord.Member, reason=None, days : int = None, hours : int = None, mins : int = None):
        '''Mute a User'''
        role = discord.utils.get(member.guild.roles, name="Muted") # retrieves muted role returns none if there isn't 
        if not role: # checks if there is muted role
            muted = await member.guild.create_role(name="Muted", reason="To use for muting")
            for channel in member.guild.channels: # removes permission to view and send in the channels 
                await channel.set_permissions(muted, send_messages=False, speak=False)
        for role in member.guild.roles:
            if role.name == "Muted":
                if days or hours or mins:# If Time Is Provided
                    delay = 0
                    if hours:# Converts Mins, Days and Hours Into A Seconds Total
                        delay += hours * 60 * 60
                    if mins:
                        delay += mins * 60
                    if days:
                        delay += days * 24 * 60 * 60
                        
                        
                    timer = datetime.now()
                    timer += timedelta(seconds=delay)
                    msg = f"{f'{days} Days(s), ' if days else ''}{f'{hours} Hours(s), ' if hours else ''}{f'{mins} Mins(s)' if mins else ''}"
                    await member.add_roles(role)
                    self.mute_list.append(member)# Add Member To The Unban Timer.
                    self.mute_time_list.append(timer)
                    self.mute_guild_list.append(ctx.guild.id)
                    embed = discord.Embed(title="User Has Been Muted!", colour=0xffb6f2)
                    embed.add_field(name="User", value=member.mention, inline=True)
                    embed.add_field(name="Reason:", value=reason, inline=True)
                    embed.add_field(name="Duration:", value=msg, inline=True)
                    embed.add_field(name="Muted By", value=ctx.author.mention, inline=True)
                    await ctx.send(embed=embed)
                    return
                    
                    
                await member.add_roles(role)
                embed = discord.Embed(title="User Has Been Muted!", colour=0xffb6f2)
                embed.add_field(name="User", value=member.mention, inline=True)
                embed.add_field(name="Reason:", value=reason, inline=True)
                embed.add_field(name="Muted By", value=ctx.author.mention, inline=True)
                await ctx.send(embed=embed)
    
                return
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def unmute(self, ctx, member: discord.Member):
        '''Unmute a User'''
        role = discord.utils.get(member.guild.roles, name="Muted") # retrieves muted role returns none if there isn't 
        if not role: # checks if there is muted role
            muted = await member.guild.create_role(name="Muted", reason="To use for muting")
            for channel in member.guild.channels: # removes permission to view and send in the channels 
                await channel.set_permissions(muted, send_messages=False, speak=False)
        for role in member.guild.roles:
            if role.name == "Muted":
                await member.remove_roles(role)

                await ctx.send(f"{member.mention} Has Been Unmuted.")
    
                return
            
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, member : discord.Member, reason = None):
        '''Kick a User'''
        if ctx.author.top_role.position > member.top_role.position:
            
            await member.kick(reason=reason)
            embed=discord.Embed(title="User Has Been Kicked!", color=0xffb6f2)

            embed.add_field(name=f"User", value=member.mention, inline=True)
            embed.add_field(name=f"Kicked By", value=ctx.author.mention, inline=True)
            embed.add_field(name=f"Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            try:
                if len(member.mutual_guilds) != 0:
                    msg = f"You Have Been Kicked From **{ctx.author.guild.name}** For **{reason}** By **{ctx.author.display_name}#{ctx.author.discriminator}**"
                    await member.send(msg)
            except:
                print("DM FAILED")
            
        else:
            await ctx.send("ERROR! This User Has A More Senior Role Than You!")
            
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    async def warn(self, ctx, member : discord.Member, reason):
        '''Warn a User'''
        if len(reason) > 150:
            await ctx.send(f"Your Warn Reason Cannot Be Longer Than 150 Characters. (Currently {len(reason)})", hidden=True)
            return
        cache = get_member(member.id, ctx.guild.id)
        if not cache["infraction_description"]:
            cache["infraction_description"] = []
            cache["infraction_date"] = []

            
        cache["infraction_description"].append(reason)
        cache["infraction_date"].append(datetime.now().date())
        await ctx.send(f'{member.mention} Has Been Warned For: **{reason}**')
        
        
    @cog_ext.cog_slash(guild_ids=guild_ids)
    async def infractions(self, ctx, member : discord.Member):
        '''Get A List Of Infractions Of a User'''
        cache = get_member(member.id, ctx.guild.id)
        if not cache["infraction_description"]:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name=f"{member.display_name}#{member.discriminator} Has No Infractions", icon_url=member.avatar_url)
            await ctx.send(embed=embed)
            return
        else:
            index = len(cache["infraction_date"]) - 1# Since Indexes Start At 0 & Length Starts At 1 It Is The Index Of The element To Be Added
            
        cache["infraction_description"]
        cache["infraction_date"].append(datetime.now().date())
        embed=discord.Embed(color=0xffb6f2)
        embed.set_author(name=f"{member.display_name}#{member.discriminator} Has {len(cache['infraction_description'])} Infractions", icon_url=member.avatar_url)
        for i, infraction in enumerate(cache["infraction_description"]):# Iterate Over The Infractions
            if i >= 10:# To Limit The Infractions Displayed To 10
                break
            embed.add_field(name="⠀", value=f"**{infraction}** • {cache['infraction_date'][i].strftime('%d/%m/%y')}", inline=False)
        embed.set_footer(text="Showing The Most Recent 10")
        await ctx.send(embed=embed)
        
    @cog_ext.cog_slash(name="clear-infractions", guild_ids=guild_ids)
    async def _clearinfractions(self, ctx, member : discord.Member):
        '''Clear All Infractions Of A Specified User'''
        cache = get_member(member.id, ctx.guild.id)
        cache["infraction_description"] = None# Set All Infractions Back To None or NULL
        cache["infraction_date"] = None
        await ctx.send(f"Cleared All Infractions Of {member.mention}")
        
        
    @cog_ext.cog_slash(guild_ids=guild_ids)
    async def slowmode(self, ctx, channel : discord.TextChannel, seconds : int):
        '''Add A Cooldown To Text Channels'''
        if seconds > 21600:
            await ctx.send("Time Must Be Less That 21600 Seconds", hidden=True)
        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(f"Disabled Slowmode in {channel.mention}")
            return
        await ctx.send(f"Set The Slowmode Delay to {seconds} Seconds in {channel.mention}")
    


            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(manage_channels=True)
    async def lock(ctx, channel : discord.TextChannel=None):
        '''Lock A Channel.  Blocks The Default Role From Sending Messages.'''
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f'{channel.mention} Locked.')
            
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(manage_messages = True)# Must be Able To Delete Messages Themselves
    async def clear(self, ctx, amount):
        try:
            amount = int(amount)# Makes Sure It Is a Number
        except ValueError:
            await ctx.send("Amount must Be A Number", hidden=True)
            
        limited = False
        if amount > 100:# Maxes Out At 100
            amount = 100
            limited = True# Points That Out If It Has Been Capped
            
        after = datetime.now() - timedelta(days = 14) 
        x = await ctx.channel.purge(limit=amount, bulk=True, after=after)# Actually Delete Messages
        if x == []:
            await ctx.send("Due To Discord Limitations Bulk Delete Only Works For Messages Less Than Two Weeks Old.", hidden=True)
            return
        if limited:
            await ctx.send("Successfully Deleted 100 Messages. (Max Of 100 At A Time)", hidden=True)
        else:
            await ctx.send(f"Successfully Deleted {amount} Messages.", hidden=True)
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    async def server(self, ctx):
        embed=discord.Embed(color=0xffb6f2)# Make It Purple
        embed.set_thumbnail(url=ctx.guild.icon_url)# Sets The Thumbnail To Guild Icon
        embed.add_field(name="Owner", value=f"<@!{ctx.guild.owner_id}>", inline=True)# Mention Guild Owner
        embed.add_field(name="Region", value=ctx.guild.region, inline=True)# Show Region (Set In Guild Settings)
        embed.add_field(name="Server Created On", value=ctx.guild.created_at.strftime("%d/%m/%y"), inline=True)# Convert Datetime Object To DD/MM/YYYY Format
        embed.add_field(name="Total Roles", value=len(ctx.guild.roles), inline=True)
        embed.add_field(name="Total Members", value=ctx.guild.member_count, inline=True)
        embed.add_field(name="Channels", value=f"Total: {len(ctx.guild.channels)}, \nText: {len(ctx.guild.text_channels)}, \nVoice: {len(ctx.author.guild.voice_channels)}", inline=True)
        embed.add_field(name="Boost Level", value=ctx.guild.premium_tier, inline=True)# Show Nitro Boost Level
        embed.add_field(name="Number Of Boosts", value=ctx.guild.premium_subscription_count, inline=True)
        embed.set_footer(text=f"Guild Name: {ctx.guild.name} || GuildID: {ctx.guild.id}")# Add A Footer Showing Guild Name & ID
        await ctx.send(embed=embed)# Finally Send Message
        
        
#####################################################
######EVERYTHING BELOW HERE IS MUSIC. BE WARNED!#####
#####################################################

class VoiceError(Exception):
    pass
class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')



    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)



    @classmethod
    async def create_source(cls, ctx, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        print(partial)
        
        try:
            data = await loop.run_in_executor(None, partial)
        except DownloadError:
            raise YTDLError("Oh No! Nothing Was Found On That Search Term (Try Rephrasing) :(")

        if data is None:
            raise YTDLError("Oh No! Nothing Was Found On That Search Term (Try Rephrasing) :(")

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError("Oh No! Nothing Was Found On That Search Term (Try Rephrasing) :(")

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        #print(f"{cls.ytdl.extract_info} ---------- {webpage_url}")
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Oh No! I Couldn\'t fetch the audio')

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Oh No! I Couldn\'t retrieve any matches for the audio!')

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{}:'.format(days))
        if hours > 0:
            duration.append('{}:'.format(hours))
        if minutes > 0:
            duration.append('{}:'.format(minutes))

        if seconds < 10:
            duration.append('0{}'.format(seconds))
        else:
            duration.append('{}'.format(seconds))

        return ''.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        millnames = ['','K',' Mil',' Bil',' Trill']# Names For Shortenings
        
        n = float(self.source.likes)
        millidx = max(0,min(len(millnames)-1,
                            int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))# Get Likes
        likes = '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])###

        n = float(self.source.views)
        millidx = max(0,min(len(millnames)-1,
                            int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))# Get Views
        views = '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


        upload_date = self.source.upload_date.replace(".", "/")

        #Embed Begins Here
                    


        background_image = Image.open("./other/music/playbg.png")  # it doesn't need `io.Bytes` because it `response` has method `read()`
        background_image = background_image.convert('RGBA') # add channel ALPHA to draw transparent rectangle

        # --- duplicate image ----

        image = background_image.copy()

        # --- draw on image ---
        draw = ImageDraw.Draw(image)


        text = '{0.source.title}'.format(self)
        text = text[:20] + '\n' + text[20:]
        text = text[:40] + '\n' + text[40:]
        text = text[:60] + '\n' + text[60:]
        text = text[:80] + '\n' + text[80:]
        text = text[:100] + '\n' + text[100:]

        font_40 = ImageFont.truetype('./other/fonts/Quicksand-Medium.ttf', 40)
        font_30 = ImageFont.truetype('./other/fonts/Quicksand-Medium.ttf', 30)

        
        draw.text((50, 100), text, fill=(255,255,255, 255), font=font_40) # Song Title


        y = 470# Standard Height For All Text
        draw.text((30, y), self.source.duration, fill=(255,255,255, 255), font=font_30)# Duration
        
        draw.text((230, y), views, fill=(255,255,255, 255), font=font_30)# View Count

        draw.text((400, y), likes, fill=(255,255,255, 255), font=font_30)# Like Count

 #Uploaded By

        text = self.source.uploader
        text = text[:13] + '\n' + text[13:]
        text = text[:26] + '\n' + text[26:]
        text = text[:39] + '\n' + text[39:]
        text = text[:52] + '\n' + text[52:]
        text = text[:65] + '\n' + text[65:]


            

        draw.text((560, y), text, fill=(255,255,255, 255), font=font_30)# Uploader Name


        draw.text((830, y), upload_date, fill=(255,255,255, 255), font=font_30)# Upload Date


            # --- avatar ---
        response = urllib.request.urlopen(self.source.thumbnail)
        thumbnail = Image.open(response)  # it doesn't need `io.Bytes` because it `response` has method `read()`
        thumbnail = thumbnail.convert('RGBA') # add channel ALPHA to draw transparent rectangle

            # read JPG from buffer to Image

            # resize it

        newsize = (384, 216)
        thumbnail = thumbnail.resize(newsize)
        image.paste(thumbnail, (600, 120))

        buffer_output = io.BytesIO()
        image.save(buffer_output, format='PNG')

            # move to beginning of buffer so `send()` it will read from beginning
        buffer_output.seek(0)

            # send image
        return File(buffer_output, 'play.png')


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.exists = True

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player_task.start()

    def __del__(self):
        self.audio_player_task.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    @tasks.loop()
    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop == False:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(file=self.current.create_embed())
            
            #If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **self.source.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        try:
            self.next.set()
        except:
            pass

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True


    async def cog_command_error(self, ctx, error: commands.CommandError):
        await ctx.send('**ERROR:** {}'.format(str(error)))

    @cog_ext.cog_slash(name='join', guild_ids=guild_ids)
    async def _join(self, ctx):
        """Joins a voice channel."""
        ctx.voice_state = self.get_voice_state(ctx)


        destination = ctx.author.voice.channel

        if ctx.voice_state.voice:
            await ctx.voice_state.voice.disconnect()
        if ctx.voice_state.voice == None:
            ctx.voice_state.voice = discord.Guild.voice_client
        else:
            await ctx.voice_state.voice.disconnect()


        ctx.voice_state.voice = await destination.connect()

        embed=discord.Embed(title="Joined Voice Channel", color=0xffb6f2)
        await ctx.send(embed=embed)
        return

        ctx.voice_state.voice = await destination.connect()

    @cog_ext.cog_slash(name='summon', guild_ids=guild_ids)
    async def _summon(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Summons Sabre to a voice channel.
        """
        ctx.voice_state = self.get_voice_state(ctx)

        if not channel and not ctx.author.voice:
            raise VoiceError('You have not specified/joined a voice channel')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name=f"Moved To {destination}")
            await ctx.send(embed=embed)

            return

        ctx.voice_state.voice = await destination.connect()

    @cog_ext.cog_slash(name='leave', guild_ids=guild_ids)
    async def _leave(self, ctx):
        """Clears the queue and leaves the voice channel."""
        ctx.voice_state = self.get_voice_state(ctx)


        try:
            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="⏹️ Playback Stopped")
            await ctx.send(embed=embed)

        except:
            await ctx.send('Not connected to any voice channel.', hidden=True)



    @cog_ext.cog_slash(name='now', guild_ids=guild_ids)
    async def _now(self, ctx):
        """⏏️ Displays the currently playing song."""
        
        ctx.voice_state = self.get_voice_state(ctx)

        if ctx.voice_state.current is None:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="⏏️ Nothing Playing.")
            await ctx.send(embed=embed)
            return
        await ctx.send("Generating...")
        await ctx.send(file=ctx.voice_state.current.create_embed())

    @cog_ext.cog_slash(name='pause', guild_ids=guild_ids)
    async def _pause(self, ctx):
        """⏸️ Pauses the currently playing song."""
        ctx.voice_state = self.get_voice_state(ctx)

        if ctx.voice_state.is_playing or ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="⏸️ Playback Paused.")
            await ctx.send(embed=embed)
        else:
            await ctx.send("Music Is Already Paused.", hidden=True)

    @cog_ext.cog_slash(name='resume', guild_ids=guild_ids)
    async def _resume(self, ctx):
        """▶️ Resumes a currently paused song."""
        ctx.voice_state = self.get_voice_state(ctx)

        if ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="▶️ Playback Resumed.")
            await ctx.send(embed=embed)
        else:
            await ctx.send("Song Is Not Paused.", hidden=True)




    @cog_ext.cog_slash(name='skip', guild_ids=guild_ids)
    async def _skip(self, ctx: commands.Context):
        """⏭ Vote to skip a song."""
        ctx.voice_state = self.get_voice_state(ctx)

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            embed=discord.Embed(color=0xffb6f2)

            if total_votes >= 3:
                embed.set_author(name=f"⏩︎ Song Skipped.")
                await ctx.send(embed=embed)

                ctx.voice_state.skip()
            else:
                embed.set_author(name='Skip Vote Registered. (**{}/3**)'.format(total_votes))
                await ctx.send(embed=embed)
                await ctx.send('You Have Voted To Skip The Current Song (**{}/3**)'.format(total_votes))

        else:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="You have already voted to skip this song.", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)


    @cog_ext.cog_slash(name='queue', guild_ids=guild_ids)
    async def _queue(self, ctx, *, page: int = 1):
        """Show the song queue."""
        ctx.voice_state = self.get_voice_state(ctx)

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue, color=0xffb6f2))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name='shuffle', guild_ids=guild_ids)
    async def _shuffle(self, ctx):
        """🔀 Shuffle the queue."""
        ctx.voice_state = self.get_voice_state(ctx)

        if len(ctx.voice_state.songs) == 0:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="The Queue Is Empty.")
            return await ctx.send(embed=embed)

        ctx.voice_state.songs.shuffle()
        embed=discord.Embed(color=0xffb6f2)
        embed.set_author(name=f"🔀 Shuffled The Queue")
        await ctx.send(embed=embed)


    @cog_ext.cog_slash(name='remove')
    async def _remove(self, ctx, index: int):
        """Removes a song from the queue at a given index."""
        ctx.voice_state = self.get_voice_state(ctx)

        if len(ctx.voice_state.songs) == 0:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name="The Queue Is Empty.")
            return await ctx.send(embed=embed)
        elif len(ctx.voice_state.songs) < index:
            await ctx.send("Index Doesn't Exist.", hidden=True)
            return

        ctx.voice_state.songs.remove(index - 1)
        embed=discord.Embed(color=0xffb6f2)
        embed.set_author(name=f"❌ Removed {index} From Queue.")
        await ctx.send(embed=embed)


    @cog_ext.cog_slash(name='loop', guild_ids=guild_ids)
    async def _loop(self, ctx):
        """Loops the currently playing song."""
        ctx.voice_state = self.get_voice_state(ctx)

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        embed=discord.Embed(color=0xffb6f2)
        embed.set_author(name=f"🔄 Loop Mode {'Enabled' if ctx.voice_state.loop else 'Disabled'}")
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name='play', guild_ids=guild_ids)
    async def _play(self, ctx, search: str):
        """Plays a song. New Songs Are Added To A Queue"""
        ctx.voice_state = self.get_voice_state(ctx)
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        else:
            await ctx.send("Searching...")

        
        try:
            source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        except YTDLError as e:
            await ctx.send(str(e), hidden=True)
        else:


            song = Song(source)
            await ctx.voice_state.songs.put(song)
            if ctx.voice_state.songs:
                if len(ctx.voice_state.songs) > 1:
                    await ctx.send('Enqueued {}'.format(str(source)))






def setup(bot):# Here Is Where The Cogs Are Added. All Cog Classes MUST Be Linked Here In Order to Be Added.
    bot.add_cog(Leveling(bot))
    bot.add_cog(Moderation(bot))
    bot.add_cog(Music(bot))
    


