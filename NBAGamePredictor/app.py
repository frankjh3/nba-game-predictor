import math
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from jinja2 import Template
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from todays_games.todays_spreads import initialize_games
from todays_games.update_live_scores import update_scores
from util.team_name_conversion import team_to_abr


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost::5432/nba_stats'


def refresh_scores():
    update_scores(games)


@app.route('/')
def home():
    return render_template('index.html', games=games)


@app.route('/game/<game_id>', methods=['GET'])
def render_game(game_id):
    return render_template('game.html', game=game_dict[game_id])


if __name__ == '__main__':
    games = initialize_games()
    update_scores(games)
    # used to retrieve game data in /game/<game_id>
    game_dict = {}
    for game in games:
        game_dict.update(
            {game.id: game}
        )

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=refresh_scores, trigger="interval", seconds=30)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=True)
