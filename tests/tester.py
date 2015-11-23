from pprint import pprint
import countertilt as ct

rw = ct.RiotWatcher(ct.API_KEY)

summoner = rw.get_summoner(name='suryD')

match_list = rw.get_match_list(summoner['id'], begin_index=0, end_index=10)
current_game = rw.get_current_game(summoner['id'])
# get match info, champ info for the match, and streak info
for match in match_list['matches']:
    match['info'] = ct.get_match_info(match['matchId'], summoner['id'])
match_list['streak_info'] = []
match_list['streak_info'] = ct.get_streak_info(match_list['matches'])
for info in match_list['streak_info']:
    pprint(info)
