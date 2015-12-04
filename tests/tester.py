from pprint import pprint
import datetime
import countertilt as ct
from riotwatcher import LoLException

rw = ct.RiotWatcher(ct.API_KEY)

summoner_name = 'Wingsofdeathx'
region = 'na'

# check that our summoner exists
try:
    summoner = rw.get_summoner(name=summoner_name, region=region)
except LoLException:
    print ('error')
# check that a current game exists
try:
    current_game = rw.get_current_game(summoner['id'], platform_id=ct.abbrev_platforms[region], region=region)
except LoLException:
    # return not found page
    print('not in game')
# make team lists
current_game['teams'] = {}
current_game['teams']['blueTeam'] = []
current_game['teams']['redTeam'] = []
# set up the streak info at top of page for this player
summoner['streak_info'] = []
summoner['streak_info'] = ct.get_streak_info(summoner['id'], region)
# get banned champ imgs
for bannedChamp in current_game['bannedChampions']:
    bannedChamp['img'] = ct.get_champion_image_url(bannedChamp['championId'])
# gather participant information
for participant in current_game['participants']:
    participant['img'] = ct.get_champion_image_url(participant['championId'])
    participant['spell1Img'] = ct.get_ss_image_url(participant['spell1Id'])
    participant['spell2Img'] = ct.get_ss_image_url(participant['spell2Id'])
    participant['profileIconImg'] = ct.get_profile_image_url(participant['profileIconId'])
    print('getting ranked stats')
    participant['stats'] = ct.get_ranked_stats(participant['summonerId'], region, participant['championId'])
    # get streak info for each participant
    participant['streak_info'] = ct.get_streak_info(participant['summonerId'], region)
    # get badges for each participant
    participant['badges'] = ct.get_badges(participant, participant['streak_info'])
    if participant['teamId'] == 100:
        current_game['teams']['blueTeam'].append(participant)
    else:
        current_game['teams']['redTeam'].append(participant)
current_game['gameStartTime'] = datetime.datetime.fromtimestamp(
    current_game['gameStartTime'] / 1000.0).time().replace(second=0, microsecond=0)
print('we done')
