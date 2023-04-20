# Mobius Discord Music Bot
A simple, easy-to-use Discord music bot that allows users to play audio from YouTube in their voice channels.

## Features
- Play audio from YouTube videos
- Stream audio directly without downloading (saving storage space)
- Delete stored audio files after they've been played
- Error handling and clean error messages

## Installation
1. Install Python 3.9 or higher.
2. Clone this repository: git clone https://github.com/yourusername/Mobius-Discord-Bot.git
3. Change to the project directory: cd Mobius-Discord-Bot
4. Install the required dependencies: pip install -r requirements.txt
5. Create a .env file and add your Bot Token (DISCORD_TOKEN=<your token here>).
6. Run the bot: python main.py

## Commands
- '!join': Joins the user's voice channel.
- '!leave': Leaves the current voice channel.
- '!play <YouTube_URL>': Plays audio from the provided YouTube URL.
- '!stop': Stops the audio playback and clears the queue.
