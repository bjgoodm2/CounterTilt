from decimal import *
import requests, riotwatcher, datetime, operator
from api_wrapper import platforms, LoLException, RiotWatcher

API_KEY = 'b5dc6253-ade4-471b-afde-c452a7990125'
CURR_SEASON = 'SEASON2016'

key = API_KEY
rw = RiotWatcher(API_KEY)
latest_version = rw.static_get_versions()[0]

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
    return 'http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ_key}'.format(
        version=latest_version,
        champ_key=champion['image']['full'])


# fetches the image url associated with the given summoner spell id
def get_ss_image_url(ss_id):
    ss = rw.static_get_summoner_spell(ss_id, spell_data='image')
    return 'http://ddragon.leagueoflegends.com/cdn/{version}/img/spell/{spell_key}'.format(
        version=latest_version,
        spell_key=ss['image']['full'])


# fetches the image url associated with the given profile icon id
def get_profile_image_url(profile_icon_id):
    return 'http://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{profile_icon_key}.png'.format(
        version=latest_version,
        profile_icon_key=profile_icon_id)


# fetches the image url associated with the given item id
def get_item_image_url(item_id):
    print('getting item url and name')
    latest_version = rw.static_get_versions()[0]
    dict = {}
    if item_id == 0:
        dict['url'] = 'http://solomid-resources.s3-website-us-east-1.amazonaws.com/probuilds/img/items/28/EmptyIcon.png'
        dict['name'] = '-'
    else:
        dict['url'] = 'http://ddragon.leagueoflegends.com/cdn/{version}/img/item/{item_key}.png '.format(
            version=latest_version,
            item_key=item_id)
        item = rw.static_get_item(item_id)
        dict['name'] = item['name']
    print('got item url and name')
    return dict


# returns a dictionary with season stats, as well as info about the champion being played in the current game
def get_ranked_stats(summoner_id, region, current_champ_id):
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
    dict['totalGames'] = dict['wins'] + dict['losses']
    dict['champKills'] = stat_summary['aggregatedStats']['totalChampionKills']
    dict['turretKills'] = stat_summary['aggregatedStats']['totalTurretsKilled']
    dict['minionKills'] = stat_summary['aggregatedStats']['totalMinionKills'] + stat_summary['aggregatedStats'][
        'totalNeutralMinionsKilled']
    dict['mostPlayedChamps'] = get_most_played_champs(summoner_id, region)
    dict['currentChampInfo'] = get_specific_champ_stats(summoner_id, region, current_champ_id)
    print('got ranked stats')
    return dict


# returns a dictionary of a summoner's most played champs and information about those champions
def get_most_played_champs(summoner_id, region):
    champions = []
    stats = rw.get_ranked_stats(summoner_id, region=region)
    for champion in stats['champions']:
        champ_stats = {}
        champ_stats['id'] = champion['id']
        champ_stats['totalGames'] = champion['stats']['totalSessionsPlayed']
        champ_stats['wins'] = champion['stats']['totalSessionsWon']
        champ_stats['losses'] = champion['stats']['totalSessionsLost']
        champ_stats['kills'] = champion['stats']['totalChampionKills']
        champ_stats['deaths'] = champion['stats']['totalDeathsPerSession']
        champ_stats['assists'] = champion['stats']['totalAssists']
        champ_stats['totalPentaKills'] = champion['stats']['totalPentaKills']
        champ_stats['maxKills'] = champion['stats']['maxChampionsKilled']
        champ_stats['maxDeaths'] = champion['stats']['maxNumDeaths']
        champions.append(champ_stats)
    champions.sort(key=operator.itemgetter('totalGames'), reverse=True)
    return champions


