#!/usr/local/bin/python2.7

# Use to get port # from Heroku environment
from os import environ

# Regular Expressions (meh, ok, alright.)
import re

# JSON import
import json
from bson import json_util

# Datetime import for getting current date
# And rate limiting new game requests
import datetime
last_game_save_datetime = datetime.datetime.now() - datetime.timedelta(minutes=2)

# Math import for ELO calculations
import math

# Mongo import and connection to pong-ranking mongoDB instance
from pymongo import MongoClient
mongo_user = 'pong-rating'
mongo_pass = 'pong-rating'
mongodb_uri = 'mongodb://' + mongo_user + ':' + mongo_pass + '@ds013206.mlab.com:13206/heroku_vbhz283w'
mongo_client = MongoClient(mongodb_uri)
db = mongo_client.heroku_vbhz283w

# Flask import
from flask import Flask, jsonify, render_template, request, Response
app = Flask(__name__)
app.secret_key = 'abc8302c9df0e8fa81' # Random secret key


"""
Class to perform ELO manipulations
"""
K_FACTOR = 90
class elo_core:

	@classmethod
 	def getExpectation(self, rating_1, rating_2):
		calc = (1.0 / (1.0 + pow(10, ((rating_2 - rating_1) / 400))));
		return calc;

	@classmethod
	def modifyRating(self, rating, expected, actual):
		calc = rating + (K_FACTOR * (actual - expected));
		return calc;


"""
Normalize team names - .title() each name and alphabetize them
"""
def normalize_team_name(team_name):
	team_name = team_name.lower()
	team_names = team_name.split(' ')
	if 'and' in team_names:
		team_names.remove('and')
	team_names.sort()
	return team_names[0].title() + ' and ' + team_names[1].title()


# Define Flask routes
# ---======= HTML Routes =======---
@app.route('/')
def root():
    return render_template('index.html')

@app.route('/players', methods=['GET', 'POST'])
def players():
	return render_template('players.html')

@app.route('/teams', methods=['GET', 'POST'])
def teams():
	return render_template('teams.html')

@app.route('/new_game', methods=['GET', 'POST'])
def new_game():
	return render_template('new_game.html')

@app.route('/view_games', methods=['GET', 'POST'])
def view_games():
	return render_template('view_games.html')



