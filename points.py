import requests
import argparse
import datetime

# constants
GAME_ENDPOINT = 'https://statsapi.web.nhl.com/api/v1/game/{id}/feed/live'

def get_game(season, game_num):
    game_id = '{year}02{:0<num}'.format(year=season, num=game_num)
    return requests.get(GAME_ENDPOINT.format(game_id))
     

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser(description='Calculates the "effective points" of all NHL players since a given season')
    parser.add_argument('season', type=int, help='The season to calculate points from. e.g. 2010 would calculate effective points starting with the 2010-2011 season onwards')
    args = parser.parse_args()

    # vars
    effective_points = {} # dict mapping player_id -> effective_points

    # each season
    for current_year in range(args.season, datetime.date.today().year + 1):
        # see https://github.com/dword4/nhlapi#game-ids
        max_games = 1230 if current_year < 2017 else 1271

        # each game
        for current_game in range(1, max_games + 1):
            response = get_game(current_year, current_game)
            if response.status_code != 200:
                print('temp for now')
                print(response.status_code)
                print(response.text)
                print(effective_points)
                exit(1)

            data = response.json()

            # game in progress/in the future
            if data['gameData']['status']['abstractGameState'] != 'Final':
                continue
            
            winner = ''
            effective_goals = 0
            home_goals = data['liveData']['boxscore']['teams']['home']['teamStats']['teamSkaterStats']['goals']
            away_goals = data['liveData']['boxscore']['teams']['away']['teamStats']['teamSkaterStats']['goals']

            if len(data['liveData']['linescore']['periods']) > 3: # OT/Shootout - all goals are effective
                effective_goals = home_goals + away_goals
            elif home_goals > away_goals:
                winner = 'home'
                effective_goals = away_goals + 1
            else:
                winner = 'away'
                effective_goals = home_goals + 1

            scoring_plays = data['liveData']['plays']['scoringPlays']
            for idx in scoring_plays:
                goal_data = data['liveData']['plays']['allPlays'][idx]
                if goal_data['result']['event'] != 'Goal' or goal_data['about']['goals'][winner] == 0:
                    continue
                # here, we have come across an effective goal - assign points to involved players
                for player in goal_data['players']:
                    pass






