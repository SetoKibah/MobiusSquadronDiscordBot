import asyncio
import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
from pytube import YouTube

load_dotenv()
# When API tokens are top-secret codes that should never see the light of day
# We stash it in the .env file like pirates hiding their treasure
DISCORD_TOKEN = os.getenv("")

intents = discord.Intents().all()
client = discord.Client(intents=intents)
# Meet our bot, it answers to '!', very existentialist of it
bot = commands.Bot(command_prefix='!',intents=intents)

class PytubeSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    # Defining a class method like a chef creating a recipe
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()

        def fetch_data():
            try:
                # YouTube, it is life
                ytb = YouTube(url)
                data = {'title': ytb.title}
                # Our bot is lazy. It just downloads the audio. Because fawk it.
                filename = ytb.streams.filter(only_audio=True, file_extension='mp4').first().download(skip_existing=True)
                return filename, data
            except Exception as e:
                # Oops, it broke.
                print(f"Error occurred while fetching data: {e}")
                return None, None

        # Our bot is also very polite, it waits its turn to fetch data
        filename, data = await loop.run_in_executor(None, fetch_data)
        if filename and data:
            # Read the names dumbass.
            return filename, data
        else:
            # Sometimes even a perfect machine fails
            raise Exception("Error occurred while fetching data from YouTube")

# ffmpeg_options is our super fancy music editing suite
ffmpeg_options = {
    'options': '-vn'
}

# You shall not pass! Unless you say '!join'
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        # I'm not your buddy, pal, unless you're in a voice channel
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    # Bot gracefully slides into your voice channel DMs
    await channel.connect()

# Pon de replay, eh.
@bot.command(name='play_song', help='To play song')
async def play(ctx, url):
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        try:
            # Bot dons its cape and flies off to fetch your song
            filename, data = await PytubeSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(
            executable="F:\\Mobius Discord Bot\\ffmpeg-2023-04-17-git-65e537b833-full_build\\bin\\ffmpeg.exe", source=filename),
            # After playing, the bot dutifully cleans up, what a good bot!
            after=lambda e: os.remove(filename) if os.path.isfile(filename) else None
        )
        except:
            print('Exception occurred')
            await ctx.send('Issue occurred downloading song. Please wait 10 seconds and try again...')
            
    await ctx.send('**Now playing:** {}'.format(data['title']))

# Bot, halt! '!pause'
@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        # Like a robot butler, it obeys your every command
        await voice_client.pause()
    else:
        # You can't pause the silence, dipshit
        await ctx.send("The bot is not playing anything at the moment.")
    
# Resume, dear Bot! '!resume'
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        # Nothing to resume if you didn't hit pause, you knob
        await ctx.send("The bot was not playing anything before this. Use play_song command")

# Lonely? The bot can go '!leave' you too
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        # How can I leave when I'm not there? From Paris with Love, The Bot
        await ctx.send("The bot is not connected to a voice channel.")

# Enough music! '!stop'
@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        # Hard to stop when you're already not doing anything!
        await ctx.send("The bot is not playing anything at the moment.")

# "The story so far: In the beginning the Universe was created. This has made a lot of people very angry and been widely regarded as a bad move."
if __name__ == "__main__" :
    # Make
    bot.run("")
