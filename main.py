import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import random
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Ippuni Music Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

queue = []
now_playing = None
is_playing = False
shuffle_mode = False

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}
FFMPEG_OPTIONS = {'options': '-vn'}

async def play_next(ctx):
    global is_playing, now_playing
    if not queue:
        is_playing = False
        now_playing = None
        return

    url = queue.pop(0)
    now_playing = url
    vc = ctx.voice_client

    if not vc or not vc.is_connected():
        if ctx.author.voice:
            vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("🔊 음성 채널에 먼저 들어가주세요.")
            return

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info.get('url')
        title = info.get('title', '제목 없음')
        if not audio_url and 'entries' in info and len(info['entries'])>0:
            audio_url = info['entries'][0].get('url')
            title = info['entries'][0].get('title', title)

    if not audio_url:
        await ctx.send("❌ 재생할 수 없는 링크입니다.")
        return

    vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    is_playing = True
    await ctx.send(f"🎶 재생 중: **{title}**")

@bot.command(name='들어와')
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🔊 봇이 음성 채널에 입장했습니다.")
    else:
        await ctx.send("⚠️ 먼저 음성 채널에 들어가주세요!")

@bot.command(name='나가')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 봇이 음성 채널에서 나갔습니다.")
    else:
        await ctx.send("❌ 봇이 음성 채널에 있지 않습니다.")

@bot.command(name='재생')
async def play(ctx, *, url):
    global is_playing
    if len(queue) >= 800:
        await ctx.send("❌ 대기열이 가득 찼습니다 (최대 800곡).")
        return
    queue.append(url)
    await ctx.send(f"🎵 대기열에 추가됨: {url} (현재 대기열: {len(queue)}곡)")

    if not is_playing:
        await play_next(ctx)

@bot.command(name='목록')
async def show_queue(ctx):
    if not queue:
        await ctx.send("📭 현재 대기열이 비어있어요.")
        return

    message = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queue[:800])])
    if len(message) > 1900:
        message = message[:1900] + "\n... (목록 생략)"
    await ctx.send(f"🎶 **대기열 (총 {len(queue)}곡)**\n{message}")

@bot.command(name='스킵')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ 다음 곡으로 넘어갑니다.")
    else:
        await ctx.send("❌ 재생 중인 노래가 없습니다.")

@bot.command(name='셔플')
async def shuffle_cmd(ctx):
    global queue, shuffle_mode
    if not queue:
        await ctx.send("📭 대기열이 비어 있어요!")
        return

    random.shuffle(queue)
    shuffle_mode = True
    await ctx.send("🔀 대기열이 셔플되었습니다!")

@bot.command(name='멈춰')
async def stop(ctx):
    if ctx.voice_client:
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ 음악을 멈추고 나갔습니다.")
    else:
        await ctx.send("❌ 현재 재생 중이 아닙니다.")

@bot.command(name='지금')
async def now(ctx):
    if now_playing:
        await ctx.send(f"🎧 지금 재생 중: **{now_playing}**")
    else:
        await ctx.send("🎶 현재 재생 중인 곡이 없습니다.")

@bot.command(name='일시정지')
async def pause(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ 노래가 일시정지되었습니다.")
    else:
        await ctx.send("❌ 일시정지할 노래가 없습니다.")

@bot.command(name='다시시작')
async def resume(ctx):
    vc = ctx.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ 노래가 다시 재생됩니다.")
    else:
        await ctx.send("❌ 재생 중이거나 재개할 곡이 없습니다.")

@tasks.loop(minutes=10)
async def status_loop():
    await bot.change_presence(activity=discord.Game("🎵 24시간 노래 재생 중"))

@bot.event
async def on_ready():
    print(f"✅ 봇 로그인 완료: {bot.user}")
    if not status_loop.is_running():
        status_loop.start()
    await bot.change_presence(activity=discord.Game("🎶 /재생 으로 노래 시작!"))

if __name__ == '__main__':
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN") or "여기에_디스코드_봇_토큰_입력"
    bot.run(TOKEN)
