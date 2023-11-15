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

intents = discord.Intents.default()
# intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

copytraders = [
    {'discordUser': 'xaocarlo', 'bbUser': 'xaocarlo', 'bbCode': "JKuwFA2ebE%2BUhjKrItsMbA%3D%3D"},
    {'discordUser': 'LuaN', 'bbUser': 'luantesting', 'bbCode': "y3R6ru2Yv6mVK3t7bebfJQ%3D%3D"},
    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk', 'bbCode': "JwT%2Ba21FcgJXHhs6%2BqVxZw%3D%3D"},
    {'discordUser': 'mani', 'bbUser': 'manicptrndr', 'bbCode': "ciOb3vGv0dp8JKJp4WTmeg%3D%3D"},
    {'discordUser': 'tedyptedto', 'bbUser': 'tedyptedtoCpTr', 'bbCode': "VAfEwFPZdNdfYGWiwy7V0g%3D%3D"},
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def check_traders(ctx):
    timestamp = int(time.time() * 1000)
    await ctx.send(f"Please wait i am getting the datas")

    embed = discord.Embed(title="Copy Traders Information", color=discord.Color(int("2b2d31", 16)))

    traders_info = []

    async with httpx.AsyncClient(http2=True) as session:
        for infos in copytraders:
            url = f"https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income?timeStamp={timestamp}&leaderMark={infos['bbCode']}"
            print({url})
            HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }

            try:
                response = await session.get(url, headers=HEADERS) 
                # print(response.text)
                json_data = json.loads(response.text)
                followers = json_data['result']['currentFollowerCount']
                stability = json_data['result']['stableScoreLevelFormat']
                roi30j = int(json_data['result']['thirtyDayYieldRateE4']) / 100
                aum = int(json_data['result']['aumE8']) / 100000000

                fire_emoji = "🔥" if roi30j > 20 else ""
                
                trader_info = f"**[{infos['bbUser']}](https://www.bybit.com/copyTrade/trade-center/detail?leaderMark={infos['bbCode']})**\n" \
                                f"ROI (30 days): {roi30j}% {fire_emoji}\n" \
                                f"Followers: {followers}\n" \
                                f"AUM: {aum} USDT\n" \
                                f"Stability: {stability}"

                traders_info.append((roi30j, trader_info))


            except Exception as e:
                print(f"An error occurred: {e}")

    traders_info.sort(reverse=True, key=lambda x: x[0])

    embed.description = "\u200b"

    for i, (roi, trader_info) in enumerate(traders_info, start=1):
        embed.add_field(name=f"", value=trader_info, inline=True)

    await ctx.send(embed=embed)

base_dir = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+'/')+'/'
bot.run(open(base_dir+"/config/token.txt", 'r').read())
