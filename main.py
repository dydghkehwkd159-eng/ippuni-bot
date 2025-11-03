import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import youtube_dl
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

queue = []
now_playing = None
vc = None

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': False}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f"✅ 봇 로그인 완료: {bot.user}")
    await bot.tree.sync()
    print("📀 명령어 동기화 완료")

@bot.tree.command(name="재생", description="노래를 재생합니다.")
async def play(interaction: discord.Interaction, url: str):
    global vc, now_playing
    await interaction.response.defer()
    voice_channel = interaction.user.voice.channel

    if not voice_channel:
        await interaction.followup.send("❌ 음성 채널에 먼저 들어가주세요!")
        return

    if not vc or not vc.is_connected():
        vc = await voice_channel.connect()

    queue.append(url)
    await interaction.followup.send(f"🎵 대기열에 추가됨: {url} (현재 {len(queue)}/800)")

    if not now_playing:
        await play_next(interaction)

async def play_next(interaction):
    global vc, now_playing

    if not queue:
        now_playing = None
        return

    now_playing = queue.pop(0)
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(now_playing, download=False)
        url2 = info['url']
        title = info.get('title', 'Unknown')
        vc.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), bot.loop))
        asyncio.run_coroutine_threadsafe(interaction.followup.send(f"🎶 재생 중: {title}"), bot.loop)

@bot.tree.command(name="정지", description="노래를 정지합니다.")
async def stop(interaction: discord.Interaction):
    global vc
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("🛑 재생이 중지되었습니다.")
    else:
        await interaction.response.send_message("❌ 봇이 음성채널에 없습니다.")

@bot.tree.command(name="스킵", description="다음 노래로 넘깁니다.")
async def skip(interaction: discord.Interaction):
    global vc
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭ 다음 곡으로 넘어갑니다.")
    else:
        await interaction.response.send_message("❌ 재생 중인 노래가 없습니다.")

@bot.tree.command(name="셔플", description="대기열을 섞습니다.")
async def shuffle(interaction: discord.Interaction):
    global queue
    random.shuffle(queue)
    await interaction.response.send_message("🔀 대기열을 셔플했습니다!")

@bot.tree.command(name="목록", description="대기열을 보여줍니다.")
async def list_queue(interaction: discord.Interaction):
    if not queue:
        await interaction.response.send_message("🎧 대기열이 비어 있습니다.")
    else:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queue[:20])])
        await interaction.response.send_message(f"🎵 **대기열 (총 {len(queue)}곡)**\n{msg}")

import os

bot.run(os.getenv("DISCORD_TOKEN"))
