import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import datetime
import numpy as np


def get_page_soup(url):
    response = requests.get(url)
    page = response.content
    soup = BeautifulSoup(page, features="lxml")
    return soup


def remove_comment(table):
    for element in table.children:
        if isinstance(element, Comment):  # remove comment, results in table
            comment = str(element.string).strip()
            table = BeautifulSoup(comment, features= "lxml")
    return table


def change_opponent_header(table):
    table_headers = table.find_all("th", {"scope": "col"})

    del table_headers[0]  # This is the "rank" - not assigned a column in table_body
    for i in range(len(table_headers)):
        table_headers[i] = table_headers[i].get_text()
        # Checks if the stat name appeared earlier in the table, adds O- to the second occurence to signify it is for
        # opponent. This occurs when a team and opponent's stats are in same table with same name
        for j in range(i):
            if table_headers[j] == table_headers[i]:
                table_headers[i] = "O-" + table_headers[i]
    return table_headers


def remove_mid_headers(data_frame, rows, append_to_front=None):
    """
    append_to_front is an additional list to append an item from before each row in rows
    """
    amount_increased = 0  # Keeps track of how many rows have been deleted from data_frame
    i = 0
    while i < len(rows):
        if append_to_front:
            cells = [append_to_front[i - amount_increased].get_text()] + rows[i].find_all("td")
            for j in range(1, len(cells)):
                cells[j] = cells[j].get_text()
        else:
            cells = rows[i].find_all("td")
            for j in range(len(cells)):
                cells[j] = cells[j].get_text()

        try:
            data_frame.loc[i - amount_increased] = cells
        except ValueError:  # Occurs when header is in middle of table - ignores header and does not add to data_frame
            amount_increased += 1
            data_frame.drop(data_frame.index[len(data_frame) - 1], inplace=True)  # Must delete a row from data_frame
        i += 1
    return data_frame


def bbref_table(table_id, url=None, include_game_link=False):
    """
    Accesses Basketball-Reference.com to get a table from the specified url and tableId

    :param table_id: html id of the table
    :param url: url of page with table
    :param include_game_link: set to True to receive url of game for each game in box score (only valid for gamelog)
    :return: whole table found on Basketball-Reference in the form of a DataFrame
    """
    soup = get_page_soup(url)
    table = soup.find("div", {"id": table_id})

    # If the data is stored in a comment, must get data inside of it by finding comment
    table = remove_comment(table)

    table_headers = change_opponent_header(table)
    table_body = table.find("tbody")

    rows = table_body.find_all("tr")

    data_frame = pd.DataFrame(columns=table_headers, index=range(len(rows)))
    data_frame = remove_mid_headers(data_frame, rows)

    if include_game_link:
        links = []
        for i in range(len(rows)):
            cells = rows[i].find_all("td")
            try:
                links.append(cells[1].find('a', href=True)["href"])
            except IndexError:
                # Occurs when header is in middle of table - ignores header and does not add link to links[]
                continue

        data_frame["Links"] = links

    return data_frame


def bbref_player(url, table_id, player_name= None):
    """
    Accesses the url supplied to the method and compares the name of that player to the one supplied,
    if one is given. If incorrect name, increments the number in the url by 1 and checks next page.
    If only url is supplied, returns the table found on that url's page.

    :param url: url of player's page on Basketball-Reference.com
    :param table_id: html id of the table to access
    :param player_name: name of the player to look for. Used when looking for a player based on name and
    not url because there can be duplicate names
    :return: DataFrame of player's statistics
    """

    # When searching for player's page by url directly, not by name of player
    if player_name is None:
        return bbref_player_table(url=url, table_id=table_id)

    soup = get_page_soup(url)

    name_section = soup.find("div", {"itemtype": "https://schema.org/Person"})
    short_name = name_section.find("h1", {"itemprop": "name"}).get_text(strip ="\n")
    long_names = name_section.find_all("strong")
    for i in range(len(long_names)):
        if long_names[i].get_text(strip="\n") != "Pronunciation":
            long_name = long_names[i].get_text(strip="\n")
            break

    player_name_list = player_name.split(" ")
    short_name_list = short_name.split(" ")
    long_name_list = long_name.split(" ")

    num_matching = 0
    correct_name = False
    for name_player in player_name_list:
        for name_short in short_name_list:
            if name_player == name_short:
                num_matching += 1
                break
    if num_matching == len(player_name_list):
        correct_name = True
    else:
        num_matching = 0
        for name_player in player_name_list:
            for name_long in long_name_list:
                if name_player == name_long:
                    num_matching += 1
                    break
        if num_matching == len(player_name_list):
            correct_name = True

    if correct_name:
        return bbref_player_table(table_id=table_id, page_soup=soup)
    else:
        # The page being checked was not for correct player - increments the number included in the URL (starts at 01)
        # to check for next player with the same first 5 letters in last name and same first
        # 2 letters in first name.
        next_url = url[: len(url)-6] + str(int(url[len(url)-6]) + 1) + url[len(url)-5 :]
        bbref_player(next_url, player_name)


