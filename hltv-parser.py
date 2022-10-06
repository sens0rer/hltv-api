import hltvapi as hltv
import datetime
from lxml import html
import requests
from bs4 import BeautifulSoup

def getTeamInfo(teamid, teamname):
    teamInfo = {}
    teamInfo['Team ID'] = teamid
    teamInfo['Team name'] = teamname.lower()
    page = requests.get('https://www.hltv.org/team/' + str(teamid) + '/' + teamname.lower())
    htmlstr = page.text
    
    start = htmlstr.find('<div class="profile-team-stat"><b>World ranking</b>')
    ranking = htmlstr[start:]
    start = ranking.find('#')
    end = ranking.find('</a>')
    ranking = int(ranking[start+1:end])
    teamInfo['World ranking'] = ranking
    
    start = htmlstr.find('<div class="profile-team-stat"><b>Weeks in top30 for core</b>')
    weeksInTop30 = htmlstr[start+81:]
    end = weeksInTop30.find("</span>")
    weeksInTop30 = int(weeksInTop30[0:end])
    teamInfo['Weeks in top30 for core'] = weeksInTop30
    
    start = htmlstr.find('<div class="profile-team-stat"><b>Coach</b>')
    if start != -1:
        coach = htmlstr[start+60:]
        end = coach.find('"')
        coach = coach[0:end]
        coach = coach.split('/')
        teamInfo['Coach'] = {'Name': coach[1],
                             'ID': coach[0]}
    else:
        teamInfo['Coach'] = {'Name': None,
                             'ID': None}
    
    players_raw = hltv.get_players(teamid)
    players = []
    for player in players_raw:
        playerdict = {"Name": player['nickname'].lower(),
                      'ID': player['id']}
        players.append(playerdict)
    teamInfo['Players'] = players
    
    return teamInfo

def _extractPlayerStats(htmlstr, prompt):
    start = htmlstr.find(prompt)
    htmlstr = htmlstr[start:]
    start = htmlstr.find('Val')
    end = htmlstr.find('</span>')
    htmlstr = htmlstr[start+5:end]
    return htmlstr


def getPlayerInfo(playerid, nickname):
    playerInfo = {}
    playerInfo['ID'] = playerid
    playerInfo['Name'] = nickname.lower()
    page = requests.get('https://www.hltv.org/player/' + str(playerid) + '/' + nickname.lower())
    htmlstr = page.text
    
    playerInfo['Rating 2.0'] = float(_extractPlayerStats(htmlstr, 'Rating 2.0'))
    playerInfo['Kills per round'] = float(_extractPlayerStats(htmlstr, 'Kills per round'))
    playerInfo['Headshots'] = float(_extractPlayerStats(htmlstr, 'Headshots')[0:-1])/100
    playerInfo['Maps played'] = int(_extractPlayerStats(htmlstr, 'Maps played'))
    playerInfo['Deaths per round'] = float(_extractPlayerStats(htmlstr, 'Deaths per round'))
    playerInfo['Rounds contributed'] = float(_extractPlayerStats(htmlstr, 'Rounds contributed')[0:-1])/100

    return playerInfo

def getMatchInfo(url):
    pass

matches = hltv.get_matches()