from cassandra.cluster import Cluster
from bs4 import BeautifulSoup
import requests
import pycountry
from pprint import pprint
import sys
sys.path.append(r'C:\Users\d_mas\Developer\The Beast\lib')
import utils

# Variables
players_db = dict()
countries_pycountry = ["Bolivia, Plurinational State of", "Bosnia and Herzegovina", "Czechia", "Dominican Republic", "United Kingdom", "Macedonia, Republic of", "Moldova, Republic of", "Papua New Guinea", "South Africa", "Russian Federation", "Korea, Republic of", "Taiwan, Province of China", "Tunisia", "United States", "Venezuela, Bolivarian Republic of", "Viet Nam"]
countries_te = ["Bolivia", "Bosnia and Herzeg.", "Czech Republic", "Dominican Rep.", "Great Britain", "Macedonia", "Moldavsko", "Papua N. Guinea", "RSA", "Russia", "South Korea", "Taipei (CHN)", "Tunis", "USA", "Venezuela", "Vietnam"]
abbr_pycountry = ["BGR", "BRB", "CHE", "CHL", "DEU", "DNK", "GRC", "HRV", "LVA", "MCO", "NLD", "OMN", "PRI", "PRT", "PRY", "SLV", "SVN", "TWN", "URY", "VNM", "ZAF", "ZWE"]
abbr_atp = ["BUL", "BAR", "SUI", "CHI", "GER", "DEN", "GRE", "CRO", "LAT", "MON", "NED", "OMA", "PUR", "POR", "PAR", "ESA", "SLO", "TPE", "URU", "VIE", "RSA", "ZIM"]
page = 1

# Get players from DB
cluster = Cluster(["127.0.0.1"])
session = cluster.connect("beast")

query = "SELECT player_atpwt_id, player_name, player_country FROM player_week WHERE player_rankdate = '2013-09-30'"
players = session.execute(query)

for player in players:
    player_db = dict()
    player_db['name'] = player.player_name
    player_db['country'] = player.player_country

    if not player.player_atpwt_id in players_db:
        players_db[player.player_atpwt_id] = player_db

# Close connections
session.shutdown()
cluster.shutdown()

# Get players by country from Tennis Explorer
url = "https://www.tennisexplorer.com/list-players/"
r = requests.get(url)
data = r.text
soup = BeautifulSoup(data, "html.parser")
countries = soup.select("tbody#rank-country td a")

for country in countries:
    if country.text.strip():
        country_pycountry = pycountry.countries.get(name=country.text.strip())

        if country_pycountry is None:
            country_pycountry = pycountry.countries.get(name=utils.replaceMultiple2(country.text.strip(), countries_te, countries_pycountry))

        # List players from country (DB)
        country_players = []

        for atp_id, player in players_db.items():
            if player['country'] == utils.replaceMultiple2(country_pycountry.alpha_3, abbr_pycountry, abbr_atp):
                country_players.append(atp_id)

        print(len(country_players))

        # Web scraping - Country players list from Tennis Explorer
        while page <= 32:
            print("--- PÀGINA " + str(page) + " ---")
            url = "https://www.tennisexplorer.com/list-players/" + country.get('href') + "&page=" + str(page) + "&order=rank"
            r = requests.get(url)
            data = r.text
            soup = BeautifulSoup(data, "html.parser")

            for player in soup.select("tbody.flags tr"):
                te_name = list(player.select("td"))[1].text.strip().split(", ")
                atp_id = utils.searchKeyDictionaryByValue(players_db, "name", te_name[1] + " " + te_name[0], True)

                if atp_id:
                    print("Jugador localitzat: " + te_name[1] + " " + te_name[0] + "!!!")

                    try:
                        country_players.remove(atp_id)
                    except ValueError:
                        print("Hi ha una excepció amb el mestre " + te_name[1] + " " + te_name[0])

            page += 1

        for atp_id in country_players:
            print("Falta trobar el mestre " + players_db[atp_id]['name'])

        exit()