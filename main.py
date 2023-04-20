import asyncio
import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
from pytube import YouTube

load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
FFMPEG_FILEPATH = os.getenv('FFMPEG_FILEPATH')

# Bot class for music queues
class MusicBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = {}


# Pytube Class
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

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = MusicBot(command_prefix='!',intents=intents)

ffmpeg_options = {
    'options': '-vn'
}

# play_next command for queue
async def play_next_wrapper(ctx):
    guild_id = ctx.guild.id
    voice_channel = ctx.voice_client
    
    async def delete_file(filename):
        await asyncio.sleep(1)
        os.remove(filename)
    
    def after_playing(e):
        if hasattr(bot, "to_delete") and bot.to_delete:
            for file in bot.to_delete:
                bot.loop.call_later(2, bot.loop.create_task, delete_file(file))
                bot.to_delete.remove(file)
        bot.loop.create_task(play_next_wrapper(ctx))
        
    if not voice_channel.is_playing() and len(bot.queue[guild_id]) > 0:
        filename, data = bot.queue[guild_id].pop(0)
        voice_channel.play(discord.FFmpegPCMAudio(executable=FFMPEG_FILEPATH, source=filename),
                        after=after_playing)
        await ctx.send('**Now playing:** {}'.format(data['title']))
        
        if not hasattr(bot, "to_delete"):
            bot.to_delete = []
        
        bot.to_delete.append(filename)
                    
    else:
        asyncio.run_coroutine_threadsafe(ctx.invoke(leave), bot.loop)        

async def play_next(ctx):
    wrapped_play_next = play_next_wrapper(ctx)
    await wrapped_play_next()

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name="queue")
async def show_queue(ctx):
    
    guild_id = ctx.guild.id
    if not bot.queue[guild_id]:
        await ctx.send("The queue is empty")
    else:
        queue_text = "Current queue:\n"
        for i, (_, data) in enumerate(bot.queue[guild_id], start=1):
            queue_text += f"{i}. {data['title']}\n"
        await ctx.send(queue_text)
    
@bot.command(name='play_song', help='To play song')
async def play(ctx, url):
    
    guild_id = ctx.guild.id
    server = ctx.message.guild
    voice_channel = server.voice_client
    
    if guild_id not in bot.queue:
        bot.queue[guild_id] = []
    
    # Check if bot is playing something already
    if voice_channel.is_playing():
        async with ctx.typing():
            filename, data = await PytubeSource.from_url(url, loop=bot.loop)
            bot.queue[guild_id].append((filename, data))
        await ctx.send(f"Added {data['title']} to the queue.")
    
    else:
        async with ctx.typing():
            try:
                filename, data = await PytubeSource.from_url(url, loop=bot.loop)
                voice_channel.play(discord.FFmpegPCMAudio(
                executable=FFMPEG_FILEPATH, source=filename),
                after=lambda e: bot.loop.create_task(play_next_wrapper(ctx)))
            except Exception as e:
                print(f'Exception occurred: {e}')
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