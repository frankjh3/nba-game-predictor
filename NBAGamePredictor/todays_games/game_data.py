from util.team_name_conversion import team_to_abr


class GameData:
    def __init__(self, away_team, home_team, spread, time, date):
        self.away_team = away_team
        self.home_team = home_team
        self.away_spread = spread
        self.home_spread = self.home_spread()
        self.time = self.correct_timezone(time)
        self.away_score = 0
        self.home_score = 0
        self.date = date
        self.id = "{away}-{home}-{date}".format(
                away=team_to_abr(away_team), home=team_to_abr(home_team), date=date)
        self.prediction = ""

    def correct_timezone(self, time):
        if time != "":
            times = time.split(":")
            hour = int(times[0])
            if hour == 1:
                return "12" + ":" + str(times[1])
            else:
                hour = hour - 1
                return str(hour) + ":" + str(times[1])
        else:
            return ""

    def home_spread(self):
        spread_string = ""
        try:
            spread = list(self.away_spread)
            if spread[0] == "+":
                spread[0] = '-'
            elif spread[0] == "-":
                spread[0] = '+'
            for letter in spread:
                spread_string += letter
        except IndexError:
            spread_string = ""
        return spread_string


