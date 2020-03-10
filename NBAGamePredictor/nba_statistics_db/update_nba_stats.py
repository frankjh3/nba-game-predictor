from util.team_name_conversion import *
import numpy as np
import operator
import mysql.connector
import os

class NBAStatsDB:
    """
    Access MySQL Database for NBA gamelogs, team stats, and averaged gamelog statistics
    """
    def __init__(self):
        self.mydb = mysql.connector.connect(

            host=os.environ['NBA_DB_HOST'],
            user=os.environ['NBA_DB_USER'],
            password=os.environ['NBA_DB_PW'],
            database=os.environ['NBA_DB'],
            auth_plugin="mysql_native_password"
        )

        # Cursor to be used to complete all queries
        self.cursor = self.mydb.cursor()

    def update_advanced_team_stats(self, data_frame):
        """
        Updates the advanced team stats to the current values on basketball-reference.com
        :param data_frame: the advanced statistics of all NBA teams
        """

        data_frame = data_frame.filter(["eFG%", "TOV%", "ORB%", "FT/FGA", "O-eFG%", "O-TOV%", "DRB%", "O-FT/FGA"])

        data_list = self.list_of_tuples_teams(data_frame, year=2019, end_of_list=True)

        query = "UPDATE advanced_team_stats SET " \
                "efg =%s, tov =%s, orb =%s, ft_per_fga =%s, opp_efg =%s, opp_tov =%s, drb =%s, opp_ft_per_fga=%s" \
                "WHERE team_id =%s AND year =%s"

        self.cursor.executemany(query, data_list)
        self.mydb.commit()

    def update_advanced_gamelog(self, data_frame, team_name):
        """
        Add new values into advanced gamelog table.
        If repeat values are attempted to be entered, they are ignored and only new values are entered
        :param data_frame: a team's advanced gamelog
        :param team_name: the name of the team who is having their gamelog updated
        """
        data_list = self.list_of_tuples_gamelog(data_frame, team_name)

        query = "INSERT IGNORE INTO advanced_gamelog " \
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        self.cursor.executemany(query, data_list)
        self.mydb.commit()

    def update_advanced_gamelog_average(self, team_name, year):
        """
        Updates both the season long averages and the averages for the past 15 games for each game in the season
        :param team_name: team name to update the advanced gamelog averages of
        """

        team_id = team_to_id(team_name)
        query = "SELECT date, opp_team_id, efg, tov, orb, ft_per_fga, opp_efg, opp_tov, " \
                "drb, opp_ft_per_fga FROM advanced_gamelog " \
                "WHERE team_id=%s AND date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE);"
        start_date = "{year}-09-01".format(year=year - 1)
        end_date = "{year}-07-01".format(year=year)
        search = tuple([team_id, start_date, end_date])

        self.cursor.execute(query, search)
        stats = self.cursor.fetchall()

        # season long averages for every point in the season
        average_values = np.zeros((len(stats), len(stats[0])-2))

        average_stats = [None] *len(stats)

        index = 0
        while index < len(stats):
            current_row = list(stats[index])
            average_values[index] = (current_row[2:] + (average_values[max(index-1, 0)]*index)) / (index + 1)

            keys = [team_id, False, stats[index][0], stats[index][1]]
            keys.extend(average_values[index])
            average_stats[index] = tuple(keys)

            index += 1

        query = "INSERT IGNORE INTO advanced_gamelog_average VALUES" \
                "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        # add season long stat averages (duplicates are ignored)
        self.cursor.executemany(query, average_stats)

        # Average for past 15 games for every point in the season
        # For first 14 games, uses less than 15 games to find average
        average_15_stats = [None] * len(stats)
        average_values_15 = np.zeros((len(stats), len(stats[0]) - 2))

        index = 0
        while index < len(stats):
            current_row = list(stats[index])

            if index > 14:
                values_to_drop = stats[index - 15]
                diff = list(map(operator.sub, current_row[2:], values_to_drop[2: ]))
            else:
                diff = current_row[2: ]
            average_values_15[index] = (diff + (average_values_15[max(index-1, 0)] * min(index, 15))) / (min(index + 1,15))

            keys = [team_id, True, stats[index][0], stats[index][1]]
            keys.extend(average_values_15[index])
            average_15_stats[index] = tuple(keys)

            index += 1

        query = "INSERT IGNORE INTO advanced_gamelog_average VALUES" \
                "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        self.cursor.executemany(query, average_15_stats)
        self.mydb.commit()

    def get_advanced_gamelog_average(self, team, year, fifteen_game_avg = True):
        """
        Returns the advanced gamelog averages for a particular team in a year. Returns either
        season long averages or 15 game averages
        :param team: team to find gamelog averages of
        :param year: year of gamelog (year is the last year in a season: for 2018-2019 season, year=2019)
        :param fifteen_game_avg: True if 15 game averages, false if season long averages
        :return: list of tuples of the advanced gamelog averages
        """
        query = "SELECT date, opp_team_id, efg, tov, orb, ft_per_fga, opp_efg, " \
                "opp_tov, drb, opp_ft_per_fga FROM advanced_gamelog_average " \
                "WHERE team_id = %s AND 15_game_avg = %s " \
                "AND date BETWEEN CAST(%s AS DATE) " \
                "AND CAST(%s AS DATE);"

        start_date = "{year}-09-01".format(year=year-1)
        end_date = "{year}-07-01".format(year=year)
        search = (team_to_id(team), fifteen_game_avg, start_date, end_date)

        self.cursor.execute(query, search)
        return self.cursor.fetchall()

    def get_advanced_gamelog_average_game(self, team, date, fifteen_game_avg = True):
        """
        Return the advanced gamelog averages for an individual game.
        :param team: team to get gamelog of
        :param date: date of the game
        :param fifteen_game_avg: True if 15 game averages, false if season long averages
        :return: the average stats of a team at a particular date (game) in a season
        """
        query = "SELECT date, opp_team_id, efg, tov, orb, ft_per_fga, opp_efg, opp_tov, " \
                "drb, opp_ft_per_fga FROM advanced_gamelog_average " \
                "WHERE team_id = %s AND 15_game_avg = %s AND date = CAST(%s AS DATE)"

        search = (team_to_id(team), fifteen_game_avg, date)

        self.cursor.execute(query, search)
        return self.cursor.fetchall()

    def get_game_scores(self, team, year):
        """
        Return the score of a team for the entire season - year
        :param team: team to get scores for
        :param year: year of scores (year is the last year in a season: for 2018-2019 season, year=2019)
        :return: list of tuples of the team and opponent's scores in a given year
        """
        query = "SELECT team_score, opp_score FROM advanced_gamelog " \
                "WHERE team_id = %s AND date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)"

        start_date = "{year}-09-01".format(year=year-1)
        end_date = "{year}-07-01".format(year=year)

        search = (team_to_id(team), start_date, end_date)

        self.cursor.execute(query, search)
        return self.cursor.fetchall()

    def list_of_tuples_teams(self, data_frame, year=None, exclude_id=False, end_of_list=False, include_index_first=False):
        """
        Utility method used to convert a DataFrame into a list of tuples, so they can be inserted into the mySQL database
        :param data_frame: DataFrame to convert to a list of tuples
        :param year: whether to include year, if None, year is not included
        :param exclude_id: whether to exclude the team_id
        :param end_of_list: whether to insert year or team_id to end or beginning of tuple. By default, inserts at beginning
        :param include_index_first: whether to include the index labels of the DataFrame as the first element of each tuple
        :return:
        """
        records = []
        i = 0
        while i < len(data_frame.index):
            record = data_frame.iloc[i].tolist()

            # Inserts team_id to beginning or end of list
            if not exclude_id and not end_of_list:
                record.insert(0, team_to_id(data_frame.index.values[i]))
            elif not exclude_id and end_of_list:
                record.append(team_to_id(data_frame.index.values[i]))

            # Inserts year to beginning or end of list (after team_id)
            if year is not None and not end_of_list:
                record.insert(1, year)
            elif year is not None and end_of_list:
                record.append(year)

            # Inserts index labels of DataFrame to tuples
            if include_index_first:
                record.insert(1, data_frame.index.values[i])

            records.append(tuple(record))
            i += 1
        return records

    def list_of_tuples_gamelog(self, data_frame, team_name):
        """
        Utility method used to convert a gamelog into a list of tuples, for insertion into mySQL DB
        :param data_frame: gamelog as a DataFrame
        :param team_name: name of the team who's gamelog is being inserted
        :return: gamelog in the form of a list of tuples
        """
        records = []
        i = 0

        team_id = team_to_id(team_name)
        while i < len(data_frame.index):
            record = data_frame.iloc[i].tolist()

            record.insert(0, team_id)
            record.insert(1, data_frame.index.values[i])

            # Convert opponent name to their team_id
            record[4] = team_to_id(record[4])

            records.append(tuple(record))
            i += 1
        return records


nba_stats_db = NBAStatsDB()