# grab useful stats about the participant's current champion being played
# these stats are pulled from this participant's past games with this champion
def get_specific_champ_stats(summoner_id, region, current_champ_id):
    stats = rw.get_ranked_stats(summoner_id, region=region)
    for champion in stats['champions']:
        if champion['id'] == current_champ_id:
            champ_stats = {}
            champ_stats['id'] = champion['id']
            champ_stats['totalGames'] = champion['stats']['totalSessionsPlayed']
            champ_stats['wins'] = champion['stats']['totalSessionsWon']
            champ_stats['losses'] = champion['stats']['totalSessionsLost']
            champ_stats['kills'] = round(Decimal(champion['stats']['totalChampionKills'])/Decimal(champion['stats']['totalSessionsPlayed']), 1)
            champ_stats['deaths'] = round(Decimal(champion['stats']['totalDeathsPerSession'])/Decimal(champion['stats']['totalSessionsPlayed']), 1)
            champ_stats['assists'] = round(Decimal(champion['stats']['totalAssists'])/Decimal(champion['stats']['totalSessionsPlayed']), 1)
            champ_stats['totalPentaKills'] = champion['stats']['totalPentaKills']
            champ_stats['maxKills'] = champion['stats']['maxChampionsKilled']
            champ_stats['maxDeaths'] = champion['stats']['maxNumDeaths']
            champ_stats['totalDamageDealt'] = champion['stats']['totalDamageDealt']
            champ_stats['totalGold'] = champion['stats']['totalGoldEarned']
            print('got current game champ stats')
            return champ_stats
    # if not found, champ has not been played before
    champ_stats = {}
    champ_stats['id'] = 0
    champ_stats['totalGames'] = 0
    champ_stats['wins'] = 0
    champ_stats['losses'] = 0
    champ_stats['kills'] = 0
    champ_stats['deaths'] = 0
    champ_stats['assists'] = 0
    champ_stats['totalPentaKills'] = 0
    champ_stats['maxKills'] = 0
    champ_stats['maxDeaths'] = 0
    champ_stats['totalDamageDealt'] = 0
    champ_stats['totalGold'] = 0
    print('got current game champ stats')
    return champ_stats


# returns a dictionary of any applicable 'badges' for this participant, given his streak info as well
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
        new_dict['title'] = 'On tilt -- has lost ' + str(loss_count) + ' recent games in a row.'
        list.append(new_dict)
    # check for champKills, turretKills, minionKills badges
    champs_per_game = round(Decimal(participant['stats']['champKills']) / Decimal(participant['stats']['totalGames']), 2)
    turrets_per_game = round(Decimal(participant['stats']['turretKills']) / Decimal(participant['stats']['totalGames']), 2)
    cs_per_game = round(Decimal(participant['stats']['minionKills']) / Decimal(participant['stats']['totalGames']))
    if champs_per_game > 7.25:
        new_dict = {}
        new_dict['badgePath'] = 'helmet.png'
        new_dict['title'] = 'Kills ' + str(champs_per_game) + ' champions per game!'
        list.append(new_dict)
    if turrets_per_game > 1.6:
        new_dict = {}
        new_dict['badgePath'] = 'castle.png'
        new_dict['title'] = 'Kills ' + str(turrets_per_game) + ' turrets per game!'
        list.append(new_dict)
    if cs_per_game > 200:
        new_dict = {}
        new_dict['badgePath'] = 'farmer.png'
        new_dict['title'] = 'Consistently farms well! ' + str(cs_per_game) + ' minions per game!'
        list.append(new_dict)
    # is this player playing one of his 5 mostPlayedChamps?
    for champ in participant['stats']['mostPlayedChamps'][:5]:
        if participant['championId'] == champ['id']:
            new_dict = {}
            new_dict['badgePath'] = 'warrior.png'
            new_dict['title'] = 'One of this player\'s 5 most played champs! \n' \
                                'Has played ' + str(champ['totalGames']) + ' games with this champ!'
            list.append(new_dict)
    for champ in participant['stats']['mostPlayedChamps']:
        if participant['championId'] == champ['id']:
            if champ['totalGames'] < 10:
                new_dict = {}
                new_dict['badgePath'] = 'newchamp.png'
                new_dict['title'] = 'This player has only played ' + str(champ['totalGames']) + ' games with this champ'
                list.append(new_dict)
            if champ['totalPentaKills'] > 0:
                new_dict = {}
                new_dict['badgePath'] = 'pentakill.png'
                new_dict['title'] = 'This player has gotten ' + str(
                    champ['totalPentaKills']) + ' pentakill(s) with this champ!'
    # has this player gotten first Blood more than once in his last 5 games?
    firstBlooded = 0
    for info in streak_info[:5]:
        if info['firstBlood']:
            firstBlooded += 1
    if firstBlooded > 1:
        new_dict = {}
        new_dict['badgePath'] = 'blood.png'
        new_dict['title'] = 'This player has gotten First Blood ' + str(firstBlooded) + ' times in the last 5 games!'
        list.append(new_dict)
    # is this player new to this division?
    if participant['stats']['rookie']:
        new_dict = {}
        new_dict['badgePath'] = 'baby.png'
        new_dict['title'] = 'This player is new to this division'
        list.append(new_dict)
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


