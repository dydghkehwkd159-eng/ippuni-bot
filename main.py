import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
from flask import Flask
from threading import Thread

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=os.getenv("PREFIX", "/"), intents=intents)

queue = []
now_playing = None
voice_client = None

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 가 로그인되었습니다!")

@bot.command(name="재생")
async def play(ctx, *, url):
    global now_playing, voice_client
    if not ctx.author.voice:
        return await ctx.send("음성 채널에 먼저 들어가주세요!")

    channel = ctx.author.voice.channel
    if not voice_client or not voice_client.is_connected():
        voice_client = await channel.connect()

    queue.append(url)
    await ctx.send(f"🎵 추가됨: {url}")

    if not now_playing:
        await play_next(ctx)

async def play_next(ctx):
    global now_playing, voice_client
    if len(queue) == 0:
        now_playing = None
        return

    url = queue.pop(0)
    now_playing = url

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info["url"]

    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()

    voice_client.stop()
    source = await discord.FFmpegOpusAudio.from_probe(audio_url, method="fallback")
    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"🎶 재생 중: {url}")

@bot.command(name="일시정지")
async def pause(ctx):
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸️ 음악이 일시정지되었습니다.")

@bot.command(name="다시시작")
async def resume(ctx):
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶️ 음악이 다시 재생됩니다.")

@bot.command(name="건너뛰기")
async def skip(ctx):
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("⏭️ 다음 노래로 넘어갑니다.")

@bot.command(name="정지")
async def stop(ctx):
    global queue
    if voice_client:
        queue.clear()
        await voice_client.disconnect()
        await ctx.send("⏹️ 음악이 중지되고 봇이 나갔습니다.")

@bot.command(name="목록")
async def list_queue(ctx):
    if not queue:
        await ctx.send("🎵 대기 중인 노래가 없습니다.")
    else:
        msg = "\n".join([f"{i+1}. {q}" for i, q in enumerate(queue[:20])])
        await ctx.send(f"🎶 현재 대기열:\n{msg}")

@bot.command(name="셔플")
async def shuffle(ctx):
    random.shuffle(queue)
    await ctx.send("🔀 대기열이 섞였습니다!")

# Flask 서버
app = Flask('')

@app.route('/')
def home():
    return "봇이 Render에서 정상 작동 중입니다 ✅"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))
