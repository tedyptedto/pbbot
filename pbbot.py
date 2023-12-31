# pip install apscheduler
# pip install discord
# pip install httpx[http2]
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
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

base_dir = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+'/')+'/'
channelId = int(open(base_dir+"/config/channel_id.txt", 'r').read())
discordBotId = open(base_dir+"/config/token.txt", 'r').read()

intents = discord.Intents.default()
if not getattr(intents, 'message_content', True):
    intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

copytraders = [

    # BYBIT
    {'discordUser': 'xaocarlo', 'bbUser': 'xaocarlo', 'bbCode': "JKuwFA2ebE%2BUhjKrItsMbA%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'xaocarlo', 'bbUser': 'RUCapital07', 'bbCode': "WdGj1QiU4kv1FoLP6%2FTLqg%3D%3D", 'exchange': "bybit"},

    {'discordUser': 'LuaN', 'bbUser': 'luantesting', 'bbCode': "y3R6ru2Yv6mVK3t7bebfJQ%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'LuaN', 'bbUser': 'luanmain', 'bbCode': "XqusunZ9%2FNPX5IMAdmHvKg%3D%3D", 'exchange': "bybit"},

    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk', 'bbCode': "JwT%2Ba21FcgJXHhs6%2BqVxZw%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'mani', 'bbUser': 'manicptrndr', 'bbCode': "ciOb3vGv0dp8JKJp4WTmeg%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk2', 'bbCode': "jGPes4W1lsptyz6Lxmwkxg%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk3', 'bbCode': "dfgxB7g/cKRFvDDVz0r4Iw==", 'exchange': "bybit"},

    {'discordUser': 'tedyptedto', 'bbUser': 'tedyptedtoCpTr', 'bbCode': "VAfEwFPZdNdfYGWiwy7V0g%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'tedyptedto', 'bbUser': 'tedySub2', 'bbCode': "W86y5Bo8c78Cy803QgMwMg%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'tedyptedto', 'bbUser': 'Tedy57123TheBestOne', 'bbCode': "K%2Bupto5fn8zpUpIY0GvI%2FA%3D%3D", 'exchange': "bybit"},

    {'discordUser': 'jnk_xnxx', 'bbUser': 'jnk777', 'bbCode': "1o7jD8RX7meCMGaqG2tE3w%3D%3D", 'exchange': "bybit"},
    {'discordUser': 'jnk_xnxx', 'bbUser': 'jnkmone', 'bbCode': "I7eQ24u71qN5fYJ%2BbnXXlQ%3D%3D", 'exchange': "bybit"},
    
    {'discordUser': 'Hawkeye', 'bbUser': 'Hawkbot scalper', 'bbCode': "3U0%2BHYawCwEVdm12DBs5cA%3D%3D", 'exchange': "bybit"},

    {'discordUser': 'justincrap', 'bbUser': 'Justin_grid', 'bbCode': "BT2AU20De/7u//z2MzEpRQ==", 'exchange': "bybit"},

    {'discordUser': 'iamtheonewhoknocks', 'bbUser': 'IamtheonewhoKnocks', 'bbCode': "b5ChnV8%2BGglQIpaZEA29ug%3D%3D", 'exchange': "bybit"},
    
    # BYBIT #

    # BINANCE #
    {'discordUser': 'mani', 'bbUser': 'manicptlowrisk_binance', 'bbCode': "3746904129636329728", 'exchange': "binance"},
    {'discordUser': 'Maloz', 'bbUser': 'Maloz', 'bbCode': "3777357340021816577", 'exchange': "binance"}
    # BINANCE #
]

stats_file = base_dir + "/config/stats.json"
last_check_time = 0
cooldown = 10
cache_leaderboard = ""

def check_or_create_stats_file():
    if not os.path.exists(stats_file):
        stats = {}
        for trader in copytraders:
            if trader['exchange'] == "bybit":
                stats[trader['bbUser']] = {
                    'followers': 0,
                    'followers_pnl': 0,
                    'stability': 0,
                    'roi30j': 0,
                    'aum': 0,
                    'sharpe': float(0.00),
                    'exchange': "bybit"
                }
            if trader['exchange'] == "binance":
                stats[trader['bbUser']] = {
                    'followers': 0,
                    'followers_pnl': 0,
                    'roi30j': 0,
                    'aum': 0,
                    'sharpe': float(0.00),
                    'exchange': "binance"
                }
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)
    else:
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        users_to_remove = [user for user in stats if user not in [trader['bbUser'] for trader in copytraders]]
        for user in users_to_remove:
            del stats[user]

        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=4)

