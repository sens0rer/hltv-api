import hltvapi as hltv
import datetime
from lxml import html
import requests


def getTeamInfo(teamid, teamname):
    """
    Returns a dictionary of basic team stats
    """
    teamInfo = {}
    teamInfo['Team ID'] = teamid
    teamInfo['Team name'] = teamname.lower()
    page = requests.get('https://www.hltv.org/team/' +
                        str(teamid) + '/' + teamname.lower())
    htmlstr = page.text

    # extract World ranking
    start = htmlstr.find(
        '<div class="profile-team-stat"><b>World ranking</b>')
    ranking = htmlstr[start:]
    start = ranking.find('#')
    end = ranking.find('</a>')
    ranking = int(ranking[start+1:end])
    teamInfo['World ranking'] = ranking

    # Extract amount of weeks in top30 for core
    start = htmlstr.find(
        '<div class="profile-team-stat"><b>Weeks in top30 for core</b>')
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
    page = requests.get('https://www.hltv.org/player/' +
                        str(playerid) + '/' + nickname.lower())
    htmlstr = page.text

    playerInfo['Rating 2.0'] = float(
        _extractPlayerStats(htmlstr, 'Rating 2.0'))
    playerInfo['Kills per round'] = float(
        _extractPlayerStats(htmlstr, 'Kills per round'))
    playerInfo['Headshots'] = float(
        _extractPlayerStats(htmlstr, 'Headshots')[0:-1])/100
    playerInfo['Maps played'] = int(
        _extractPlayerStats(htmlstr, 'Maps played'))
    playerInfo['Deaths per round'] = float(
        _extractPlayerStats(htmlstr, 'Deaths per round'))
    playerInfo['Rounds contributed'] = float(
        _extractPlayerStats(htmlstr, 'Rounds contributed')[0:-1])/100

    return playerInfo


def _getDetailedGameStats(mapurl):
    """
    Returns detailed stats about a game played
    mapurl - string(example: https://www.hltv.org/stats/matches/mapstatsid/144917/sprout-vs-faze)
    """
    stats = {}
    page = requests.get(mapurl)
    htmlstr = page.text

    # Map name
    start = htmlstr.find('<span class="bold">Map</span>')
    mapPlayed = htmlstr[start+36:]
    end = mapPlayed.find("\n")
    mapPlayed = mapPlayed[0:end]
    stats['Map'] = mapPlayed

    # Team scores, rounds won
    start = htmlstr.find('team-left')
    score1 = htmlstr[start:]
    end = score1.find("</div>")
    score1 = score1[0:end]
    start = score1.find('won')
    if start != -1:
        stats['Team 1 score'] = 1
        stats['Team 2 score'] = 0
        score1 = score1[start+5:]
        stats['Team 1 rounds won'] = int(score1)

        start = htmlstr.find('team-right')
        score2 = htmlstr[start:]
        end = score2.find("</div>")
        score2 = score2[0:end]
        start = score2.find('lost')
        score2 = score2[start+6:]
        stats['Team 2 rounds won'] = int(score2)

    else:
        stats['Team 1 score'] = 0
        stats['Team 2 score'] = 1
        start = score1.find('lost')
        score1 = score1[start+6:]
        stats['Team 1 rounds won'] = int(score1)

        start = htmlstr.find('team-right')
        score2 = htmlstr[start:]
        end = score2.find("</div>")
        score2 = score2[0:end]
        start = score2.find('won')
        score2 = score2[start+5:]
        stats['Team 2 rounds won'] = int(score2)

    # Starting team
    roundsWon = []
    start = htmlstr.find('match-info-row')
    halvesInfo = htmlstr[start:]
    end = halvesInfo.find("Breakdown")
    halvesInfo = halvesInfo[0:end]
    ct = halvesInfo.find('"ct-color"')
    t = halvesInfo.find('"t-color"')
    if ct < t:
        stats['Team 1 starting team'] = 'CT'
        stats['Team 2 starting team'] = 'T'
    else:
        stats['Team 1 starting team'] = 'T'
        stats['Team 2 starting team'] = 'CT'

    # Rounds won by team
    halvesInfo = halvesInfo.split("<")
    count = 0
    for string in halvesInfo:
        if string.split(">")[-1].isdigit():
            if count > 1:
                roundsWon.append(int(string.split(">")[-1]))
            count += 1
            continue
        if count > 5:
            start = string.find(")")
            string = string[start+1:]
            if not string:
                break
            start = string.find("(")
            end = string.find(":")
            roundsWon.append(int(string[start+2:end]))
            start = string.find(":")
            end = string.find(")")
            roundsWon.append(int(string[start+2:end]))
            break
    stats['Half results'] = []
    for i in range(int(len(roundsWon)/2)):
        stats['Half results'].append(
            (roundsWon[2 * i], roundsWon[2 * i + 1]))

    # Extracting info from 'Both sides' table
    start = htmlstr.find('stats-table totalstats')
    end = htmlstr.find("</tbody>")
    table1 = htmlstr[start:end]
    table2 = htmlstr[end+1:]
    start = table2.find('stats-table totalstats')
    table2 = table2[start:]
    end = table2.find("</tbody>")
    table2 = table2[0:end]

    team1 = {}
    terminator = table1.find('st-player')
    while terminator + 1:

        table1 = table1[terminator+20:]
        start = table1.find('players/')
        end = table1.find('" data-tooltip-id')
        player = table1[start+8:end].split('/')
        player = int(player[0]), player[1]
        start = table1.find('kills"')
        table1 = table1[start+7:]
        end = table1.find('<')
        team1[player] = {}
        team1[player]['Kills'] = int(table1[0:end])

        start = table1.find('(')
        table1 = table1[start+1:]
        end = table1.find(')')
        team1[player]['Headshots'] = int(table1[0:end])

        start = table1.find('assists">')
        table1 = table1[start+9:]
        end = table1.find('<')
        team1[player]['Assists'] = int(table1[0:end])

        start = table1.find('deaths">')
        table1 = table1[start+8:]
        end = table1.find('<')
        team1[player]['Deaths'] = int(table1[0:end])

        start = table1.find('kdratio">')
        table1 = table1[start+9:]
        end = table1.find('%')
        team1[player]['KAST'] = float(table1[0:end])

        start = table1.find('adr">')
        table1 = table1[start+5:]
        end = table1.find('<')
        team1[player]['ADR'] = float(table1[0:end])

        start = table1.find('fkdiff')
        table1 = table1[start+6:]
        start = table1.find('">')
        table1 = table1[start+2:]
        end = table1.find('<')
        team1[player]['FK Diff'] = int(table1[0:end])

        start = table1.find('rating')
        table1 = table1[start+6:]
        start = table1.find('">')
        table1 = table1[start+2:]
        end = table1.find('<')
        team1[player]['Rating 2.0'] = float(table1[0:end])

        terminator = table1.find('st-player')

    stats['Team 1 overall match stats'] = team1

    team2 = {}
    terminator = table2.find('st-player')
    while terminator + 1:

        table2 = table2[terminator+20:]
        start = table2.find('players/')
        end = table2.find('" data-tooltip-id')
        player = table2[start+8:end].split('/')
        player = int(player[0]), player[1]
        start = table2.find('kills"')
        table2 = table2[start+7:]
        end = table2.find('<')
        team2[player] = {}
        team2[player]['Kills'] = int(table2[0:end])

        start = table2.find('(')
        table2 = table2[start+1:]
        end = table2.find(')')
        team2[player]['Headshots'] = int(table2[0:end])

        start = table2.find('assists">')
        table2 = table2[start+9:]
        end = table2.find('<')
        team2[player]['Assists'] = int(table2[0:end])

        start = table2.find('deaths">')
        table2 = table2[start+8:]
        end = table2.find('<')
        team2[player]['Deaths'] = int(table2[0:end])

        start = table2.find('kdratio">')
        table2 = table2[start+9:]
        end = table2.find('%')
        team2[player]['KAST'] = float(table2[0:end])

        start = table2.find('adr">')
        table2 = table2[start+5:]
        end = table2.find('<')
        team2[player]['ADR'] = float(table2[0:end])

        start = table2.find('fkdiff')
        table2 = table2[start+6:]
        start = table2.find('">')
        table2 = table2[start+2:]
        end = table2.find('<')
        team2[player]['FK Diff'] = int(table2[0:end])

        start = table2.find('rating')
        table2 = table2[start+6:]
        start = table2.find('">')
        table2 = table2[start+2:]
        end = table2.find('<')
        team2[player]['Rating 2.0'] = float(table2[0:end])

        terminator = table2.find('st-player')

    stats['Team 2 overall match stats'] = team2

    return stats


