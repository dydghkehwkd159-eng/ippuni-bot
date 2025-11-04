import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

queue = []
now_playing = None

@bot.event
async def on_ready():
    print(f'✅ 로그인 성공: {bot.user}')

@bot.command(name='재생')
async def play(ctx, *, url):
    global now_playing
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send('❌ 먼저 음성 채널에 들어가 주세요.')
            return

    queue.append(url)
    await ctx.send(f'🎵 대기열에 추가됨: {url}')

    if not now_playing:
        await play_next(ctx)

async def play_next(ctx):
    global now_playing
    if not queue:
        now_playing = None
        await ctx.send('⏹️ 대기열이 비었습니다.')
        return

    now_playing = queue.pop(0)
    await ctx.send(f'▶️ 재생 중: {now_playing}')

    with yt_dlp.YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(now_playing, download=False)
        url2 = info['url']

    ctx.voice_client.play(discord.FFmpegPCMAudio(url2), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

@bot.command(name='스킵')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('⏭️ 다음 곡으로 넘어갑니다.')

@bot.command(name='나가기')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('👋 봇이 음성 채널에서 나갔습니다.')

@bot.command(name='목록')
async def list_queue(ctx):
    if not queue:
        await ctx.send('📭 현재 대기열이 비어있습니다.')
    else:
        message = '\n'.join([f'{i+1}. {url}' for i, url in enumerate(queue[:20])])
        await ctx.send(f'📜 대기열 목록:\n{message}')

# 🎈 Flask (Render용 keep-alive)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

bot.run(os.getenv('TOKEN'))
