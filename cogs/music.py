import asyncio
import functools
import io
import itertools
import math
import random
import urllib

import discord
import youtube_dl
from async_timeout import timeout
from discord import File
from discord.ext import commands, tasks
from discord_slash import cog_ext
from PIL import Image, ImageDraw, ImageFont
from youtube_dl.utils import DownloadError

#from modules import cache_get as cache





guild_ids = [704255331680911402]

# Silence useless bug reports messages for Music
youtube_dl.utils.bug_reports_message = lambda: ''

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


        
        
def setup(bot):
    bot.add_cog(Music(bot))