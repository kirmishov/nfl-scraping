import json
import sys
from collections import namedtuple
from datetime import datetime, timedelta
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup

START_DATE = '2015-09-10'
END_DATE = '2016-10-30'

Game = namedtuple(
    'Game', ['id', 'away', 'away_open', 'away_close', 'away_side_picks',
    'home', 'home_open', 'home_close', 'home_side_picks',
    'total_open', 'total_close','over_picks', 'under_picks',
    'a1', 'a2', 'a3', 'a4', 'aOT', 'a_total_score',
    'v1', 'v2', 'v3', 'v4', 'vOT', 'v_total_score'])


def date_range(start_date, end_date):
    dates = []
    while datetime.strptime(start_date, '%Y-%m-%d') < datetime.strptime(end_date, '%Y-%m-%d'):
        dates.append(start_date)
        start_date = datetime.strftime(datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=7), '%Y-%m-%d')
    if len(dates)==0:
        print ('Not correct date_range')
        sys.exit()
    return dates

def games_info_from_page(date_str):
    r = requests.get('https://www.covers.com/Sports/NFL/Matchups?selectedDate={}'.format(date_str), timeout=30)
    if r.status_code!=200:
        return None
    print('Date checking: {}'.format(date_str))
    soup = BeautifulSoup(r.text, 'html.parser')
    games_info = []
    for game_cont in soup.find_all('div', {'class': 'cmg_game_container cmg_matchup_game cmg_postgame'}):
        # print (game_cont)
        id = game_cont.find('div', {'class': 'cmg_game_data cmg_matchup_game_box'})['data-event-id']
        away = game_cont.find('div', {'class': 'cmg_game_data cmg_matchup_game_box'})['data-away-team-shortname-search']
        home = game_cont.find('div', {'class': 'cmg_game_data cmg_matchup_game_box'})['data-home-team-shortname-search']
        link = game_cont.find('a', href=True, text='Consensus')['href']

        table_scores = game_cont.find('tbody').find_all('tr')
        a_scores = [int(elem.text.strip()) for elem in table_scores[0].find_all('td') if not any(c.isalpha() for c in elem.text.strip()) and len(elem.text.strip())!=0]
        v_scores = [int(elem.text.strip()) for elem in table_scores[1].find_all('td') if not any(c.isalpha() for c in elem.text.strip()) and len(elem.text.strip())!=0]
        for ar in [a_scores, v_scores]:
            if len(ar) == 5:
                ar.insert(4, 0)
        # print (a_scores, v_scores)
        games_info.append((id, away, home, link, a_scores, v_scores))
    return games_info


def game_data_from_page(game):
    sleep(randint(2,5))
    r = requests.get(game[3], timeout=30)
    if r.status_code!=200:
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    consensus_content = soup.find('div', {'id': 'consensus_analysis_content'})
    away_picks = consensus_content.find_all('div', {'class': 'covers-CoversConsensusDetailsTable-awayLine'})
    home_picks = consensus_content.findAll('div', {'class': 'covers-CoversConsensusDetailsTable-homeLine'})
    away_totals = soup.find_all('div', {'class': 'covers-CoversConsensusDetailsTable-finalWagersleft'})
    home_totals = soup.find_all('div', {'class': 'covers-CoversConsensusDetailsTable-finalWagersRight'})

    totals_str = soup.find_all('div', {'class': 'covers-CoversConsensusDetailsTable-sideHeadMiddle'})
    totals = [float(elem.text) for elem in totals_str if not any(c.isalpha() for c in elem.text)]
    # print (totals)

    away_open = float(away_picks[0].text)
    away_close = float(away_picks[-1].text)
    home_open = float(home_picks[0].text)
    home_close = float(home_picks[-1].text)
    away_side_picks = int(away_totals[0].text)
    home_side_picks = int(home_totals[0].text)
    over_picks = int(away_totals[1].text)
    under_picks = int(home_totals[1].text)
    total_open = float(totals[0])
    total_close = float(totals[-1])

    game_obj = Game(
        game[0], game[1], away_open, away_close, away_side_picks,
        game[2], home_open, home_close, home_side_picks,
        total_open, total_close, over_picks, under_picks,
        game[4][0], game[4][1], game[4][2], game[4][3], game[4][4], game[4][5],
        game[5][0], game[5][1], game[5][2], game[5][3], game[5][4], game[5][5])
    
    # print (json.dumps(game_obj._asdict()))

    with open('data/game{}.json'.format(game_obj.id), 'w') as f:
        f.write(json.dumps(game_obj._asdict()))
    print('Game ID parsed: {}'.format(game_obj.id),end="\r")


if __name__ == "__main__":
    for date_str in date_range(START_DATE, END_DATE):
        games_info = games_info_from_page(date_str)
        if games_info:
            for game in games_info:
                if game:
                    game_data_from_page(game)
