import requests
import argparse
import datetime

# constants
GAME_ENDPOINT = 'https://statsapi.web.nhl.com/api/v1/game/{id}/feed/live'

def get_game(season, game_num):
    game_id = '{year}02{num:04d}'.format(year=season, num=game_num)
    return requests.get(GAME_ENDPOINT.format(id=game_id))
     

if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser(description='Calculates the "effective points" of all NHL players since a given season')
    parser.add_argument('season', type=int, help='The season to calculate points from. e.g. 2010 would calculate effective points starting with the 2010-2011 season onwards')
    parser.add_argument('--verbose', help='Verbose', default=False, action='store_true')
    args = parser.parse_args()

    # vars
    effective_points_map = {} # dict mapping player_id -> effective_points_map

    # use time to determine end season
    today = datetime.date.today()
    end_season = today.year + 1 if today.month >= 9 else today.year

    # each season
    for current_year in range(args.season, end_season):
        if args.verbose:
            print(current_year)

        # see https://github.com/dword4/nhlapi#game-ids
        max_games = 1230 if current_year < 2017 else 1271

        # each game
        for current_game in range(1, max_games + 1):
            response = get_game(current_year, current_game)
            if response.status_code != 200:
                print(response.status_code)
                print(response.request.path_url)
                print(response.text)
                exit(1)
            
            data = response.json()
            if data['gameData']['status']['abstractGameState'] != 'Final': # game in progress/in the future
                continue
            
            winner = ''
            winner_id = -1
            effective_goals = 0
            home_goals = data['liveData']['boxscore']['teams']['home']['teamStats']['teamSkaterStats']['goals']
            away_goals = data['liveData']['boxscore']['teams']['away']['teamStats']['teamSkaterStats']['goals']

            if len(data['liveData']['linescore']['periods']) > 3: 
                effective_goals = home_goals + away_goals # OT/Shootout - all goals are effective
            elif home_goals > away_goals:
                winner = 'home'
                winner_id = data['liveData']['boxscore']['teams']['home']['team']['id']
                effective_goals = away_goals + 1 # effective goals is equal to the losing team's goals + 1
            else:
                winner = 'away'
                winner_id = data['liveData']['boxscore']['teams']['away']['team']['id']
                effective_goals = home_goals + 1 # effective goals is equal to the losing team's goals + 1

            if args.verbose:
                print('\t{:04d}: {}-{} {}'.format(current_game, home_goals, away_goals, 'OT/SO' if winner == '' else winner))

            scoring_plays = data['liveData']['plays']['scoringPlays']
            for idx in scoring_plays:
                # skip if not a goal or is a goal from the losing team (excluding OT/Shootout)
                goal_data = data['liveData']['plays']['allPlays'][idx]
                if effective_goals == 0 or goal_data['result']['event'] != 'Goal' or (winner_id != -1 and goal_data['team']['id'] != winner_id):
                    continue

                # here, we have come across an effective goal - assign points to involved players
                effective_goals -= 1
                for player in goal_data['players']:
                    if player['playerType'] == 'Scorer' or player['playerType'] == 'Assist':
                        id = player['player']['id']
                        effective_points_map[id] = effective_points_map[id] + 1 if id in effective_points_map else 1

            # sanity check - make sure points were only given to effective goals
            assert effective_goals == 0
    
    # done going through all seasons
    print('Done')
    print(effective_points_map)



