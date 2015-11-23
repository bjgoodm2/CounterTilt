import shutil
import requests
import riotwatcher
import datetime
from flask import render_template
from riotwatcher import platforms, LoLException, RiotWatcher

API_KEY = '87258093-0098-49d5-8e90-5f0bcad77964'
CURR_SEASON = 'SEASON2015'

key = API_KEY
rw = RiotWatcher(API_KEY)

# abbreviated platforms for use in views
abbrev_platforms = {
    riotwatcher.BRAZIL: 'BR1',
    riotwatcher.EUROPE_NORDIC_EAST: 'EUN1',
    riotwatcher.EUROPE_WEST: 'EUW1',
    riotwatcher.KOREA: 'KR',
    riotwatcher.LATIN_AMERICA_NORTH: 'LA1',
    riotwatcher.LATIN_AMERICA_SOUTH: 'LA2',
    riotwatcher.NORTH_AMERICA: 'NA1',
    riotwatcher.OCEANIA: 'OC1',
    riotwatcher.RUSSIA: 'RU',
    riotwatcher.TURKEY: 'TR1'
}


# fetches the image url associated with the given champ id
def get_champion_image_url(champ_id):
    champion = rw.static_get_champion(champ_id, champ_data='image')
    latest_version = rw.static_get_versions()[0]
    return 'http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ_key}'.format(
        version=latest_version,
        champ_key=champion['image']['full'])


# fetches the image url associated with the given summoner spell id
def get_ss_image_url(ss_id):
    ss = rw.static_get_summoner_spell(ss_id, spell_data='image')
    latest_version = rw.static_get_versions()[0]
    return 'http://ddragon.leagueoflegends.com/cdn/5.22.3/img/spell/{spell_key}'.format(
        version=latest_version,
        spell_key=ss['image']['full'])


# fetches the image url associated with the given profile icon id
def get_profile_image_url(profile_icon_id):
    latest_version = rw.static_get_versions()[0]
    return 'http://ddragon.leagueoflegends.com/cdn/5.22.3/img/profileicon/{profile_icon_key}.png'.format(
        version=latest_version,
        profile_icon_key=profile_icon_id)


# fetches the image url associated with the given item id
def get_item_image_url(item_id):
    latest_version = rw.static_get_versions()[0]
    if item_id == 0:
        return 'http://www.probuilds.net/resources/img/items/64/EmptyIcon.png'
    else:
        return 'http://ddragon.leagueoflegends.com/cdn/5.22.3/img/item/{item_key}.png '.format(
            version=latest_version,
            item_key=item_id)


# returns a dictionary with season stats
def get_ranked_stats(summoner_id, region):
    stats = rw.get_stat_summary(summoner_id, region=region)
    dict = {}
    # grab stats from ranked solo queue
    stat_summary = search('RankedSolo5x5', stats['playerStatSummaries'], 'playerStatSummaryType')
    # grab stats about what league this player is in
    league_stats = rw.get_league_entry([summoner_id], region=region)
    league_summary = search('RANKED_SOLO_5x5', league_stats[str(summoner_id)], 'queue')
    dict['rookie'] = league_summary['entries'][0]['isFreshBlood']
    dict['rank'] = league_summary['tier'] + ' ' + league_summary['entries'][0]['division']
    if league_summary['tier'].lower() == 'master' or league_summary['tier'].lower() == 'challenger':
        dict['rankImgPath'] = league_summary['tier'].lower() + '.png'
    else:
        dict['rankImgPath'] = league_summary['tier'].lower() + '_' + league_summary['entries'][0][
            'division'].lower() + '.png'
    dict['lp'] = league_summary['entries'][0]['leaguePoints']
    dict['streak'] = league_summary['entries'][0]['isHotStreak']
    dict['wins'] = stat_summary['wins']
    dict['losses'] = stat_summary['losses']
    dict['total_games'] = dict['wins'] + dict['losses']
    dict['champ_kills'] = stat_summary['aggregatedStats']['totalChampionKills']
    dict['turret_kills'] = stat_summary['aggregatedStats']['totalTurretsKilled']
    dict['minion_kills'] = stat_summary['aggregatedStats']['totalMinionKills'] + stat_summary['aggregatedStats'][
        'totalNeutralMinionsKilled']
    return dict


# returns a dictionary of any applicable medals
def get_badges(participant, streak_info):
    list = []
    # determine how many wins in a row this participant has
    win_count = 0
    for info in streak_info:
        if info['icon'] != 'check-circle':
            break
        else:
            win_count += 1
    # if you've won 3 or more games in a row, you're on a hot streak
    if win_count > 2:
        new_dict = {}
        new_dict['badgePath'] = 'hotstreak.png'
        new_dict['title'] = 'On a hot streak! ' + str(win_count) + ' wins in a row!'
        list.append(new_dict)
    # determine how many losses in a row this participant has
    loss_count = 0
    for info in streak_info:
        if info['icon'] == 'check-circle':
            break
        else:
            loss_count += 1
    # if you've lost 3 or more games in a row, you're on tilt
    if loss_count > 2:
        new_dict = {}
        new_dict['badgePath'] = 'snowflake.png'
        new_dict['title'] = 'On tilt -- has lost ' + str(loss_count) + ' recent games in a row'
        list.append(new_dict)
    # check for other badges
    if float(participant['stats']['champ_kills']) / float(participant['stats']['total_games']) > 7.25:
        new_dict = {}
        new_dict['badgePath'] = 'helmet.png'
        new_dict['title'] = 'Kills a high number of champions per game'
        list.append(new_dict)
    if float(participant['stats']['turret_kills']) / float(participant['stats']['total_games']) > 1.6:
        new_dict = {}
        new_dict['badgePath'] = 'castle.png'
        new_dict['title'] = 'Kills a high number of turrets per game'
        list.append(new_dict)
    if float(participant['stats']['minion_kills']) / float(participant['stats']['total_games']) > 200:
        new_dict = {}
        new_dict['badgePath'] = 'farmer.png'
        new_dict['title'] = 'Consistently farms well'
        list.append(new_dict)
    # implement 'first blood' with warning icon
    if not list:
        new_dict = {}
        new_dict['badgePath'] = 'dash.png'
        new_dict['title'] = 'No emblems?  ... Amateur.'
        list.append(new_dict)
    return list


