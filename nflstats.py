import math
import json
import xlsxwriter
import pandas
from collections import OrderedDict
from tkinter import *
from tkinter.ttk import *
import re
from sportsreference.nfl.teams import Teams
from sportsreference.nfl.schedule import Schedule
from sportsreference.nfl.boxscore import Boxscores
from sportsreference.nfl.boxscore import Boxscore
import team_object as teamobj

team_elo_list = []
# dictionaries for retrieving DB lookup abbreviation or team name when given the opposite
with open('miscjson.txt') as file:
    data = json.load(file)
team_dict = data['teamdict']
abbrev_dict = {val: key for key, val in team_dict.items()}

'''
FUNCTIONS TO BE TESTED -- using Pytest
'''
def sched(name, year):
    games_print = OrderedDict()
    team_abbrev = team_dict[name]
    team_schedule = Schedule(team_abbrev, year)
    for game in team_schedule:
        games_print[game.date] = game.opponent_name
    return games_print


def elo_regression(teams):
    for abbrev, team in teams.items():
        team.elo = team.elo * (2 / 3) + 1500 * (1 / 3)
    return teams


def get_game_codes(week, year):
    p = re.compile("'(\\d{4}\\d+\\w+)'")
    selected_week = Boxscores(int(week), year)
    return p.findall(str(selected_week.games.values()))

