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
import requests
import matplotlib.pyplot as plt
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

base_dir = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+'/')+'/'
channelId = int(open(base_dir+"/config/channel_id.txt", 'r').read())
channelIdHL = int(open(base_dir+"/config/channel_id_HL.txt", 'r').read())
discordBotId = open(base_dir+"/config/token.txt", 'r').read()

intents = discord.Intents.default()
if not getattr(intents, 'message_content', True):
    intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def send_copytraders_data(ctx):
    allowed_users = ['jnk_xnxx', 'tedyptedto']
    if ctx.message.author.name not in allowed_users:
        bot_response = await ctx.send("You are not authorized to use this command.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
        return

    with open(base_dir + '/config/copytraders.json', 'r') as file:
        copytraders_data = json.load(file)

    copytraders_data.sort(key=lambda x: x['discordUser'])

    chunks = []
    chunk = {}
    counter = 0

    for entry in copytraders_data:
        chunk.update({str(counter): entry})
        counter += 1
        if counter % 4 == 0:
            chunks.append(chunk)
            chunk = {}

    if chunk:
        chunks.append(chunk)

    for i, chunk_data in enumerate(chunks, start=1):
        message = f"```\n{json.dumps(chunk_data, indent=4)}\n```"
        await ctx.author.send(message)
        await asyncio.sleep(1)

    await asyncio.sleep(5)
    await ctx.message.delete()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        bot_response = await ctx.send(f"Missing required argument: {error.param}")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
    else:
        bot_response = await ctx.send("An error occurred while executing the command.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()



@bot.command()
async def add(ctx, discord_user, bb_user, bb_code, exchange):
    allowed_users = ['jnk_xnxx', 'tedyptedto']
    if ctx.message.author.name not in allowed_users:
        bot_response = await ctx.send("You are not authorized to use this command.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
        return
    if any(arg is None for arg in [discord_user, bb_user, bb_code, exchange]):
        bot_response = await ctx.send("Please provide all arguments: `discord_user`, `bb_user`, `bb_code`, `exchange`.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
        return
    new_trader = {
        "discordUser": discord_user,
        "bbUser": bb_user,
        "bbCode": bb_code,
        "exchange": exchange
    }
    with open(base_dir +'/config/copytraders.json', 'r') as file:
        traders = json.load(file)
    traders.append(new_trader)
    
    with open(base_dir +'/config/copytraders.json', 'w') as file:
        json.dump(traders, file, indent=4)
    
    bot_response = await ctx.send(f"User **{discord_user}** added to copytrading list!")
    await asyncio.sleep(5)
    await ctx.message.delete()
    await bot_response.delete()


@bot.command()
async def remove(ctx, discord_user: str, bb_user: str, bb_code: str, exchange: str):
    allowed_users = ['jnk_xnxx', 'tedyptedto']
    if ctx.message.author.name not in allowed_users:
        bot_response = await ctx.send("You are not authorized to use this command.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
        return
    if any(arg is None for arg in [discord_user, bb_user, bb_code, exchange]):
        bot_response = await ctx.send("Please provide all arguments: `discord_user`, `bb_user`, `bb_code`, `exchange`.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
        return
    with open(base_dir + '/config/copytraders.json', 'r') as file:
        traders = json.load(file)
    
    removed = False
    for trader in traders:
        if (
            trader['discordUser'] == discord_user
            and trader['bbUser'] == bb_user
            and trader['bbCode'] == bb_code
            and trader['exchange'] == exchange
        ):
            traders.remove(trader)
            removed = True
            break
    
    if removed:
        with open(base_dir + '/config/copytraders.json', 'w') as file:
            json.dump(traders, file, indent=4)
        bot_response = await ctx.send(f"User **{discord_user}** removed to copytrading list!")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()
    else:
        bot_response = await ctx.send(f"User **{discord_user}** not found in the traders list.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await bot_response.delete()


copytraders = []
with open(base_dir + '/config/copytraders.json', 'r') as file:
    copytraders = json.load(file)


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
    timeout = httpx.Timeout(60.0)  # Timeout total de 60 secondes
    async with httpx.AsyncClient(http2=True, timeout=timeout) as session:
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
            print(url)
            json_data = json.loads(cache_leaderboard)
            for leaderRecommendInfoList in json_data['result']['leaderRecommendInfoList']:
                title = leaderRecommendInfoList['title']
                if title == "":
                    title = leaderRecommendInfoList['leaderTag'].replace('LEADER_TAG_', '')

                for position, users in enumerate(leaderRecommendInfoList['leaderRecommendDetailList']):
                    user = users['nickName']
                    if (user == username):
                        aInfos.append({
                            "user": username,
                            "leadbordtype": title,
                            "position" : position +1, 
                        })

            print(json.dumps(json_data, indent=4))
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
async def check_vaults(ctx, fromTask=False):
    global channelIdHL
    if not fromTask:
        if ctx.channel.id != channelIdHL:
            print('From not authorized channel')
            return

    #                                           ### Accounts to check
    copytraders = []
    with open(base_dir + '/config/copytraders.json', 'r') as file:
        copytraders = json.load(file)

    for copytrader in copytraders:
        if copytrader['exchange'] != 'hyperliquid':
            continue

        followersEquity = 0.0
        nbFollowers = 0
        usdc_value = 0.0

        #                                           ### is Hyperliquid vault
        url = 'https://api-ui.hyperliquid.xyz/info'

        headers = {
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }

        data = {
            "type": "vaultDetails",
            "vaultAddress": copytrader['bbCode'] 
        }

        response = requests.post(url, headers=headers, json=data)

        # Afficher le contenu de la réponse
        response_json = response.json()
        leaderEquity = 0.0
        i = 0
        for followers in response_json['followers']:
            if i == 0:
                leaderEquity = float(followers['vaultEquity'])
            else:
                followersEquity += float(followers['vaultEquity'])
                nbFollowers = nbFollowers + 1
            i = i + 1

        usdc_value = leaderEquity

        apr = response_json['apr'] * 100

        #                                           ### Build message / Discord mobile = 29 caractères
        messageToSend = ""
        messageToSend += f"{copytrader['bbUser'].upper():<15} {apr:>12,.0f}%\n"
        messageToSend += f"..............................\n"
        if nbFollowers > 0:
            messageToSend += f"{'NbFollowers':<16} {'Equ. Foll.':>12}\n"
            messageToSend += f"👥{nbFollowers:<15} {followersEquity:>10,.2f}$\n"
            messageToSend += f"..............................\n"

        await ctx.send("```" + messageToSend + "```")

        vaultLinkMessage = f"\
            **[Vault Link {copytrader['bbUser']}](https://app.hyperliquid.xyz/vaults/{copytrader['bbCode']})**\
        "
        await ctx.send(vaultLinkMessage)

        # Extraire les données de "week"
        extractPeriod = "week"
        month_data = None
        for item in response_json['portfolio']:
            if item[0] == extractPeriod:
                month_data = item[1]
                break
        if month_data is not None:
            pnl_history = month_data["pnlHistory"]
            timestamps = [datetime.fromtimestamp(int(entry[0])/1000) for entry in pnl_history]
            pnl_values = [float(entry[1]) for entry in pnl_history]

            # Création du graphique
            plt.figure(figsize=(10, 5))
            plt.plot(timestamps, pnl_values, marker='o')
            plt.title('PnL History - ' + extractPeriod)
            plt.xlabel('Date')
            plt.ylabel('PnL Value')
            plt.grid(True)

            # Sauvegarder le graphique
            plt.savefig('./tmp/pnl_history_month.png')

            # Fermer la figure
            plt.close()
            with open('./tmp/pnl_history_month.png', 'rb') as f:
                picture = discord.File(f)
                await ctx.send(file=picture)
        else:
            print("Aucune donnée trouvée pour '" + extractPeriod "'.")

       





@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command()
async def check_traders(ctx, fromTask=False):
    with open(base_dir +'/config/copytraders.json', 'r') as file:
        copytraders = json.load(file)
    global channelId
    global last_check_time
    global cache_leaderboard
    cache_leaderboard = ""
    if not fromTask:
        if ctx.channel.id != channelId:
            print('From not authorized channel')
            return
    print(' ici l 270')
    timestamp = int(time.time() * 1000)

    traders_info = []
    traders_info2 = []
    # message = await ctx.send("https://i.imgur.com/c4AGtzM.gif", reference=ctx.message) # generate a bug on Cron 
    message = await ctx.send("Loading data, please wait...")
    print(' ici l 277')
 
    timeout = httpx.Timeout(60.0)  # Timeout total de 60 secondes

    async with httpx.AsyncClient(http2=True, timeout=timeout) as session:
        for infos in copytraders:
            if infos['exchange'] == "bybit":
                url = f"https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income?timeStamp={timestamp}&leaderMark={infos['bbCode']}"
                urlInfo = f"https://api2.bybit.com/fapi/beehive/private/v1/pub-leader/info?timeStamp={timestamp}&language=en&leaderMark={infos['bbCode']}"
                HEADERS = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }
                try:
                    print(' ici l 288')
                    print(url)
                    response = await session.get(url, headers=HEADERS) 
                    print(urlInfo)
                    infosUser = await session.get(urlInfo, headers=HEADERS) 
                    print(' ici l 291')
                    #print(urlInfo)
                    #print(infosUser)
                    infosUser = json.loads(infosUser.text) 
                    json_data = json.loads(response.text)
                    followers = json_data['result']['currentFollowerCount']
                    followers_pnl = round(float(json_data['result']['ninetyDayFollowerYieldE8']) / 100000000, 2)
                    stability = json_data['result']['stableScoreLevelFormat']
                    roi30j = int(json_data['result']['ninetyDayYieldRateE4']) / 100
                    aum = int(json_data['result']['aumE8']) / 100000000
                    nbdays = int(infosUser['result']['tradeDays'])
                    sharpe = round(int(json_data['result']['ninetyDaySharpeRatioE4']) / 10000, 2)
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

                    fire_emoji = "🔥" if roi30j >= 65.00 else ""

                    aLeaderboard = (await getUserLeaderBoard(infos['bbUser']))


                    leaderboardtext = ""
                    for leaderboard in aLeaderboard:
                        leaderboard['position'] = str(leaderboard['position']) + "°"
                        leaderboardtext += f"🏆 **{leaderboard['position']} {leaderboard['leadbordtype']}**\n" if leaderboard['position'] else f"\n"

                    trader_info = f"**[{infos['bbUser']}](https://www.bybit.com/copyTrade/trade-center/detail?leaderMark={infos['bbCode']})**\n" \
                                f"🗓️ **{nbdays}** Days\n" \
                                f"🎯 ROI (90D): **{roi30j}%** {fire_emoji} {roi_arrow}\n" \
                                f"👤 Followers: **{followers}** {follower_arrow}\n" \
                                f"👥 Flw PNL: **{format_aum(followers_pnl)}$** {followers_pnl_arrow}\n" \
                                f"💰 AUM: **{format_aum(aum)}$** {aum_arrow}\n" \
                                f"⚖️ Stability: **{stability}** {stability_arrow}\n" \
                                f"🔪 Sharpe (90D): **{sharpe:.2f}** {sharpe_arrow}\n" \
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
            embed = discord.Embed(title='╔════════════( Copy Traders BYBIT 90D )════════════╗', color=discord.Color(int("2b2d31", 16)))




            if infos['exchange'] == "binance":
                url = f"https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/detail?portfolioId={infos['bbCode']}"
                urlInfo = f"https://www.binance.com/bapi/futures/v1/public/future/copy-trade/lead-portfolio/performance?portfolioId={infos['bbCode']}&timeRange=90D"
                HEADERS = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            }
            
                try:
                    print(urlInfo)
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
                    timestamp_today = int(time.time())
                    days = (timestamp_today - timestamp_trader) / (24 * 3600) 

                    sharpe_message = f"🔪 Sharpe : **{float(sharpe):.2f}** {sharpe_arrow}\n" if days >= 30 else ""
                    


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

                    fire_emoji = "🔥" if roi30j >= 65.00 else ""

                    trader_info2 = f"**[{infos['bbUser'].replace('_binance', '')}](https://www.binance.com/en/copy-trading/lead-details?portfolioId={infos['bbCode']})**\n" \
                                f"🗓️ **{days:.0f}** Days\n" \
                                f"🎯 ROI: **{roi30j:.2f}%** {fire_emoji} {roi_arrow}\n" \
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

        traders_info.sort(reverse=True, key=lambda x: x[0])
        traders_info2.sort(reverse=True, key=lambda x: x[0])

        embed.description = f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Total AUM: __**{format_aum(total_aum)}$**__"
        embed2.description = f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Total AUM: __**{format_aum(total_aum2)}$**__"
        total_aum = 0
        total_aum2 = 0

        embed_2 = discord.Embed(title='╠════════════( Copy Traders BYBIT 90D )════════════╣', color=discord.Color(int("2b2d31", 16)))
        embed_3 = discord.Embed(title='╚════════════( Copy Traders BYBIT 90D )════════════╝', color=discord.Color(int("2b2d31", 16)))
        for i, (roi, trader_info) in enumerate(traders_info, start=1):
            if i <= 15:
                embed.add_field(name=f"", value=f"**{i}.** "+trader_info, inline=True)
            elif i > 15 and i <= 30:
                embed_2.add_field(name=f"", value=f"**{i}.** "+trader_info, inline=True)
            elif i > 30 and i <= 45:
                embed_3.add_field(name=f"", value=f"**{i}.** "+trader_info, inline=True)

        for i, (roi, trader_info2) in enumerate(traders_info2, start=1):
            embed2.add_field(name=f"", value=f"**{i}.** "+trader_info2, inline=True)

        await ctx.send(content="", embed=embed)
        await ctx.send(content="", embed=embed_2)
        await ctx.send(content="", embed=embed_3)
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
    global channelIdHL
    channelHL = bot.get_channel(channelIdHL)

    await check_vaults(channelHL, fromTask=True)

    global channelId
    channel = bot.get_channel(channelId)

    await check_traders(channel, fromTask=True)


scheduler = AsyncIOScheduler()
scheduler.add_job(cronFunction, CronTrigger(hour="8", minute="0", second="0"))
# scheduler.add_job(cronFunction, 'interval', seconds=5)

scheduler.start()

bot.run(discordBotId)
