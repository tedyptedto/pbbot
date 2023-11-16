# pip install apscheduler
# pip install discord
# pip install httpx[http2]
# https://github.com/Rapptz/discord.py
# créer le bot : https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token
#
#
import string
import discord
from discord.ext import commands
import aiohttp
import asyncio
import time
from urllib.parse import quote
import os
import httpx
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

def get_arrow(current, previous):
    try:
        current = str(current)
        previous = str(previous)
        if current > previous:
            return " | **↗**"
        elif current < previous:
            return " | **↘**"
        else:
            return ""
    except ValueError:
        return "❌"

base_dir = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+'/')+'/'
channelId = int(open(base_dir+"/config/channel_id.txt", 'r').read())
discordBotId = open(base_dir+"/config/token.txt", 'r').read()

intents = discord.Intents.default()
if not getattr(intents, 'message_content', False):
    intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

copytraders = [
    {'discordUser': 'xaocarlo', 'bbUser': 'xaocarlo', 'bbCode': "JKuwFA2ebE%2BUhjKrItsMbA%3D%3D"},
    {'discordUser': 'LuaN', 'bbUser': 'luantesting', 'bbCode': "y3R6ru2Yv6mVK3t7bebfJQ%3D%3D"},
    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk', 'bbCode': "JwT%2Ba21FcgJXHhs6%2BqVxZw%3D%3D"},
    {'discordUser': 'mani', 'bbUser': 'manicptrndr', 'bbCode': "ciOb3vGv0dp8JKJp4WTmeg%3D%3D"},
    {'discordUser': 'tedyptedto', 'bbUser': 'tedyptedtoCpTr', 'bbCode': "VAfEwFPZdNdfYGWiwy7V0g%3D%3D"},
]

stats_file = base_dir + "/config/stats.json"

def check_or_create_stats_file():
    if not os.path.exists(stats_file):
        stats = {}
        for trader in copytraders:
            stats[trader['bbUser']] = {
                'followers': 0,
                'stability': 0,
                'roi30j': 0,
                'aum': 0
            }
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)
    else:
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        # Usunięcie użytkowników z pliku stats.json, którzy nie są na liście copytraders
        users_to_remove = [user for user in stats if user not in [trader['bbUser'] for trader in copytraders]]
        for user in users_to_remove:
            del stats[user]

        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)

check_or_create_stats_file()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def check_traders(ctx):
    global channelId
    if ctx.channel.id != channelId:
        print('From not authorized channel')
        return

    timestamp = int(time.time() * 1000)
    embed = discord.Embed(title="╔═══════════( Copy Traders Information )═══════════╗", color=discord.Color(int("2b2d31", 16)))

    traders_info = []
    message = await ctx.send("Please wait, I am getting the data...")
    async with httpx.AsyncClient(http2=True) as session:
        for infos in copytraders:
            url = f"https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income?timeStamp={timestamp}&leaderMark={infos['bbCode']}"
            HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }

            try:
                response = await session.get(url, headers=HEADERS) 
                json_data = json.loads(response.text)
                followers = json_data['result']['currentFollowerCount']
                stability = json_data['result']['stableScoreLevelFormat']
                roi30j = int(json_data['result']['thirtyDayYieldRateE4']) / 100
                aum = int(json_data['result']['aumE8']) / 100000000

                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    if infos['bbUser'] in stats:
                        prev_values = stats[infos['bbUser']]
                        follower_arrow = get_arrow(followers, prev_values['followers'])
                        stability_arrow = get_arrow(stability, prev_values['stability'])
                        roi_arrow = get_arrow(roi30j, prev_values['roi30j'])
                        aum_arrow = get_arrow(aum, prev_values['aum'])
                    else:
                        follower_arrow = stability_arrow = roi_arrow = aum_arrow = ""

                fire_emoji = "🔥" if roi30j > 20 else ""

                trader_info = f"**[{infos['bbUser']}](https://www.bybit.com/copyTrade/trade-center/detail?leaderMark={infos['bbCode']})**\n" \
                              f"ROI (30D): **{roi30j}%** {fire_emoji} {roi_arrow}\n" \
                              f"Followers: **{followers}** {follower_arrow}\n" \
                              f"AUM: **{aum} USDT** {aum_arrow}\n" \
                              f"Stability: **{stability}** {stability_arrow}"

                traders_info.append((roi30j, trader_info))

                stats[infos['bbUser']] = {
                    'followers': followers,
                    'stability': stability,
                    'roi30j': roi30j,
                    'aum': aum
                }

                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=4)

            except Exception as e:
                print(f"An error occurred: {e}")

    traders_info.sort(reverse=True, key=lambda x: x[0])

    embed.description = "\u200b"

    for i, (roi, trader_info) in enumerate(traders_info, start=1):
        embed.add_field(name=f"", value=trader_info, inline=True)
    await message.edit(content="", embed=embed)

async def cronFunction():
    global channelId
    channel = bot.get_channel(channelId)

    await check_traders(channel)


scheduler = AsyncIOScheduler()
scheduler.add_job(cronFunction, CronTrigger(hour="8", minute="0", second="0"))
scheduler.start()

bot.run(discordBotId)
