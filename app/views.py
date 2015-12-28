from pprint import pprint
from app import app
import datetime
import requests
from flask import Flask, render_template, redirect, url_for, request, g, send_from_directory
import countertilt as ct
from riotwatcher import platforms, LoLException, RiotWatcher

rw = RiotWatcher(ct.API_KEY)


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        if request.form['stats'] == "true":
            return redirect("/summoner/" + request.form['region'] + "/" + request.form['summonerName'])
        else:
            return redirect("/game/" + request.form['region'] + "/" + request.form['summonerName'])


@app.route('/game', methods=['POST', 'GET'])
@app.route('/game/<region>/<summoner_name>', methods=['POST', 'GET'])
def game(region, summoner_name):
    # check that our summoner exists
    try:
        summoner = rw.get_summoner(name=summoner_name, region=region)
    except LoLException:
        return render_template('error.html')
    # check that a current game exists
    try:
        current_game = rw.get_current_game(summoner['id'], platform_id=ct.abbrev_platforms[region], region=region)
    except LoLException:
        # return not found page
        return render_template('game.html', current_game=None, summoner=summoner, region=region)
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
        participant['stats'] = ct.get_ranked_stats(participant['summonerId'], region, participant['championId'])
        # TODO: I need a production key, ye God Riot Tuxedo hear my plea
        # get streak info for each participant
        participant['streak_info'] = ct.get_streak_info(participant['summonerId'], region)
        # get badges for each participant
        # TODO: Change summoner['streak_info'] to participant['streak_info'] once production key is acquired
        participant['badges'] = ct.get_badges(participant, participant['streak_info'])
        if participant['teamId'] == 100:
            current_game['teams']['blueTeam'].append(participant)
        else:
            current_game['teams']['redTeam'].append(participant)
    current_game['gameStartTime'] = datetime.datetime.fromtimestamp(
        current_game['gameStartTime'] / 1000.0).time().replace(second=0, microsecond=0)
    return render_template('game.html', current_game=current_game, summoner=summoner,
                           region=region)


@app.route('/summoner', methods=['POST', 'GET'])
@app.route('/summoner/<region>/<summoner_name>', methods=['POST', 'GET'])
def summoner(region, summoner_name):
    # check that our summoner exists
    try:
        summoner = rw.get_summoner(name=summoner_name, region=region)
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
        match['img'] = ct.get_champion_image_url(match['champion'])
        match['champ_info'] = rw.static_get_champion(match['champion'])
        match['info'] = ct.get_match_info(match, summoner['id'], region)
    match_list['streak_info'] = []
    match_list['streak_info'] = ct.get_streak_info(summoner['id'], region)
    return render_template('summoner.html', summoner=summoner, match_list=match_list, region=region)



@app.route('/riot.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
