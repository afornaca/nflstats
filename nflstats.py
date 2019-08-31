import math
import xlsxwriter
from xlsxwriter import Workbook
from collections import OrderedDict
from tkinter import *
from tkinter.ttk import *
import re
from sportsreference.nfl.teams import Teams
from sportsreference.nfl.schedule import Schedule
from sportsreference.nfl.boxscore import Boxscores
from sportsreference.nfl.boxscore import Boxscore

team_elo_list = []


class NflTeam:
    name = ""
    abbrev = ""
    elo = 1500

    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation


class NflStatsGUI:
    def __init__(self, master):
        self.master = master
        master.title("STILL TESTING STUFF OUT :)")
        master.geometry("600x900")

        team_dict = {'Kansas City Chiefs': 'KAN', 'Los Angeles Rams': 'RAM', 'New Orleans Saints': 'NOR',
                     'New England Patriots': 'NWE', 'Indianapolis Colts': 'CLT', 'Pittsburgh Steelers': 'PIT',
                     'Seattle Seahawks': 'SEA', 'Los Angeles Chargers': 'SDG', 'Chicago Bears': 'CHI',
                     'Atlanta Falcons': 'ATL', 'Houston Texans': 'HTX', 'Tampa Bay Buccaneers': 'TAM',
                     'Baltimore Ravens': 'RAV', 'Carolina Panthers': 'CAR', 'Green Bay Packers': 'GNB',
                     'New York Giants': 'NYG', 'Cincinnati Bengals': 'CIN', 'Philadelphia Eagles': 'PHI',
                     'Minnesota Vikings': 'MIN', 'Cleveland Browns': 'CLE', 'San Francisco 49ers': 'SFO',
                     'Detroit Lions': 'DET', 'Miami Dolphins': 'MIA', 'Tennessee Titans': 'OTI',
                     'Oakland Raiders': 'RAI', 'Washington Redskins': 'WAS', 'Buffalo Bills': 'BUF',
                     'Jacksonville Jaguars': 'JAX', 'Arizona Cardinals': 'CRD', 'Denver Broncos': 'DEN',
                     'Dallas Cowboys': 'DAL', 'New York Jets': 'NYJ'
                     }

        # GUI ELEMENTS
        self.select_team_label = Label(master, text="Select a team:")
        self.team_combo = Combobox(master, values=list(team_dict.keys()))
        self.year_label = Label(master, text="Enter a year:")
        self.year_entry = Entry(master, width=4)

        self.sched_button = Button(master, text="Get Schedule", command=lambda: self.schedule(self.team_combo.get(),
                                                                                              self.year_entry.get(),
                                                                                              team_dict))
        self.select_week = Button(master, text="WEEK TEST", command=lambda: self.week_schedule(2018, 1, team_dict))
        self.elo_startyear_label = Label(master, text="Start Year:")
        self.elo_startyear_entry = Entry(master, width=4)
        self.elo_endyear_label = Label(master, text="End Year:")
        self.elo_endyear_entry = Entry(master, width=4)
        self.calculate_elo_button = Button(master, text="Calculate Elo",
                                           command=lambda: self.calculate_elo(team_dict,
                                                                              self.elo_startyear_entry.get(),
                                                                              self.elo_endyear_entry.get()))
        self.output_text = Text(master, height=40, width=50)

        # GRID LAYOUT
        self.select_team_label.grid(row=0, column=0, sticky=W)
        self.team_combo.grid(row=0, column=1, sticky=W)
        self.year_label.grid(row=1, column=0, sticky=W)
        self.year_entry.grid(row=1, column=1, sticky=W)
        self.sched_button.grid(row=2, column=0, sticky=W)
        self.select_week.grid(row=3, column=0)
        self.elo_startyear_label.grid(row=4, column=0)
        self.elo_startyear_entry.grid(row=4, column=1, sticky=W)
        self.elo_endyear_label.grid(row=5, column=0)
        self.elo_endyear_entry.grid(row=5, column=1, sticky=W)
        self.calculate_elo_button.grid(row=6, column=0, sticky=E)
        self.output_text.grid(row=7, column=1)

    def schedule(self, teamname, year, team_dict):
        team_abbrev = ''
        for key, value in team_dict.items():
            if key == teamname:
                team_abbrev = team_dict[key]
        self.output_text.delete(1.0, "end-1c")
        self.output_text.insert("end-1c", teamname + " " + year + " Schedule:\n")
        team_schedule = Schedule(team_abbrev, year)
        for game in team_schedule:
            self.output_text.insert("end-1c", '{:15s} {:24s}\n'.format(game.date + ":", game.opponent_name))

    def week_schedule(self, year, week, team_dict):
        winner_name = ""
        loser_name = ""
        p = re.compile("'(\\d{4}\\d+\\w+)'")
        selected_week = Boxscores(week, year)
        game_codes = p.findall(str(selected_week.games.values()))

        self.output_text.delete(1.0, "end-1c")
        for code in game_codes:
            game_data = Boxscore(code)
            for name, abbrev in team_dict.items():
                if abbrev == game_data.winning_abbr:
                    winner_name = name
            for name, abbrev in team_dict.items():
                if abbrev == game_data.losing_abbr:
                    loser_name = name
            self.output_text.insert("end-1c", winner_name + " " + str(game_data.home_points) + " " +
                                    loser_name + " " + str(game_data.away_points) + "\n")

    def calculate_elo(self, team_dict, start_year, end_year):
        # CONSTANT K FOR ELO ALGO

        excel_name = 'NFLelo' + start_year + '-' + end_year + '.xlsx'
        wb = xlsxwriter.Workbook(excel_name)

        start_year = int(start_year)
        end_year = int(end_year)

        k = 30
        p = re.compile("'(\\d{4}\\d+\\w+)'")
        team_objects = {}
        self.output_text.delete(1.0, "end-1c")
        for name, abbrev in team_dict.items():
            new_team = NflTeam(name, abbrev)
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

            for abbrev, team in team_objects.items():
                if year > start_year:
                    team.elo = team.elo * (2 / 3) + 1500 * (1 / 3)
                    print("############", team.name, str(team.elo), "########")
            # will iterate through weeks 1-21
            for week in range(1, 22):
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

            if year == 2019:
                for abbrev, team in team_objects.items():
                    team.elo = team.elo * (2 / 3) + 1500 * (1 / 3)

            n = 1
            excel_dict = OrderedDict(sorted(team_objects.items(), key=lambda x: x[1].elo, reverse=True))
            for abv, tobj in excel_dict.items():
                for name, ab in team_dict.items():
                    if ab == abv:
                        sheet.write(n, 0, name)
                        sheet.write(n, 1, tobj.elo)
                        for team in Teams(year):
                            if team.abbreviation == abv:
                                sheet.write(n, 2, team.wins)
                                sheet.write(n, 3, team.losses)
                        n = n + 1

        rank = 1
        newdict = OrderedDict(sorted(team_objects.items(), key=lambda x: x[1].elo, reverse=True))
        for abv, tobj in newdict.items():
            for name, ab in team_dict.items():
                if ab == abv:
                    self.output_text.insert("end-1c", '{:4s}{:24s}{:9s}\n'.format(str(rank) + '.', name, str(tobj.elo)))
                    rank = rank + 1

        # Close Excel Workbook
        wb.close()

    def probability(self, team1elo, team2elo):
        return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (team1elo - team2elo) / 400))


root = Tk()
my_gui = NflStatsGUI(root)
root.mainloop()

######################################################################################
# Adds teams and their total yards to a dictionary and prints them in ordered form
######################################################################################
# from sportsreference.nfl.teams import Teams
# Ordered = {}
# for team in Teams('2018'):
#     Ordered[team.yards] = team.name
#
# for key in sorted(Ordered.keys(), reverse=True):
#     print(str(key) + ' ' + Ordered[key])


# from sportsreference.nfl.teams import Teams
# from sportsreference.nfl.roster import Player
#
# for team in Teams('2018'):
#     for player in team.roster.players(slim=False):
#         for i in player:
#             plyr = Player(i.player_id)
#             # if plyr.passing_yards > 100:
#             #     print(plyr.name + plyr.passing_yards)
#             print(plyr.name + str(plyr.passing_yards))

# from sportsreference.nfl.roster import Player
#
# sqn = Player('ZuerGr00')
# print(sqn.fourty_to_fourty_nine_yard_field_goal_attempts)
# print(sqn.fourty_to_fourty_nine_yard_field_goals_made)
