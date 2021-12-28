import asyncio
from datetime import datetime, timedelta

import discord
import requests
from discord.ext import commands, tasks
from discord_slash import SlashContext, cog_ext
from modules import cache_get as cache

guild_ids = [704255331680911402]

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.countdown.start()
           
        self.ban_list = []
        self.ban_time_list = []
        self.ban_guild_list = []
        
             
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
        guild = cache.get_guild(ctx.guild.id)
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
                    if guild["toggle"]["modlog"]:
                        if guild["modlog"]["channel"] and guild["modlog"]["bans"]:
                            channel = self.bot.get_channel(guild["modlog"]["channel"])
                            if not channel:
                                guild["modlog"]["channel"] = None
                                return
                            embed=discord.Embed(title="User Ban Event", description=f"{member.display_name}#{member.discriminator} Has Been Banned", color=0x4d003c)
                            embed.add_field(name="Banned By:", value=ctx.author.mention, inline=False)
                            embed.add_field(name="Ban Reason:", value=reason, inline=True)
                            embed.add_field(name="Ban Duration", value=f'{f"**{days} day(s)** " if days else ""}{f"{comma} **{hours} hour(s) **" if hours else ""}{f"and **{mins} min(s)**" if mins else ""}', inline=True)
                            await channel.send(embed=embed)
                except:
                    await ctx.send('Error! Ban Failed')
            else:
                try:
                    await ctx.guild.ban(member, delete_message_days=0, reason=reason)# If No Duration Specified Just Straight Up Ban 'em
                    await ctx.send(f'**{member.mention}** Has Been Banned For **{reason}**')
                    if guild["toggle"]["modlog"]:# Modlog For Ban Command
                        if guild["modlog"]["channel"] and guild["modlog"]["bans"]:
                            channel = self.bot.get_channel(guild["modlog"]["channel"])
                            if not channel:
                                guild["modlog"]["channel"] = None
                                return
                            embed=discord.Embed(title="User Ban Event", description=f"{member.display_name}#{member.discriminator} Has Been Banned", color=0x4d003c)
                            embed.add_field(name="Banned By:", value=ctx.author.mention, inline=False)
                            embed.add_field(name="Ban Reason:", value=reason, inline=True)
                            embed.add_field(name="Ban Duration", value="Permanent", inline=True)
                            await channel.send(embed=embed)
                except:
                    await ctx.send("Error! Ban Failed")
                    
        else:
            await ctx.send('You do not have permission to ban users!')
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def mute(self, ctx, member: discord.Member, reason=None, days : int = None, hours : int = None, mins : int = None):
        '''Mute a User. Defaults To 5 Mins'''

        guild = cache.get_guild(ctx.guild.id)
        delay = 0
        if hours:# Converts Mins, Days and Hours Into A Seconds Total
            delay += hours * 60 * 60
        if mins:
            delay += mins * 60
        if days:
            delay += days * 24 * 60 * 60
        
        if delay > 2419199:
            delay = 2419199
            hours = 23
            mins = 59
            days = 27
        elif delay == 0:
            delay = 5 * 60
            mins = 5
                
                
            msg = f"{f'{days} Days(s), ' if days else ''}{f'{hours} Hours(s), ' if hours else ''}{f'{mins} Mins(s)' if mins else ''}"
            
            
        headers = {"Authorization": f"Bot {self.bot.http.token}"}# Set Headers
        url = f"https://discord.com/api/v9/guilds/{ctx.guild.id}/members/{member.id}"# Send Request To Mute User
        timeout = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
        json = {'communication_disabled_until': timeout}
        session = requests.patch(url, json=json, headers=headers)
        if session.status_code in range(200, 299):# When Mute Is Successful
            embed = discord.Embed(title="User Has Been Muted!", colour=0xffb6f2)
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Reason:", value=reason, inline=True)
            embed.add_field(name="Duration:", value=msg, inline=True)
            embed.add_field(name="Muted By", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)
            if guild["toggle"]["modlog"]:
                if guild["modlog"]["channel"] and guild["modlog"]["mutes"]:
                    channel = self.bot.get_channel(guild["modlog"]["channel"])
                    if not channel:
                        guild["modlog"]["channel"] = None
                        cache.update_guild(guild)
                        return
                    embed=discord.Embed(title="User Mute Event", description=f"{member.display_name}#{member.discriminator} Has Been Muted", color=0x4d003c)
                    embed.add_field(name="Muted By:", value=ctx.author.mention, inline=False)
                    embed.add_field(name="Mute Reason:", value=reason, inline=True)
                    embed.add_field(name="Mute Duration", value=f"{f'{days} Days, ' if days else ''}{f'{hours} Hours, ' if hours else ''}{f'{mins} Mins' if mins else ''}", inline=True)
                    await channel.send(embed=embed)
        else:# Oh No an ERROR!
            await ctx.send("Oh No! I Failed To Mute The User! Do I Have The Right Permissions?")
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def unmute(self, ctx, member: discord.Member):
        '''Unmute a User'''
        guild = cache.get_guild(ctx.guild.id)
        headers = {"Authorization": f"Bot {self.bot.http.token}"}# Set Headers
        url = f"https://discord.com/api/v9/guilds/{ctx.guild.id}/members/{member.id}"# Send Request To Mute User

        json = {'communication_disabled_until': None}
        session = requests.patch(url, json=json, headers=headers)
        if session.status_code in range(200, 299):# When Mute Is Successful

                await ctx.send(f"{member.mention} Has Been Unmuted.")
                if guild["toggle"]["modlog"]:# Modlog For Unmute Command
                    if guild["modlog"]["channel"] and guild["modlog"]["mutes"]:
                        channel = self.bot.get_channel(guild["modlog"]["channel"])
                        if not channel:
                            guild["modlog"]["channel"] = None
                            cache.update_guild(guild)
                            return
                        embed=discord.Embed(title="User Unmute Event", description=f"{member.display_name}#{member.discriminator} Has Been Unmuted", color=0x4d003c)
                        embed.add_field(name="Unmuted By:", value=ctx.author.mention, inline=False)
                        await channel.send(embed=embed)
    
                return
        else:
            await ctx.send("Failed To Unmute User :(")
            
            
            
    @cog_ext.cog_slash(guild_ids=guild_ids)
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, member : discord.Member, reason = None):
        '''Kick a User'''
        if ctx.author.top_role.position > member.top_role.position:
            guild = cache.get_guild(ctx.guild.id)
            await member.kick(reason=reason)
            embed=discord.Embed(title="User Has Been Kicked!", color=0xffb6f2)

            embed.add_field(name=f"User", value=member.mention, inline=True)
            embed.add_field(name=f"Kicked By", value=ctx.author.mention, inline=True)
            embed.add_field(name=f"Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            if guild["toggle"]["modlog"]:# Modlog For Kick Command
                if guild["modlog"]["channel"] and guild["modlog"]["kick"]:
                    channel = self.bot.get_channel(guild["modlog"]["channel"])
                    if not channel:
                        guild["modlog"]["channel"] = None
                        cache.update_guild(guild)
                        return
                    embed=discord.Embed(title="User Kick Event", description=f"{member.display_name}#{member.discriminator} Has Been Kicked", color=0x4d003c)
                    embed.add_field(name="Kicked By:", value=ctx.author.mention, inline=False)
                    embed.add_field(name="Kick Reason:", value=reason, inline=True)
                    await channel.send(embed=embed)
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
        guild = cache.get_guild(ctx.guild.id)
        guild, index = cache.find_member(guild, member.id)

            
        guild["members"][index]["infraction_description"].append(reason)
        guild["members"][index]["infraction_date"].append(datetime.now().date())
        await ctx.send(f'{member.mention} Has Been Warned For: **{reason}**')
        
        if guild["toggle"]["modlog"]:# Modlog For Warn Command
            if guild["modlog"]["channel"] and guild["modlog"]["warns"]:
                channel = self.bot.get_channel(guild["modlog"]["channel"])
                if not channel:
                    guild["modlog"]["channel"] = None
                    return
                embed=discord.Embed(title="User Warn Event", description=f"{member.display_name}#{member.discriminator} Has Been Warned", color=0x4d003c)
                embed.add_field(name="Warned By:", value=ctx.author.mention, inline=False)
                embed.add_field(name="Warn Reason:", value=reason, inline=True)
                await channel.send(embed=embed)
        cache.update_guild(guild)
        
    @cog_ext.cog_slash(guild_ids=guild_ids)
    async def infractions(self, ctx, member : discord.Member):
        '''Get A List Of Infractions Of a User'''
        guild = cache.get_guild(ctx.guild.id)
        guild, index = cache.find_member(guild, member.id)
        if not guild["members"][index]["infraction_description"]:
            embed=discord.Embed(color=0xffb6f2)
            embed.set_author(name=f"{member.display_name}#{member.discriminator} Has No Infractions", icon_url=member.avatar_url)
            await ctx.send(embed=embed)
            return
        else:
            index = len(guild["members"][index]["infraction_date"]) - 1# Since Indexes Start At 0 & Length Starts At 1 It Is The Index Of The element To Be Added
            
        guild["members"][index]["infraction_description"]
        guild["members"][index]["infraction_date"].append(datetime.now().date())
        embed=discord.Embed(color=0xffb6f2)
        embed.set_author(name=f"{member.display_name}#{member.discriminator} Has {len(guild['members'][index]['infraction_description'])} Infractions", icon_url=member.avatar_url)
        for i, infraction in enumerate(guild['members'][index]["infraction_description"]):# Iterate Over The Infractions
            if i >= 10:# To Limit The Infractions Displayed To 10
                break
            embed.add_field(name="⠀", value=f"**{infraction}** • {guild['members'][index]['infraction_date'][i].strftime('%d/%m/%y')}", inline=False)
        embed.set_footer(text="Showing The Most Recent 10")
        await ctx.send(embed=embed)
        
    @cog_ext.cog_slash(name="clear-infractions", guild_ids=guild_ids)
    async def _clearinfractions(self, ctx, member : discord.Member):
        '''Clear All Infractions Of A Specified User'''
        guild = cache.get_guild(ctx.guild.id)
        guild, index = cache.find_member(member.id)
        guild["members"][index]["infraction_description"] = None# Set All Infractions Back To None or NULL
        guild["members"][index]["infraction_date"] = None
        await ctx.send(f"Cleared All Infractions Of {member.mention}")
        cache.update_guild(guild)
        if guild["toggle"]["modlog"]:# Modlog For Clear Warns Command
            if guild["modlog"]["channel"] and guild["modlog"]["warns"]:
                channel = self.bot.get_channel(guild["modlog"]["channel"])
                if not channel:
                    guild["modlog"]["channel"] = None
                    return
                embed=discord.Embed(title="User Warn Clear Event", description=f"{member.display_name}#{member.discriminator} Has Been Cleared", color=0x4d003c)
                embed.add_field(name="Cleared By:", value=ctx.author.mention, inline=False)

                await channel.send(embed=embed)
        
        
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
    async def lock(self, ctx, channel : discord.TextChannel=None):
        '''Lock A Channel.  Blocks The Default Role From Sending Messages.'''
        channel = channel or ctx.channel
        guild = cache.get_guild(ctx.guild.id)
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f'{channel.mention} Locked.')
        if guild["toggle"]["modlog"]:# Modlog For Lock Command
            if guild["modlog"]["channel"] and guild["modlog"]["lock"]:
                channel = self.bot.get_channel(guild["modlog"]["channel"])
                if not channel:
                    guild["modlog"]["channel"] = None
                    cache.update_guild(guild)
                    return
                embed=discord.Embed(title="Channel Lock Event", description=f"{channel.mention} Has Been Locked", color=0x4d003c)
                embed.add_field(name="Locked By:", value=ctx.author.mention, inline=False)

            
            
            
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
        
        guild = cache.get_guild(ctx.guild.id)
        if guild["toggle"]["modlog"]:# Modlog For Clear Command
            if guild["modlog"]["channel"] and guild["modlog"]["purge"]:
                channel = self.bot.get_channel(guild["modlog"]["channel"])
                if not channel:
                    guild["modlog"]["channel"] = None
                    cache.update_guild()
                    return
                embed=discord.Embed(title="User Purge Event", description=f"{ctx.channel.mention} Has Been Cleared", color=0x4d003c)
                embed.add_field(name="Cleared By:", value=ctx.author.mention, inline=False)
                embed.add_field(name="Count:", value=f"{amount} Deleted.", inline=True)

            
            
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
        
        
        
        
        
def setup(bot):
    bot.add_cog(Moderation(bot))