check_or_create_stats_file()

async def getUserLeaderBoard(username):
    global cache_leaderboard
    async with httpx.AsyncClient(http2=True) as session:
        timestamp = int(time.time() * 1000)
        url = f"https://api2.bybit.com/fapi/beehive/private/v1/common/recommend-leaders?timeStamp={timestamp}&language=en"
        HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }
        
        aInfos = []

        try:
            if cache_leaderboard == "":
                response = await session.get("https://www.bybit.com/copyTrade/", headers=HEADERS) # Needed to get the cookies
                response = await session.get(url, headers=HEADERS)
                cache_leaderboard = response.text 
            # print(url)
            json_data = json.loads(cache_leaderboard)
            for leaderRecommendInfoList in json_data['result']['leaderRecommendInfoList']:
                title = leaderRecommendInfoList['title']
                for position, users in enumerate(leaderRecommendInfoList['leaderRecommendDetailList']):
                    user = users['nickName']
                    if (user == username):
                        aInfos.append({
                            "user": username,
                            "leadbordtype": title,
                            "position" : position +1, 
                        })

            # print(json.dumps(json_data, indent=4))
        except Exception as e:
            print(f"21 An error occurred: {e}")


        return aInfos

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


total_aum = 0
total_aum2 = 0


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command()
async def check_traders(ctx, fromTask=False):
    global channelId
    global last_check_time
    global cache_leaderboard
    cache_leaderboard = ""
    if not fromTask:
        if ctx.channel.id != channelId:
            print('From not authorized channel')
            return

    timestamp = int(time.time() * 1000)

    traders_info = []
    traders_info2 = []
    # message = await ctx.send("https://i.imgur.com/c4AGtzM.gif", reference=ctx.message) # generate a bug on Cron 
    message = await ctx.send("https://i.imgur.com/c4AGtzM.gif")

    async with httpx.AsyncClient(http2=True) as session:
        for infos in copytraders:
            if infos['exchange'] == "bybit":
                url = f"https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income?timeStamp={timestamp}&leaderMark={infos['bbCode']}"
                urlInfo = f"https://api2.bybit.com/fapi/beehive/private/v1/pub-leader/info?timeStamp={timestamp}&language=en&leaderMark={infos['bbCode']}"
                HEADERS = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }
                try:
                    response = await session.get(url, headers=HEADERS) 
                    infosUser = await session.get(urlInfo, headers=HEADERS) 
                    #print(urlInfo)
                    #print(infosUser)
                    infosUser = json.loads(infosUser.text) 
                    json_data = json.loads(response.text)
                    followers = json_data['result']['currentFollowerCount']
                    followers_pnl = round(float(json_data['result']['thirtyDayFollowerYieldE8']) / 100000000, 2)
                    stability = json_data['result']['stableScoreLevelFormat']
                    roi30j = int(json_data['result']['thirtyDayYieldRateE4']) / 100
                    aum = int(json_data['result']['aumE8']) / 100000000
                    nbdays = int(infosUser['result']['tradeDays'])
                    sharpe = round(int(json_data['result']['thirtyDaySharpeRatioE4']) / 10000, 2)
                    global total_aum
                    total_aum += aum

                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                        if infos['bbUser'] in stats:
                            prev_values = stats[infos['bbUser']]
                            follower_arrow = get_arrow(followers,   prev_values['followers']            if 'followers'  in prev_values else followers)
                            stability_arrow = get_arrow(stability,  prev_values['stability']            if 'stability'  in prev_values else stability)
                            roi_arrow = get_arrow(roi30j,           prev_values['roi30j']               if 'roi30j'     in prev_values else roi30j)
                            aum_arrow = get_arrow(aum,              prev_values['aum']                  if 'aum'        in prev_values else aum)
                            sharpe_arrow = get_arrow(sharpe,        prev_values['sharpe']               if 'sharpe'     in prev_values else sharpe)
                            followers_pnl_arrow = get_arrow(followers_pnl, prev_values['followers_pnl'] if 'followers_pnl' in prev_values else followers_pnl)
                        else:
                            follower_arrow = stability_arrow = roi_arrow = aum_arrow = sharpe_arrow = followers_pnl_arrow = ""

                    fire_emoji = "🔥" if roi30j >= 20.00 else ""

                    aLeaderboard = (await getUserLeaderBoard(infos['bbUser']))


                    leaderboardtext = ""
                    for leaderboard in aLeaderboard:
                        leaderboard['position'] = str(leaderboard['position']) + "°"
                        leaderboardtext += f"🏆 **{leaderboard['position']} {leaderboard['leadbordtype']}**\n" if leaderboard['position'] else f"\n"

                    trader_info = f"**[{infos['bbUser']}](https://www.bybit.com/copyTrade/trade-center/detail?leaderMark={infos['bbCode']})**\n" \
                                f"🗓️ **{nbdays}** Days\n" \
                                f"🎯 ROI (30D): **{roi30j}%** {fire_emoji} {roi_arrow}\n" \
                                f"👤 Followers: **{followers}** {follower_arrow}\n" \
                                f"👥 Flw PNL: **{format_aum(followers_pnl)}$** {followers_pnl_arrow}\n" \
                                f"💰 AUM: **{format_aum(aum)}$** {aum_arrow}\n" \
                                f"⚖️ Stability: **{stability}** {stability_arrow}\n" \
                                f"🔪 Sharpe (30D): **{sharpe:.2f}** {sharpe_arrow}\n" \
                                f"{leaderboardtext}" \
                                f"\n"
                    traders_info.append((roi30j, trader_info))

                    stats[infos['bbUser']] = {
                        'followers': followers,
                        'followers_pnl': round(followers_pnl, 2),
                        'stability': stability,
                        'roi30j': roi30j,
                        'aum': aum,
                        'sharpe': round(sharpe, 2),
                        'exchange': "bybit"
                    }

                    with open(stats_file, 'w') as f:
                        json.dump(stats, f, indent=4)

                except Exception as e:
                    print(f"18 An error occurred: {e}")
                    print(e)
                    print(str(e))
            embed = discord.Embed(title='╔═════════════( Copy Traders BYBIT )═════════════╗', color=discord.Color(int("2b2d31", 16)))
            #embed.add_field(name=f"", value=f"", inline=True)
            #embed.add_field(name=f"Total AUM", value=f'{format_aum(total_aum)}$', inline=True)
            #embed.set_footer(text=f"Total AUM: {format_aum(total_aum)}$", icon_url="https://cdn-icons-png.flaticon.com/512/5206/5206272.png")
            #embed.add_field(name=f"", value=f"", inline=True)




            if infos['exchange'] == "binance":
                url = f"https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/detail?portfolioId={infos['bbCode']}"
                urlInfo = f"https://www.binance.com/bapi/futures/v1/public/future/copy-trade/lead-portfolio/performance?portfolioId={infos['bbCode']}&timeRange=30D"
                HEADERS = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }
            
                try:
                    #print(urlInfo)
                    response = await session.get(url, headers=HEADERS) 
                    infosUser = await session.get(urlInfo, headers=HEADERS) 
                    infosUser = json.loads(infosUser.text) 
                    json_data = json.loads(response.text)
                    followers = round(float(json_data['data']['currentCopyCount']))
                    followers_pnl = float(json_data['data']['copierPnl'])
                    #stability = json_data['result']['stableScoreLevelFormat']
                    roi30j = round(float(infosUser['data']['roi']), 2)
                    aum = round(float(json_data['data']['aumAmount']), 2)
                    #nbdays = int(infosUser['result']['tradeDays'])
                    sharpe = round(float(json_data['data']['sharpRatio']), 3) if json_data['data']['sharpRatio'] != None else 0.0
                    global total_aum2
                    total_aum2 += aum
                    timestamp_trader = json_data['data']['startTime'] / 1000
                    timestamp_today = int(time.time())  # Dzisiejszy timestamp (aktualny czas)
                    days = (timestamp_today - timestamp_trader) / (24 * 3600)  # 24 godziny * 3600 sekund = 1 dzień

                    sharpe_message = f"🔪 Sharpe (30D): **{float(sharpe):.2f}** {sharpe_arrow}\n" if days >= 30 else ""
                    


                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                        if infos['bbUser'] in stats:
                            prev_values = stats[infos['bbUser']]
                            follower_arrow = get_arrow(followers,           prev_values['followers'] if 'followers' in prev_values else followers_pnl)
                            roi_arrow = get_arrow(roi30j,                   prev_values['roi30j'] if 'roi30j' in prev_values else roi30j)
                            aum_arrow = get_arrow(aum,                      prev_values['aum'] if 'aum' in prev_values else aum)
                            sharpe_arrow = get_arrow(sharpe,                prev_values['sharpe'] if 'sharpe' in prev_values else sharpe)
                            followers_pnl_arrow = get_arrow(followers_pnl,  prev_values['followers_pnl'] if 'followers_pnl' in prev_values else followers_pnl)
                        else:
                            follower_arrow = roi_arrow = aum_arrow = sharpe_arrow = followers_pnl_arrow = ""

                    fire_emoji = "🔥" if roi30j >= 20.00 else ""

                    trader_info2 = f"**[{infos['bbUser'].replace('_binance', '')}](https://www.binance.com/en/copy-trading/lead-details?portfolioId={infos['bbCode']})**\n" \
                                f"🗓️ **{days:.0f}** Days\n" \
                                f"🎯 ROI (30D): **{roi30j:.2f}%** {fire_emoji} {roi_arrow}\n" \
                                f"👤 Followers: **{followers}** {follower_arrow}\n" \
                                f"👥 Flw PNL: **{format_aum(followers_pnl)}$** {followers_pnl_arrow}\n" \
                                f"💰 AUM: **{format_aum(aum)}$** {aum_arrow}\n" \
                                f"{sharpe_message}" \
                                f"\n"
                    traders_info2.append((40, trader_info2))


                    stats[infos['bbUser']] = {
                        'followers': followers,
                        'followers_pnl': round(followers_pnl, 2),
                        'roi30j': roi30j,
                        'aum': aum,
                        'sharpe': round(sharpe, 2),
                        'exchange': "binance"
                    }

                    with open(stats_file, 'w') as f:
                        json.dump(stats, f, indent=4)

                except Exception as e:
                    print(f"19 An error occurred: {e}")
            embed2 = discord.Embed(title='╔════════════( Copy Traders BINANCE )════════════╗', color=discord.Color(int("2b2d31", 16)))
            #embed2.add_field(name=f"", value=f"", inline=True)
            #embed2.add_field(name=f"Total AUM", value=f'{format_aum(total_aum2)}$', inline=True)
            #embed2.set_footer(text=f"Total AUM: {format_aum(total_aum2)}$", icon_url="https://cdn-icons-png.flaticon.com/512/5206/5206272.png")
            #embed2.add_field(name=f"", value=f"", inline=True)

        traders_info.sort(reverse=True, key=lambda x: (x[1].split('Stability: **')[1].split('**')[0], x[0]))
        traders_info2.sort(reverse=True, key=lambda x: (float(x[1].split('ROI (30D): **')[1].split('%')[0]), x[0]))

        embed.description = f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Total AUM: __**{format_aum(total_aum)}$**__"
        embed2.description = f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Total AUM: __**{format_aum(total_aum2)}$**__"
        total_aum = 0
        total_aum2 = 0
        for i, (roi, trader_info) in enumerate(traders_info, start=1):
            embed.add_field(name=f"", value=f"**{i}.** "+trader_info, inline=True)

        for i, (roi, trader_info2) in enumerate(traders_info2, start=1):
            embed2.add_field(name=f"", value=f"**{i}.** "+trader_info2, inline=True)

        await message.edit(content="", embed=embed)
        await ctx.send(content="", embed=embed2)



@check_traders.error
async def check_traders_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        response = await ctx.send(f"Wait {error.retry_after:.0f} seconds before using the command", reference=ctx.message)
        await asyncio.sleep(4)
        await response.delete()
        await ctx.message.delete()
    else:
        await ctx.send("20 An error occurred while executing the command.")
        print(error)

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

def format_aum(aum):
    if aum >= 1000000:
        return f"{aum / 1000000:.2f}M"
    elif aum >= 1000:
        return f"{aum / 1000:.2f}k"
    else:
        return f"{aum:.2f}"

async def cronFunction():
    global channelId
    channel = bot.get_channel(channelId)

    await check_traders(channel, fromTask=True)


scheduler = AsyncIOScheduler()
scheduler.add_job(cronFunction, CronTrigger(hour="8", minute="0", second="0"))
# scheduler.add_job(cronFunction, 'interval', seconds=5)

scheduler.start()

bot.run(discordBotId)
