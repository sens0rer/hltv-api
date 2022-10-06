import hltvapi as hltv
import datetime
from lxml import html
import requests
from bs4 import BeautifulSoup

def getTeamInfo(teamid, teamname):
    """
    Returns a dictionary of basic team stats
    """
    teamInfo = {}
    teamInfo['Team ID'] = teamid
    teamInfo['Team name'] = teamname.lower()
    page = requests.get('https://www.hltv.org/team/' + str(teamid) + '/' + teamname.lower())
    htmlstr = page.text
    
    # extract World ranking
    start = htmlstr.find('<div class="profile-team-stat"><b>World ranking</b>')
    ranking = htmlstr[start:]
    start = ranking.find('#')
    end = ranking.find('</a>')
    ranking = int(ranking[start+1:end])
    teamInfo['World ranking'] = ranking
    
    # Extract amount of weeks in top30 for core
    start = htmlstr.find('<div class="profile-team-stat"><b>Weeks in top30 for core</b>')
    weeksInTop30 = htmlstr[start+81:]
    end = weeksInTop30.find("</span>")
    weeksInTop30 = int(weeksInTop30[0:end])
    teamInfo['Weeks in top30 for core'] = weeksInTop30
    
    # Extract coach nickname and id
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
    
    # Extract player nicknames and ids
    players_raw = hltv.get_players(teamid)
    players = []
    for player in players_raw:
        playerdict = {"Name": player['nickname'].lower(),
                      'ID': player['id']}
        players.append(playerdict)
    teamInfo['Players'] = players
    
    return teamInfo

def _extractPlayerStats(htmlstr, prompt):
    """
    Extracts required player stat(prompt) from player's page html code converted
    to string(htmlstr)
    """
    start = htmlstr.find(prompt)
    htmlstr = htmlstr[start:]
    start = htmlstr.find('Val')
    end = htmlstr.find('</span>')
    htmlstr = htmlstr[start+5:end]
    return htmlstr


def getPlayerInfo(playerid, nickname):
    """
    Returns a dictionary of player stats
    """
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

def getFinishedMatchInfo(url):
    """
    Returns a dictionary of match stats
    """
    matchInfo = {}
    matchInfo['URL'] = url
    page = requests.get(url)
    htmlstr = page.text
    
    # Team names and ids
    start = htmlstr.find('team1-gradient')
    teams = htmlstr[start+31:]
    end = teams.find('">')
    matchInfo['Team 1'] = {'Name': teams[0:end].split("/")[1],
                           'ID': teams[0:end].split("/")[0]}
    
    start = teams.find('team2-gradient')
    teams = teams[start+31:]
    end = teams.find('">')
    matchInfo['Team 2'] = {'Name': teams[0:end].split("/")[1],
                           'ID': teams[0:end].split("/")[0]}
    
    # Best of ?
    start = htmlstr.find('Best of')
    boN = htmlstr[start+8:]
    end = boN.find(" ")
    boN = boN[0:end]
    matchInfo['bo?'] = int(boN)
    
    # Result
    start = htmlstr.find('teamName')
    score = htmlstr[start:]
    start = score.find('</div>')
    score = score[start:]
    start = score.find('<div class="score">')
    score = score[start:]
    start = score.find('spoiler')
    score = score[start+9:]
    end = score.find("<")
    scoreT1 = score[0:end]
    start = score.find('spoiler')
    score = score[start+9:]
    end = score.find("<")
    scoreT2 = score[0:end]
    if matchInfo['bo?'] > 1:
        matchInfo['Team 1 points'] = int(scoreT1)
        matchInfo['Team 2 points'] = int(scoreT2)
    else:
        if scoreT1 == scoreT2:
            matchInfo['Team 1 points'] = 0.5
            matchInfo['Team 2 points'] = 0.5
        elif scoreT1 > scoreT2:
            matchInfo['Team 1 points'] = 1
            matchInfo['Team 2 points'] = 0
        else:
            matchInfo['Team 1 points'] = 0
            matchInfo['Team 2 points'] = 1
    
    print(matchInfo)
    return htmlstr

def getUpcomingMatchInfo(url):
    pass

# matches = hltv.get_matches()
mInfo = getFinishedMatchInfo('https://www.hltv.org/matches/2358424/faze-vs-sprout-iem-road-to-rio-2022-europe-rmr-a')