# ---====== Data Routes ======---
"""
Save new game and update all player/team data in mongoDB
"""
@app.route('/save_new_game', methods=['GET', 'POST'])
def save_new_game():

	# Access writeable global datetime
	global last_game_save_datetime

	# Rate limit game saving to once per 10 seconds ()
	if (last_game_save_datetime > datetime.datetime.now() - datetime.timedelta(seconds=10)):
		#404 NOT FOUND (for now)
		return json.dumps({'success': True}), 404, {'ContentType': 'application/json'} 
	else:
		last_game_save_datetime = datetime.datetime.now()

	# Get current time in our format
	time_format = "%B %d, %Y at %I:%M:%S %p"
	time_adjusted = datetime.datetime.now() - datetime.timedelta(hours=4)
	date = time_adjusted.strftime(time_format)

	# Read request args
	is_doubles = False
	winning_team = request.args.get('winning_team')
	losing_team = request.args.get('losing_team')
	score = request.args.get('score')

	# Determine if we have a doubles match
	if ' and ' in winning_team:
		is_doubles = True

	# Define new game
	new_game = {}
	new_game['entryDate'] = date

	# Normalize team names
	if is_doubles:
		new_game['wt'] = normalize_team_name(winning_team)
		new_game['lt'] = normalize_team_name(losing_team)
	else:
		new_game['wt'] = winning_team.title()
		new_game['lt'] = losing_team.title()

	new_game['score'] = score

	# Insert new game into mongoDB
	db.games.insert_one(new_game)


	# Find each team in DB - if they dont exist, start with 1500 elo and default values
	# If doubles - check for players in either order and do it without giving a fuck about case
	if is_doubles:
		winners = winning_team.split(' and ')
		winning_cursor = db.teams.find({ 'player': normalize_team_name(winning_team) })
	# Else attempt to get singles player
	else:
		winning_cursor = db.players.find({ 'player': winning_team.title() })

	if winning_cursor.count() > 0: # Not a new player
		for doc in winning_cursor:
			json_doc = json.dumps(doc, default=json_util.default)
			wt_json = json.loads(json_doc)
	else: # New player - use default data to start
		wt_json = { 'player': winning_team, 'ELO': 1500, 'wins': 0, 'losses': 0, 'win_pct': 0, 'current_win_streak': 0, 'longest_win_streak': 0 }


	# If doubles - check for players in either order and do it without giving a fuck about case
	if is_doubles:
		losers = losing_team.split(' and ')
		losing_cursor = db.teams.find({ 'player': normalize_team_name(losing_team) })
	# Else attempt to get singles player
	else:
		losing_cursor = db.players.find({ 'player': losing_team.title() })

	if losing_cursor.count() > 0: # Not a new player
		for doc in losing_cursor:
			json_doc = json.dumps(doc, default=json_util.default)
			lt_json = json.loads(json_doc)
	else: # New player - use default data to start
		lt_json = { 'player': losing_team, 'ELO': 1500, 'wins': 0, 'losses': 0, 'win_pct': 0, 'current_win_streak': 0, 'longest_win_streak': 0 }


	# Calculate new ELOs	
	wt_elo = wt_json['ELO']
	lt_elo = lt_json['ELO']

	expected = elo_core.getExpectation(wt_elo, lt_elo)

	wt_elo_update = elo_core.modifyRating(wt_elo, expected, 1)
	lt_elo_update = elo_core.modifyRating(lt_elo, expected, 0)

	# Update winner info
	wt_json['ELO'] = wt_elo_update
	wt_json['wins'] = wt_json['wins'] + 1
	wt_json['current_win_streak'] = wt_json['current_win_streak'] + 1
	if (wt_json['current_win_streak'] > wt_json['longest_win_streak']):
		wt_json['longest_win_streak'] = wt_json['current_win_streak']
	wt_json['win_pct'] = (wt_json['wins'] / float(wt_json['losses'] + wt_json['wins'])) * 100

	# Update loser info
	lt_json['ELO'] = lt_elo_update
	lt_json['losses'] = lt_json['losses'] + 1
	lt_json['current_win_streak'] = 0
	lt_json['win_pct'] = (lt_json['wins'] / float(lt_json['losses'] + lt_json['wins'])) * 100

	# Clean mongoDB _id property from json if exists
	wt_json.pop('_id', None)
	lt_json.pop('_id', None)

	# Normalize team names
	if (is_doubles):
		wt_json['player'] = normalize_team_name(winning_team)
		lt_json['player'] = normalize_team_name(losing_team)
	else:
		wt_json['player'] = winning_team.title()
		lt_json['player'] = losing_team.title()

	# Upsert new player data into mongoDB
	if (is_doubles):
		db.teams.update({ 'player': wt_json['player'] }, wt_json, upsert=True)
		db.teams.update({ 'player': lt_json['player'] }, lt_json, upsert=True)
	else:
		db.players.update({ 'player': winning_team.title() }, wt_json, upsert=True)
		db.players.update({ 'player': losing_team.title() }, lt_json, upsert=True)

	# Yay success !!
	return json.dumps({'success': True}), 200, {'ContentType': 'application/json'} 


"""
Find all TEAMS and return their JSON
"""
@app.route('/get_teams_history', methods=['GET', 'POST'])
def get_teams_history():
	cursor = db.teams.find()
	cursor_count = cursor.count()
	print '\n\nTeams query returned ' + str(cursor_count) + ' results.\n'
	responseDict = {}
	i = 0;
	if cursor_count > 0:
		for doc in cursor:
			json_doc = json.dumps(doc, default=json_util.default)
			responseDict[str(i)] = json.loads(json_doc)
			i = i + 1
	return jsonify(responseDict)


"""
Find all PLAYERS and return their JSON
"""
@app.route('/get_player_history', methods=['GET', 'POST'])
def get_player_history():
	cursor = db.players.find()
	cursor_count = cursor.count()
	print '\n\nPlayers query returned ' + str(cursor_count) + ' results.\n'
	responseDict = {}
	i = 0;
	if cursor_count > 0:
		for doc in cursor:
			json_doc = json.dumps(doc, default=json_util.default)
			responseDict[str(i)] = json.loads(json_doc)
			i = i + 1

	return jsonify(responseDict)


"""
Find all GAMES and return their JSON
"""
@app.route('/get_game_history', methods=['GET', 'POST'])
def get_game_history():
	cursor = db.games.find()
	cursor_count = cursor.count()
	print '\n\nGames query returned ' + str(cursor_count) + ' results.\n'
	responseDict = {}
	i = 0;
	if cursor_count > 0:
		for doc in cursor:
			json_doc = json.dumps(doc, default=json_util.default)
			responseDict[str(i)] = json.loads(json_doc)
			i = i + 1
	return jsonify(responseDict)


if __name__ == '__main__':
    port = int(environ.get('PORT', 5000)) # Get port number from Heroku environment (assigned automatically)
    app.run(debug=True, host='0.0.0.0', port=port)