def getFinishedMatchInfo(url):
    """
    Returns a dictionary of basic match stats
    """
    matchInfo = {}
    matchInfo['URL'] = url
    matchInfo['ID'] = url.split("/")[4]
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

    # Detailed stat url
    start = htmlstr.find('small-padding stats-detailed-stats')
    detailedStats = htmlstr[start:]
    start = detailedStats.find('href')
    detailedStats = detailedStats[start+6:]
    end = detailedStats.find('"')
    detailedStats = detailedStats[0:end]
    matchInfo['Detailed stats'] = "https://www.hltv.org" + detailedStats

    # Urls to stats of every map
    matchInfo['Single map stat URLs'] = []
    if matchInfo['bo?'] > 1:
        page2 = requests.get(matchInfo['Detailed stats'])
        htmlstr2 = page2.text
        for i in range(matchInfo['bo?']):
            start = htmlstr2.find('class="stats-match-map-winner-logo"')
            htmlstr2 = htmlstr2[start:]
            start = htmlstr2.find('href')
            htmlstr2 = htmlstr2[start+6:]
            end = htmlstr2.find('"')
            matchInfo['Single map stat URLs'].append(
                "https://www.hltv.org" + htmlstr2[0:end])
    else:
        matchInfo['Single map stat URLs'] = [
            matchInfo['Detailed stats']]

    mapstats = []
    for i, url in enumerate(matchInfo['Single map stat URLs']):
        mapstats.append(_getDetailedGameStats(url))
    matchInfo['Single map stats'] = mapstats

    matchInfo['Team 1 players'] = [
        x for x in matchInfo['Single map stats'][0]['Team 1 overall match stats'].keys()]
    matchInfo['Team 2 players'] = [
        x for x in matchInfo['Single map stats'][0]['Team 2 overall match stats'].keys()]

    return matchInfo


def getUpcomingMatchInfo(url):
    pass


# matches = hltv.get_matches()
mInfo = getFinishedMatchInfo(
    'https://www.hltv.org/matches/2358424/faze-vs-sprout-iem-road-to-rio-2022-europe-rmr-a')
# mInfo = _getDetailedGameStats(
#     'https://www.hltv.org/stats/matches/mapstatsid/144922/faze-vs-sprout')