class NflStatsGUI:
    def __init__(self, master):
        self.master = master
        master.title("STILL TESTING STUFF OUT :)")
        master.geometry("700x900")

        ''' GUI ELEMENTS'''
        self.select_team_label = Label(master, text="Select a team:")
        self.team_combo = Combobox(master, values=list(sorted(team_dict.keys())))
        self.year_label = Label(master, text="Enter a year:")
        self.year_entry = Entry(master, width=4)

        self.sched_button = Button(master, text="Get Schedule", command=lambda: self.schedule(self.team_combo.get(),
                                                                                              self.year_entry.get()))
        self.elo_startyear_label = Label(master, text="Start Year:")
        self.elo_startyear_entry = Entry(master, width=4)
        self.elo_endyear_label = Label(master, text="End Year:")
        self.elo_endyear_entry = Entry(master, width=4)
        self.calculate_elo_button = Button(master, text="Calculate Elo",
                                           command=lambda: self.calculate_elo(team_dict, abbrev_dict,
                                                                              self.elo_startyear_entry.get(),
                                                                              self.elo_endyear_entry.get(),
                                                                              self.elo_endweek_entry.get()))
        self.elo_endweek_label = Label(master, text="End Week:")
        self.elo_endweek_entry = Entry(master, width=2)
        self.win_probability_week_label = Label(master, text="Win Prob Week:")
        self.win_probability_week_entry = Entry(master, width=2)
        self.win_probability_button = Button(master, text="Win Probabilities",
                                             command=lambda: self.generate_probabilities(
                                                 self.win_probability_week_entry.get(),
                                                 team_dict))
        self.output_text = Text(master, height=40, width=60)
        self.scroll = Scrollbar(master)
        self.output_text.config(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.output_text.yview)

        '''GRID LAYOUT'''
        self.select_team_label.grid(row=0, column=0, sticky=W)
        self.team_combo.grid(row=0, column=1, sticky=W)
        self.year_label.grid(row=1, column=0, sticky=W)
        self.year_entry.grid(row=1, column=1, sticky=W)
        self.sched_button.grid(row=2, column=0, sticky=W)
        self.elo_startyear_label.grid(row=4, column=0, sticky=W)
        self.elo_startyear_entry.grid(row=4, column=1, sticky=W)
        self.elo_endyear_label.grid(row=5, column=0, sticky=W)
        self.elo_endyear_entry.grid(row=5, column=1, sticky=W)
        self.elo_endweek_label.grid(row=6, column=0, sticky=W)
        self.elo_endweek_entry.grid(row=6, column=1, sticky=W)
        self.calculate_elo_button.grid(row=7, column=0, sticky=W)
        self.win_probability_week_label.grid(row=8, column=0, sticky=W)
        self.win_probability_week_entry.grid(row=8, column=1, sticky=W)
        self.win_probability_button.grid(row=9, column=0, sticky=W)
        self.output_text.grid(row=10, column=1)
        self.scroll.grid(row=10, column=2, sticky=N + S + W)

    def schedule(self, team_name, year):
        games = sched(team_name, year)
        self.output_text.delete(1.0, "end-1c")
        self.output_text.insert("end-1c", team_name + " " + year + " Schedule:\n")
        for date, opponent in games.items():
            self.output_text.insert('end-1c', '{:15s} {:24s}\n'.format(date + ":", opponent))

    def calculate_elo(self, team_dict, abbrev_dict, start_year, end_year, end_week):
        endw = 22
        week = 1
        excel_name = 'NFLelo' + start_year + '-' + end_year + 'week' + end_week + '.xlsx'
        wb = xlsxwriter.Workbook(excel_name)

        start_year = int(start_year)
        end_year = int(end_year)

        # CONSTANT K FOR ELO ALGO
        k = 30
        p = re.compile("'(\\d{4}\\d+\\w+)'")
        team_objects = {}
        self.output_text.delete(1.0, "end-1c")
        for name, abbrev in team_dict.items():
            new_team = teamobj.NflTeam(name, abbrev)
            team_objects.update({abbrev: new_team})
        for year in range(start_year, end_year + 1):
            # Initialize new excel sheet
            sheet = wb.add_worksheet(str(year))
            sheet.set_column(0, 0, 24)
            sheet.set_column(1, 1, 10)
            sheet.write(0, 0, "Team")
            sheet.write(0, 1, "Elo Rating")
            sheet.write(0, 2, "Wins")
            sheet.write(0, 3, "Losses")

            if year > start_year:
                team_objects = elo_regression(team_objects)

            # will iterate through weeks 1-21
            if year == end_year:
                endw = int(end_week) + 1
            for week in range(1, endw):
                print("----- YEAR ", year, " | WEEK:", week, "-----")
                selected_week = Boxscores(week, year)
                game_codes = p.findall(str(selected_week.games.values()))

                for game in game_codes:
                    box = Boxscore(game)
                    winner = team_objects[box.winning_abbr]
                    loser = team_objects[box.losing_abbr]

                    # elo
                    prob_winner = self.probability(loser.elo, winner.elo)
                    prob_loser = self.probability(winner.elo, loser.elo)
                    winner.elo = winner.elo + k * (1 - prob_winner)
                    loser.elo = loser.elo + k * (0 - prob_loser)

                    welo = round(winner.elo, 4)
                    lelo = round(loser.elo, 4)
                    print(winner.name, str(welo))
                    print(loser.name, str(lelo))

            # update elo at end of year to regress 1/3 to mean
            if year == end_year and week == 21:
                team_objects = elo_regression(team_objects)

            n = 1
            excel_dict = OrderedDict(sorted(team_objects.items(), key=lambda x: x[1].elo, reverse=True))
            for abv, tobj in excel_dict.items():
                for name, ab in team_dict.items():
                    if ab == abv:
                        sheet.write(n, 0, name)
                        sheet.write(n, 1, tobj.elo)
                        # SportsReference Library Team Lookups is Currently Broken as of 11/25/19
                        # for team in Teams(year):
                        #     if team.abbreviation == abv:
                        #         sheet.write(n, 2, team.wins)
                        #         sheet.write(n, 3, team.losses)
                        n = n + 1

        # SportsReference Library Team Lookups is Currently Broken as of 11/25/19
        # rank = 1
        # newdict = OrderedDict(sorted(team_objects.items(), key=lambda x: x[1].elo, reverse=True))
        # for abv, tobj in newdict.items():
        #     name = abbrev_dict[abv]
        #     self.output_text.insert("end-1c", '{:4s}{:24s}{:9s}\n'.format(str(rank) + '.', name, str(tobj.elo)))
        #     rank = rank + 1

        # Close Excel Workbook
        wb.close()

    def probability(self, team1elo, team2elo):
        return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (team1elo - team2elo) / 400))

    def generate_probabilities(self, week, team_dict):
        self.output_text.delete(1.0, "end-1c")
        year = 2019
        home_team = ""
        away_team = ""
        data = pandas.read_excel(r'NFLelo2015-2019week5.xlsx', sheet_name='2019')
        df = pandas.DataFrame(data, columns=['Team', 'Elo Rating'])
        ratings_dict = dict(zip(df['Team'], df['Elo Rating']))

        game_codes = get_game_codes(week, year)

        for game in game_codes:
            box = Boxscore(game)
            for name, abv in team_dict.items():
                if abv == box.home_abbreviation.upper():
                    home_team = name
                    print(home_team)
                if abv == box.away_abbreviation.upper():
                    away_team = name
                    print(away_team)
            elo_difference = ratings_dict[home_team] - ratings_dict[away_team]
            spread = str(round(-elo_difference / 25))
            if spread == '0':
                spread = 'even'
            if '-' not in spread:
                if spread == 'even':
                    spread = spread
                else:
                    spread = '+' + spread

            home_probability = round(100 * (1 / ((math.pow(10, -elo_difference / 400)) + 1)), 2)
            away_probability = round(100 - home_probability, 2)
            self.output_text.insert("end-1c", '{:24s}{:5}\n{:24s}{:5}\nElo-based Spread: {:3}\n\n'
                                    .format(away_team, away_probability, home_team, home_probability, spread))


root = Tk()
my_gui = NflStatsGUI(root)
root.mainloop()
