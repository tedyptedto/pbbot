import requests
import time
import json
from urllib.parse import quote

# Liste de codes
copytraders = [
    {'discordUser':'tedyptedto', 'bbUser':'tedyptedtoCpTr', 'bbCode':"VAfEwFPZdNdfYGWiwy7V0g=="},
    {'discordUser':'LuaN', 'bbUser':'luantesting', 'bbCode':"y3R6ru2Yv6mVK3t7bebfJQ=="},
    {'discordUser':'mani', 'bbUser':'manicptlowrisk', 'bbCode':"JwT+a21FcgJXHhs6+qVxZw=="},
    {'discordUser':'mani', 'bbUser':'manicptrndr', 'bbCode':"ciOb3vGv0dp8JKJp4WTmeg=="},
    {'discordUser':'xaocarlo', 'bbUser':'xaocarlo', 'bbCode':"JKuwFA2ebE+UhjKrItsMbA=="},
]

# Timestamp actuel 
timestamp = int(time.time() * 1000)

print(f"Please wait")
for infos in copytraders:
    encoded_code = quote(infos['bbCode'], safe='')
    # Construire l'URL avec le timestamp et le code actuel
    url = f"https://api2.bybit.com/fapi/beehive/public/v1/common/leader-income?timeStamp={timestamp}&leaderMark={encoded_code}"

    # print(url)

    # Faire la requête GET à l'URL
    response = requests.get(url)

    # Vérifier si la requête a réussi (statut 200)
    if response.status_code == 200:
        # Récupérer le contenu JSON
        json_data = response.json()

        # print(json.dumps(json_data, indent=4))

        # print("Contenu JSON pour le code", infos['code'], ":", json_data)
        followers = json_data['result']['currentFollowerCount']
        stability = json_data['result']['stableScoreLevelFormat']
        roi30j = int(json_data['result']['thirtyDayYieldRateE4']) / 100
        aum = int(json_data['result']['aumE8']) / 100000000

        print(f"@{infos['discordUser']} {infos['bbUser']} => {roi30j}% https://www.bybit.com/copyTrade/trade-center/detail?leaderMark={encoded_code} ({followers} followers) (AUM {aum} USDT)")

    else:
        print("La requête a échoué pour le code", infos)