# custom search function, searches for name in dictionary's array
def search(name, dictionary, statType):
    for element in dictionary:
        if element[statType] == name:
            return element
    return None


# finds the current summoner in the match data
def find_summoner_in_match(match, summoner_id):
    participantId = 1
    for pi in match['participantIdentities']:
        if pi['player']['summonerId'] == summoner_id:
            participantId = pi['participantId']
    for participant in match['participants']:
        if participant['participantId'] == participantId:
            return participant


def game_view_handler(request):
    # check that our summoner exists
    try:
        region = request.form['region']
        summoner = rw.get_summoner(name=request.form['search'], region=region)
    except LoLException:
        return render_template('error.html')
    # check that a current game exists
    try:
        current_game = rw.get_current_game(summoner['id'], platform_id=abbrev_platforms[region], region=region)
    except LoLException:
        # return not found page
        return render_template('game.html', current_game=None, summoner=summoner, region=region)
    # make team lists
    current_game['teams'] = {}
    current_game['teams']['blueTeam'] = []
    current_game['teams']['redTeam'] = []

    # set up the streak info at top of page for this player
    summoner['streak_info'] = []
    summoner['streak_info'] = get_streak_info(summoner['id'], region)

    # get banned champ imgs
    for bannedChamp in current_game['bannedChampions']:
        bannedChamp['img'] = get_champion_image_url(bannedChamp['championId'])
    # gather participant information
    for participant in current_game['participants']:
        participant['img'] = get_champion_image_url(participant['championId'])
        participant['spell1Img'] = get_ss_image_url(participant['spell1Id'])
        participant['spell2Img'] = get_ss_image_url(participant['spell2Id'])
        participant['profileIconImg'] = get_profile_image_url(participant['profileIconId'])
        participant['stats'] = get_ranked_stats(participant['summonerId'], region)
        # TODO: SPEED THIS PROCESS UP, TAKES 9 MINS
        # get streak info for each participant
        # participant['streak_info'] = get_streak_info(participant['summonerId'], region)
        # get badges for each participant
        # TODO: Change summoner['streak_info'] to participant['streak_info'] once speed up is achieved
        participant['badges'] = get_badges(participant, summoner['streak_info'])
        if participant['teamId'] == 100:
            current_game['teams']['blueTeam'].append(participant)
        else:
            current_game['teams']['redTeam'].append(participant)
    current_game['gameStartTime'] = datetime.datetime.fromtimestamp(
        current_game['gameStartTime'] / 1000.0).time().replace(second=0, microsecond=0)
    return render_template('game.html', current_game=current_game, summoner=summoner,
                           region=region)


# gets information about a certain match passed in by id
def get_match_info(match_id, summoner_id, region):
    match = rw.get_match(match_id, region=region)
    dict = {}
    summoner = find_summoner_in_match(match, summoner_id)
    dict['winner'] = summoner['stats']['winner']
    dict['items'] = []
    for i in range(0, 6):
        dict['items'].append(get_item_image_url(summoner['stats']['item' + str(i)]))
    m, s = divmod(match['matchDuration'], 60)
    dict['duration'] = "%02d:%02d" % (m, s)
    dict['kills'] = summoner['stats']['kills']
    dict['deaths'] = summoner['stats']['deaths']
    dict['assists'] = summoner['stats']['assists']
    dict['ssImg1'] = get_ss_image_url(summoner['spell1Id'])
    dict['ssImg2'] = get_ss_image_url(summoner['spell2Id'])
    dict['firstBlood'] = summoner['stats']['firstBloodKill'] or summoner['stats']['firstBloodAssist']
    return dict


def get_streak_info(summoner_id, region):
    match_list = rw.get_match_list(summoner_id, region=region, begin_index=0, end_index=10)
    for match in match_list['matches']:
        match['info'] = get_match_info(match['matchId'], summoner_id, region)
    list = []
    for match in match_list['matches']:
        if match['info']['winner']:
            dict = {}
            dict['icon'] = 'check-circle'
            dict['color'] = '#2ecc71'
            list.append(dict)
        else:
            dict = {}
            dict['icon'] = 'times-circle'
            dict['color'] = '#e74c3c'
            list.append(dict)
    return list


def summoner_view_handler(request):
    # check that our summoner exists
    try:
        region = request.form['region']
        summoner = rw.get_summoner(name=request.form['search'], region=region)
    except LoLException:
        # return not found page
        return render_template('error.html')
    # grab the ranked match list for that summoner
    try:
        match_list = rw.get_match_list(summoner['id'], region=region, begin_index=0, end_index=10)
    except LoLException:
        return render_template('error.html')
    # get match info, champ info for the match, and streak info
    for match in match_list['matches']:
        match['img'] = get_champion_image_url(match['champion'])
        match['champ_info'] = rw.static_get_champion(match['champion'])
        match['info'] = get_match_info(match['matchId'], summoner['id'], region)
    match_list['streak_info'] = []
    match_list['streak_info'] = get_streak_info(summoner['id'], region)
    return render_template('summoner.html', summoner=summoner, match_list=match_list, region=region)
