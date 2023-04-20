import asyncio
import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
from pytube import YouTube

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents)

class PytubeSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        ytb = YouTube(url)
        data = {'title': ytb.title}
        filename = ytb.streams.filter(only_audio=True, file_extension='mp4').first().download(skip_existing=True)
        return filename, data
    
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()

        def fetch_data():
            try:
                ytb = YouTube(url)
                data = {'title': ytb.title}
                filename = ytb.streams.filter(only_audio=True, file_extension='mp4').first().download(skip_existing=True)
                return filename, data
            except Exception as e:
                print(f"Error occurred while fetching data: {e}")
                return None, None

        filename, data = await loop.run_in_executor(None, fetch_data)
        if filename and data:
            return filename, data
        else:
            raise Exception("Error occurred while fetching data from YouTube")

ffmpeg_options = {
    'options': '-vn'
}
    
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='play_song', help='To play song')
async def play(ctx, url):
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        try:
            filename, data = await PytubeSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(
            executable="F:\\Mobius Discord Bot\\ffmpeg-2023-04-17-git-65e537b833-full_build\\bin\\ffmpeg.exe", source=filename),
            after=lambda e: os.remove(filename) if os.path.isfile(filename) else None
        )
        except:
            print('Exception occurred')
            await ctx.send('Issue occurred downloading song. Please wait 10 seconds and try again...')
            
    await ctx.send('**Now playing:** {}'.format(data['title']))

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")
    


@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")




if __name__ == "__main__" :
    bot.run(DISCORD_TOKEN)