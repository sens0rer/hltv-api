import requests
import bs4
from bs4 import BeautifulSoup


def get_basic_team_info(soup: BeautifulSoup) -> dict:
    team_info = {}
    # Team name and country
    team_info['Team name'] = soup.find(
        'h1', class_='profile-team-name text-ellipsis').string
    team_info['Country'] = list(
        soup.find('div', class_='team-country text-ellipsis').stripped_strings)[0]
    # Team logo
    img_tag = soup.find('img',class_="teamlogo",title=team_info.get('Team name',''))
    team_info['Logo'] = img_tag.attrs.get('srcset')
    # Miscelaneous data from the table at the top
    for tag in soup.find_all("div", class_='profile-team-stat'):
        strings = [i for i in tag.stripped_strings]
        key = strings[0]
        value = " ".join(strings[1:])
        team_info[key] = value
    return team_info


def get_team_social_media(soup: BeautifulSoup) -> list:
    social_media = []
    div = soup.find('div', class_='socialMediaButtons')
    for tag in div.children:
        social_media.append(tag.attrs.get('href'))
    return social_media


def get_person_info_from_table(table_tag: bs4.element.Tag) -> dict:
    person_info = {}
    key_list = []
    # Get table column names
    for child in table_tag.thead.find_all("th"):
        strings = [i for i in child.stripped_strings]
        key_list.append(" ".join(strings))
    key_list = key_list[1:]
    # Get tables values for each player
    for player_tag in table_tag.tbody.find_all('tr'):
        value_list = []
        for child in player_tag.find_all('td'):
            if child.attrs.get('class') == ['playersBox-first-cell']:
                img = child.find('img', class_='playerBox-bodyshot')
                img_url = img.attrs.get('src')
                full_name = img.attrs.get('title')
                country_img = child.find(
                    'img', class_='gtSmartphone-only flag')
                country = country_img.attrs.get('title')
                nickname = list(child.stripped_strings)[0]
                person_info[nickname] = {}
                person_info[nickname]['Country'] = country
                person_info[nickname]['Full name'] = full_name
                person_info[nickname]['Player photo'] = img_url
            else:
                strings = [i for i in child.stripped_strings]
                value_list.append(" ".join(strings))
        for i, key in enumerate(key_list):
            person_info[nickname][key] = value_list[i]
    return person_info


def get_team_roster(soup: BeautifulSoup) -> dict:
    roster = {'Coach': {}, 'Players': {}}
    # Coach info
    coach_table = soup.find("table", class_="table-container coach-table")
    roster['Coach'] = get_person_info_from_table(table_tag=coach_table)
    player_table = soup.find("table", class_="table-container players-table")
    roster['Players'] = get_person_info_from_table(table_tag=player_table)
    return roster


def get_team_info(teamid: int | str, teamname: str) -> dict:
    """
    Returns a dictionary of team stats
    """
    team_info = {}
    team_info['Team ID'] = teamid
    page = requests.get(
        f'https://www.hltv.org/team/{teamid}/{teamname.lower()}')
    soup = BeautifulSoup(page.content, 'lxml')
    team_info.update(get_basic_team_info(soup))
    team_info['Social media'] = get_team_social_media(soup)
    team_info['Roster'] = get_team_roster(soup)
    return team_info
