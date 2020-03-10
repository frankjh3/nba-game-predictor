from basketball_stats_scraper.basketball_reference_scraper.bbref_scraper import *
from basketball_stats_scraper.ats_trends_scraper.ats_scraper import *
from nba_statistics_db.update_nba_stats import NBAStatsDB
from todays_games.todays_spreads import *
from util.team_name_conversion import *
import time
import numpy as np


correct = 0
games_num = 0


def score_predict(away_team, home_team, year, fifteen_game_avg = True):
    nba_stats_db = NBAStatsDB()

    """
    update_team_advanced_stats_db(away_team, year, nba_stats_db)
    update_team_advanced_stats_db(home_team, year, nba_stats_db)
    """

    away_stats_avg = nba_stats_db.get_advanced_gamelog_average(away_team, year)
    home_stats_avg = nba_stats_db.get_advanced_gamelog_average(home_team, year)

    away_scores = nba_stats_db.get_game_scores(away_team, year)
    home_scores = nba_stats_db.get_game_scores(home_team, year)

    away_point_sum = point_sum(away_scores, away_stats_avg, home_stats_avg, away_team, nba_stats_db)
    home_point_sum = point_sum(home_scores, home_stats_avg, away_stats_avg, home_team, nba_stats_db)

    points_sum = (away_point_sum + -home_point_sum) / 2

    split = splits(away_team, home_team, year)
    points_sum += split

    return points_sum


def point_sum(scores, stats_avg, opp_stats_avg, team, nba_stats_db):
    coeffs = np.array([0, 0, 0, 0, 0, 0, 0, 0])
    i = 14
    while i < len(stats_avg):
        result = (scores[i][0] - scores[i][1])

        diff = stats_difference(stats_avg[i][2:10], stats_avg[i][1], stats_avg[i][0], nba_stats_db)

        this_coeffs = np.zeros((8,))
        for w in range(len(diff)):
            if diff[w] != 0:
                this_coeffs[w] = result / diff[w]

        j = 0
        while j < len(this_coeffs):
            if this_coeffs[j] < 0:
                this_coeffs[j] = -min(abs(this_coeffs[j]), 100)
            else:
                this_coeffs[j] = min(this_coeffs[j], 100)
            j += 1
        coeffs = this_coeffs + coeffs
        i += 1
    coeffs = coeffs / len(stats_avg)

    team_stats = list(stats_avg[len(stats_avg) - 1][2: 10])
    opp_stats = list(opp_stats_avg[len(opp_stats_avg) - 1][2: 10])

    team_stats[6] = 100.0 - team_stats[6]
    opp_stats[6] = 100.0 - opp_stats[6]
    diff = np.array([team_stats[0] - opp_stats[4], team_stats[1] - opp_stats[5], team_stats[2] - opp_stats[6],
                     team_stats[3] - opp_stats[7], team_stats[4] - opp_stats[0], team_stats[5] - opp_stats[1],
                     team_stats[6] - opp_stats[2], team_stats[7] - opp_stats[3]])

    points = coeffs * diff
    points_sum = sum(points)

    calculate_accuracy(team, coeffs, nba_stats_db)
    return points_sum