# gets information about a certain match passed in by id
def get_match_info(match, summoner_id, region):
    match = rw.get_match(match['matchId'], region=region)
    print('dict forming')
    summoner = find_summoner_in_match(match, summoner_id)
    match['winner'] = summoner['stats']['winner']
    match['items'] = []
    for i in xrange(6):
        match['items'].append(get_item_image_url(summoner['stats']['item' + str(i)]))
    match['trinket'] = get_item_image_url(summoner['stats']['item6'])
    m, s = divmod(match['matchDuration'], 60)
    match['duration'] = "%02d:%02d" % (m, s)
    match['kills'] = summoner['stats']['kills']
    match['deaths'] = summoner['stats']['deaths']
    match['assists'] = summoner['stats']['assists']
    match['ssImg1'] = get_ss_image_url(summoner['spell1Id'])
    match['ssImg2'] = get_ss_image_url(summoner['spell2Id'])
    match['firstBlood'] = summoner['stats']['firstBloodKill'] or summoner['stats']['firstBloodAssist']
    match['firstTower'] = summoner['stats']['firstTowerKill'] or summoner['stats']['firstTowerAssist']
    match['firstInhibitor'] = summoner['stats']['firstInhibitorKill'] or summoner['stats']['firstInhibitorAssist']
    match['champLevel'] = summoner['stats']['champLevel']
    match['minions'] = summoner['stats']['minionsKilled']
    match['monsters'] = summoner['stats']['neutralMinionsKilled']
    match['enemyJg'] = summoner['stats']['neutralMinionsKilledEnemyJungle']
    match['friendlyJg'] = summoner['stats']['neutralMinionsKilledTeamJungle']
    match['csPerMin'] = float(summoner['stats']['minionsKilled'] + summoner['stats']['neutralMinionsKilled']) / float(
        match['matchDuration'] / 60)
    match['pentaKills'] = summoner['stats']['pentaKills']
    match['gold'] = summoner['stats']['goldEarned']
    print('dict formed')
    # get each of the other participants' names and champion images
    get_match_participants(match)
    match['killParticipation'] = kill_participation(match, summoner)
    # get information about the summoner's champion played this game, so we can provide improvement suggestions
    match['currentChampInfo'] = get_specific_champ_stats(summoner_id, region, summoner['championId'])
    return match


# gets participant names and their corresponding champions played for a given match
# this match dictionary must be of the format provided by RiotWatcher's get_match
def get_match_participants(match):
    print 'getting match participants'
    for pi in match['participantIdentities']:
        name = pi['player']['summonerName']
        participant_id = pi['participantId']
        for p in match['participants']:
            if p['participantId'] == participant_id:
                p['champImg'] = get_champion_image_url(p['championId'])
                p['name'] = name
    print('got match participants')


# returns a player's kill participation in a game, based off of how many kills their team had, and how many
# kills that player was a part of (took the kill or had an assist)
def kill_participation(match, summoner):
    team_kills = 0
    for p in match['participants']:
        if p['teamId'] == summoner['teamId']:
            team_kills += p['stats']['kills']
    summoner_ka = summoner['stats']['kills'] + summoner['stats']['assists']
    kp = round(Decimal(summoner_ka)/Decimal(team_kills) * 100, 2)
    print('got kill participation')
    return kp


# get streak info, this is info about a player's last 10 matches, including whether or not they won
# those matches, and whether or not they got first Blood in those matches
def get_streak_info(summoner_id, region):
    match_list = rw.get_match_list(summoner_id, region=region, begin_index=0, end_index=10)
    list = []
    for match in match_list['matches']:
        match = rw.get_match(match['matchId'], region=region)
        summoner = find_summoner_in_match(match, summoner_id)
        summoner['stats']['firstBlood'] = False
        if summoner['stats']['firstBloodKill'] or summoner['stats']['firstBloodAssist']:
                summoner['stats']['firstBlood'] = True
        if summoner['stats']['winner']:
            summoner['stats']['icon'] = 'check-circle'
            summoner['stats']['color'] = '#2ecc71'
            list.append(summoner['stats'])
        else:
            summoner['stats']['icon'] = 'times-circle'
            summoner['stats']['color'] = '#e74c3c'
            list.append(summoner['stats'])
    print ('got streak info')
    return list