def bbref_player_table(table_id, url=None, page_soup=None):
    """
    Returns a table of player statistics for the supplied url or page.
    Page is provided in the case that the correct player was found in bbref_player method,
    as to avoid the need to request that url's content again.

    :param table_id: the html id of the table to return
    :param url: the url of the player's page
    :param page: the source html of the player's page
    :return: DataFrame of player's statistics
    """

    if page_soup is None:
        soup = get_page_soup(url)
    else:
        soup = page_soup

    table = soup.find("div", {"id": table_id})

    # If the data is stored in a comment, must get data inside of it by finding comment
    table = remove_comment(table)

    table_headers = change_opponent_header(table)

    table_body = table.find("tbody")
    seasons = table_body.find_all("th")
    rows = table_body.find_all("tr")

    data_frame = pd.DataFrame(columns=['Season'] + table_headers, index=range(len(rows)))
    data_frame = remove_mid_headers(data_frame, rows, append_to_front=seasons)

    return data_frame


def bbref_referee_stats(*args):
    """
    Returns the averaged relative statistics for a group of referees.
    The statistics are relative to the average of all referees.
    A positive number indicates that the referee favors the home team,
    while a negative number indicates the referee favors the away team.

    :param args: The name of the referees to find statistics for. Must be referees
    active in the current season
    :return: relative averaged statistics for the referees
    """
    date = datetime.datetime.now()
    url = "https://www.basketball-reference.com/referees/{year}_register.html".format(year = date.year)

    soup = get_page_soup(url)

    referees = soup.findAll("th", {"data-stat": "referee"})

    # array to store referee stats before averaging into a Series
    ref_stats = np.empty(shape=(len(args), 5))

    i = 0
    for referee_name in args:
        referee_name = referee_name.split(" ")

        if referee_name[0][0].isupper() and referee_name[0][1].isupper():
            # Must change name like "JB" to "J.B." to find on basketball-reference.com
            referee_name[0] = referee_name[0][0] + "." + referee_name[0][1] + "."

        for ref in referees:
            name = ref.get_text()
            name = name.split(" ")
            if referee_name[0] == name[0] and referee_name[1] == referee_name[1]:
                ref_page_link = ref.find('a', href=True)["href"]

        ref_url = "https://www.basketball-reference.com{ref}".format(ref=ref_page_link)

        soup = get_page_soup(ref_url)
        table = soup.find("div", {"id" : "all_rs_home_vs_visitor"})

        table = remove_comment(table)

        # Finds career average statistics for the referee
        career = table.find("tfoot")
        cells = career.find_all("td")

        # Relative statistics are the last 5 cells in the table
        ref_stats[i] = [cells[len(cells) - 5].get_text(),
                        cells[len(cells) - 4].get_text(),
                        cells[len(cells) - 3].get_text(),
                        cells[len(cells) - 2].get_text(),
                        cells[len(cells) - 1].get_text()]
        i += 1
    avg = np.average(ref_stats, axis=0)
    
    data_series = pd.Series(avg, index=["W/L%", "FGA", "FTA", "PF", "PTS"])
    return data_series


def splits_table(url):
    soup = get_page_soup(url)

    table = soup.find("div", {"id": "div_team_splits"})
    rows = table.find_all("tr")

    # totals - team avg points - opp avg points
    # home - home avg points - home opp avg points
    # away - away avg points - away opp avg points

    values = []

    cells = rows[2].find_all("td")
    values.append([cells[17].get_text(), cells[31].get_text()])
    cells = rows[4].find_all("td")
    values.append([cells[17].get_text(), cells[31].get_text()])
    cells = rows[5].find_all("td")
    values.append([cells[17].get_text(), cells[31].get_text()])

    return values