def stats_difference(team_stats, opp_id, date, nba_stats_db, fifteen_game_avg = True):
    query = "SELECT efg, tov, orb, ft_per_fga, opp_efg, opp_tov, drb, opp_ft_per_fga FROM advanced_gamelog_average " \
            "WHERE team_id = %s AND 15_game_avg = %s AND date <= CAST(%s AS DATE)"

    away_search = (opp_id, fifteen_game_avg, date)

    team_stats = list(team_stats)

    attempts = 0
    while True:
        try:
            nba_stats_db.cursor.execute(query, away_search)
            opp_stats = nba_stats_db.cursor.fetchall()
            opp_stats = list(opp_stats[len(opp_stats) - 1])
            break
        except TypeError:  # need to update gamelog for missing team
            attempts += 1
            if attempts == 2:
                break
            #print("reached")
            update_team_advanced_stats_db(id_to_team(opp_id), 2019, nba_stats_db)

    # change defensive rebound rate to offensive rebound rate allowed
    team_stats[6] = 100.0 - team_stats[6]
    opp_stats[6] = 100.0 - opp_stats[6]

    team_stats[1] = team_stats[1] / 100.0
    team_stats[2] = team_stats[2] / 100.0
    team_stats[5] = team_stats[5] / 100.0
    team_stats[6] = team_stats[6] / 100.0

    opp_stats[1] = opp_stats[1] / 100.0
    opp_stats[2] = opp_stats[2] / 100.0
    opp_stats[5] = opp_stats[5] / 100.0
    opp_stats[6] = opp_stats[6] / 100.0

    diff = np.array([team_stats[0] - opp_stats[4], team_stats[1] - opp_stats[5], team_stats[2] - opp_stats[6], team_stats[3] - opp_stats[7],
                     team_stats[4] - opp_stats[0], team_stats[5] - opp_stats[1], team_stats[6] - opp_stats[2], team_stats[7] - opp_stats[3]])

    return diff


def update_team_advanced_stats_db(team, year, nba_stats_db):
    gamelog = game_log(team, year=year, advanced_stats=True)
    nba_stats_db.update_advanced_gamelog(gamelog, team)
    nba_stats_db.update_advanced_gamelog_average(team)


def calculate_accuracy(team, coeffs, nba_stats_db):
    global correct
    global games_num
    stats = nba_stats_db.get_advanced_gamelog_average(team, 2019)

    query = "SELECT away FROM advanced_gamelog " \
            "WHERE team_id = %s AND date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)"
    start_date = "{year}-09-01".format(year=2019 - 1)
    end_date = "{year}-07-01".format(year=2019)
    nba_stats_db.cursor.execute(query, (team_to_id(team), start_date, end_date))

    away_or_home = nba_stats_db.cursor.fetchall()

    scores = nba_stats_db.get_game_scores(team, 2019)
    spread_results = ats_results(team)["Line"]

    for i in range(len(spread_results)):
        if spread_results[i] == "(Pick)":
            spread_results[i] = "0"
        elif spread_results[i][0] == '+':
            spread_results[i] = '-' + spread_results[i][1:]
        else:
            spread_results[i] = spread_results[i][1:]

    num_correct = 0
    num_games = len(stats)

    i = 3
    while i <  len(stats):
        result = (scores[i][0] - scores[i][1])
        diff = stats_difference(stats[i-1][2:10], stats[i][1], stats[i-1][0], nba_stats_db)

        points = [x * y for x, y in zip(coeffs, diff)]

        points_sum = sum(points)
        if away_or_home[i] == '':
            points_sum += 3

        if result > float(spread_results[i]):
            covered = True
        elif result < float(spread_results[i]):
            covered = False
        else:
            num_games -= 1
            i += 1
            continue

        if points_sum > float(spread_results[i]) and covered:
            num_correct += 1
        elif points_sum < float(spread_results[i]) and not covered:
            num_correct += 1

        i += 1
    correct += num_correct
    games_num += (num_games - 3)
    print(team + ": " + str(num_correct) + "/" + str(num_games - 3))


games = initialize_games()
for game in games:
    away_team = game.away_team
    home_team = game.home_team

    predicted_score = score_predict(away_team, home_team, 2019)

    spread = game.away_spread
    if spread[0] == '+':
        spread = '-' + spread[1:]
    else:
        spread = spread[1:]

    if predicted_score > float(spread):
        cover = True
    else:
        cover = False

    if cover:
        cover_team = away_team
    else:
        cover_team = home_team
    print(away_team + ": " +  str(predicted_score) + ", " + cover_team + " will cover")
    time.sleep(3)

percent = correct / games_num
print("total: " + str(correct) + "/" + str(games_num - 3) + ", " + str(percent) + "% correct" )


