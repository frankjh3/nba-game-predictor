from basketball_stats_scraper.basketball_reference_scraper.bbref_scraper import *
from basketball_stats_scraper.ats_trends_scraper.ats_scraper import *
from nba_statistics_db.update_nba_stats import NBAStatsDB
from util.team_name_conversion import *
import numpy as np
from sklearn import svm


class CoverPredict:
    def __init__(self, away_team, home_team, year):
        self.away_team = id_to_team(away_team)
        print(self.away_team)
        self.home_team = home_team
        self.year = year
        self.nba_stats_db = NBAStatsDB()

        """
        self.update_team_advanced_stats_db(self.away_team)
        self.update_team_advanced_stats_db(home_team)
        """

        self.away_stats_avg = self.nba_stats_db.get_advanced_gamelog_average(id_to_team(away_team), year)
        self.home_stats_avg = self.nba_stats_db.get_advanced_gamelog_average(home_team, year)

    def predict_game(self):
        away_results = self.cover_result(self.away_team)[:len(self.away_stats_avg)]
        away_results = away_results.astype('int')
        home_results = self.cover_result(self.home_team)

        results = np.concatenate((away_results, home_results))
        results = results.astype('int')

        away_games = self.game_team_stats(True)
        home_games = self.game_team_stats(False)

        # Add spreads

        away_spreads = past_spreads(self.away_team)[:len(self.away_stats_avg)]
        max = abs(away_spreads[0])
        for i in range(len(away_spreads)):
            if abs(away_spreads[i]) > max:
                max = abs(away_spreads[i])
        away_spreads = np.divide(away_spreads, max)

        # kernel='rbf', gamma=0.0000001, C=1000000000
        clf = svm.SVC(gamma=0.0000001, C=1000000000000)

        clf.fit(away_games[1:-10], away_results[1:-10])

        num_correct = 0
        i = len(away_games) - 10
        while i < len(away_games):
            print('Prediction:', clf.predict(away_games)[i])
            if clf.predict(away_games)[i] == away_results[i]:
                num_correct += 1
            i += 1
        print(num_correct)
        return num_correct

    def game_team_stats(self, away):
        query = "SELECT efg, tov, orb, ft_per_fga, opp_efg, opp_tov, drb, opp_ft_per_fga FROM advanced_gamelog_average " \
                "WHERE team_id = %s AND 15_game_avg = %s AND date = CAST(%s AS DATE)"

        # include the team stats plus the opposing team's stats in each row of the array for every game in the season

        if away:
            stats_avg = self.away_stats_avg
        else:
            stats_avg = self.home_stats_avg

        opp_stats = [None] * len(stats_avg)

        i = 0
        for game in stats_avg:
            opp_search = (game[1], True, game[0])
            while True:
                try:
                    self.nba_stats_db.cursor.execute(query, opp_search)
                    opp_stats[i] = self.nba_stats_db.cursor.fetchall()[0]
                except IndexError:
                    self.update_team_advanced_stats_db(id_to_team(game[1]))
                else:
                    break

            i += 1

        opp_stats = np.array(opp_stats)

        for row in opp_stats:
            row[6] = 100 - row[6]

        for i in range(len(opp_stats)):
            temp = np.copy(opp_stats[i][ :4])
            opp_stats[i][: 4] = opp_stats[i][4:]
            opp_stats[i][4:] = temp

        game_team_stats = np.zeros((len(stats_avg), 8))
        for i in range(len(stats_avg)):
            game_team_stats[i] = np.subtract(stats_avg[i][2:10], opp_stats[i])

        return game_team_stats

    def cover_result(self,team):
        scores = self.nba_stats_db.get_game_scores(team, 2019)
        spread_results = ats_results(team)["Line"]

        for i in range(len(scores)):
            if spread_results[i] == "(Pick)":
                spread_results[i] = "0"
            elif spread_results[i][0] == '+':
                spread_results[i] = '-' + spread_results[i][1:]
            else:
                spread_results[i] = spread_results[i][1:]

        for i in range(len(scores)):
            result = (scores[i][0] - scores[i][1])
            if result >= float(spread_results[i]):
                spread_results[i] = 1
            elif result < float(spread_results[i]):
                spread_results[i] = 0
        return np.array(spread_results)

    def update_team_advanced_stats_db(self,team):
        print("reached")
        gamelog = game_log(team, year=self.year, advanced_stats=True)
        self.nba_stats_db.update_advanced_gamelog(gamelog, team)
        self.nba_stats_db.update_advanced_gamelog_average(team, self.year)


i = 1
total = 0
while i <= 30:
    cp = CoverPredict(i, "Milwaukee", 2019)
    total += cp.predict_game()
    i += 1

print(total)
