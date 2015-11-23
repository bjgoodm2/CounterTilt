from app import app
import requests
from flask import Flask, render_template, redirect, url_for, request, g, send_from_directory
import countertilt as ct
from riotwatcher import platforms, LoLException, RiotWatcher

rw = RiotWatcher(ct.API_KEY)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/game', methods=['POST', 'GET'])
def game():
    if request.method == 'POST':
        return ct.game_view_handler(request)
    else:
        return render_template('error.html')


@app.route('/summoner', methods=['POST', 'GET'])
def summoner():
    if request.method == 'POST':
        return ct.summoner_view_handler(request)
    else:
        return render_template('error.html')

@app.route('/riot.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
