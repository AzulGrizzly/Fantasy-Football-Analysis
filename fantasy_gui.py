import tkinter as tk
from tkinter import ttk
import time
import requests
from tkinter import messagebox
import threading


class Player:
    def __init__(self, name, position, projected_points, average_points):
        self.name = name
        self.position = position
        self.projected_points = projected_points
        self.average_points = average_points


class NewFantasyAPI:
    def __init__(self):
        self.api_key = 'bd56f6b962d54687bebfd25d80bb4ab8'
        self.base_url = 'https://api.sportsdata.io/v3/nfl/scores/json/'

    def get_autocomplete_players(self, team, search_text):
        url = f"{self.base_url}PlayersBasic/{team}?key={self.api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            matching_players = [player['Name'] for player in data if search_text.lower() in player['Name'].lower()]
            return matching_players
        else:
            print(f"Failed to retrieve player names. Status code: {response.status_code}")
            return []

    def get_player_by_name(self, player_name):
        url = f"{self.base_url}PlayersBasic?key={self.api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            matching_players = [player for player in data if player_name.lower() in player['FullName'].lower()]

            if matching_players:
                player_id = matching_players[0]["PlayerID"]
                player_info_url = f"{self.base_url}Player/{player_id}?key={self.api_key}"
                player_info_response = requests.get(player_info_url)

                if player_info_response.status_code == 200:
                    player_info = player_info_response.json()
                    player = Player(
                        player_info["FullName"],
                        player_info["Position"],
                        None,  # Replace with the appropriate projected points data from the new API
                        None,  # Replace with the appropriate average points data from the new API
                    )
                    return player
                else:
                    print(f"Failed to retrieve player data. Status code: {player_info_response.status_code}")
                    return None
            else:
                return None
        else:
            print(f"Failed to retrieve player data. Status code: {response.status_code}")
            return None


    

    def calculate_player_weight(self, player):
        projected_points_weight = 0.4
        average_points_weight = 0.3
        positional_impact_weight = 0.2
        positional_scarcity_weight = 0.1
        max_projected_points = 50
        max_average_points = 30
        projected_points = player.projected_points  # Projected points for the week
        average_points = player.average_points      # Average points for the season
        position = player.position                  # Player's position

        normalized_projected_points = projected_points / max_projected_points  # Define max_projected_points based on your data
        normalized_average_points = average_points / max_average_points      # Define max_average_points based on your data

        positional_impact = {
            'QB': 0.9, 'RB': 1.0, 'WR': 1.2, 'TE': 1.1
        }
        positional_scarcity = {
            'QB': 0.5, 'RB': 1.0, 'WR': 1.5, 'TE': 1.2
        }

        weight = (
            projected_points_weight * normalized_projected_points +
            average_points_weight * normalized_average_points +
            positional_impact_weight * positional_impact.get(position, 1.0) +
            positional_scarcity_weight * positional_scarcity.get(position, 1.0)
        )

        return weight
    


    def analyze_trade(self, team1_players, team2_players):
        team1_weight = sum(self.calculate_player_weight(player) for player in team1_players)
        team2_weight = sum(self.calculate_player_weight(player) for player in team2_players)

        if team1_weight > team2_weight:
            return "Team 1 has the advantage in this trade."
        elif team2_weight > team1_weight:
            return "Team 2 has the advantage in this trade."
        else:
            return "This trade seems to be fairly balanced."
        
class FantasyFootballApp:
    def __init__(self, root, api):
        self.root = root
        self.root.title("Fantasy Football Trade Analysis App")
        self.root.geometry("800x400")  # Adjust the window size

        self.api = api
        self.all_player_names = []  # List to store all NFL player names
        self.team1_players = []  # Initialize an empty list for team1 players
        self.team2_players = []  # Initialize an empty list for team2 players

        # Create a Boolean variable to track if player names are loaded
        self.player_names_loaded = False

        self.setup_ui()  # Call setup_ui directly

        # Start a separate thread to fetch player names
        threading.Thread(target=self.fetch_player_names).start()


    def fetch_player_names(self):
        # Fetch player names here
        self.all_player_names = self.api.get_autocomplete_players(team="YOUR_TEAM_NAME", search_text="")
        self.all_player_names.sort()  # Sort the player names alphabetically
        self.player_names_loaded = True  # Mark player names as loaded

        # Populate dropdowns with player names
        self.root.after(0, self.populate_dropdowns_with_players)

        

    def populate_dropdowns_with_players(self):
        teams = [
            "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
            "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
            "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
            "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WSH"
        ]  # List of all NFL team abbreviations

        all_team_names = []

        for team_name in teams:
            player_names = self.api.get_autocomplete_players(team=team_name, search_text="")
            all_team_names.extend(player_names)

        all_team_names = list(set(all_team_names))  # Remove duplicates
        all_team_names.sort()  # Sort the team names alphabetically

        # Create Combobox widgets for team1 and team2 entries
        self.team1_entry['values'] = all_team_names
        self.team2_entry['values'] = all_team_names

    def setup_ui(self):

        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        self.team1_players = []
        self.team2_players = []

        team1_frame = ttk.Frame(self.main_frame)
        team1_frame.pack(side="left", padx=(0, 10), pady=10, expand=True, fill="both")

        ttk.Label(
            team1_frame, text="Enter Team 1 Players:"
        ).pack(side="top", anchor="w")

        self.team1_var = tk.StringVar()
        self.team1_entry = ttk.Combobox(
            team1_frame, textvariable=self.team1_var, width=20
        )
        self.team1_entry.pack(side="top", anchor="w", padx=10, pady=(0, 5))
        self.team1_entry.bind("<KeyRelease>", self.autocomplete_team1)

        self.team1_listbox = tk.Listbox(team1_frame, height=5, width=30)
        self.team1_listbox.pack(side="top", anchor="w", padx=10, pady=5)

        ttk.Button(
            team1_frame, text="Add Player", command=self.add_team1_player
        ).pack(side="top", anchor="w", padx=10, pady=(0, 5))

        ttk.Button(
            team1_frame, text="Remove Player", command=self.remove_selected_player_team1
        ).pack(side="top", anchor="w", padx=10, pady=(0, 5))

        team2_frame = ttk.Frame(self.main_frame)
        team2_frame.pack(side="right", padx=(10, 0), pady=10, expand=True, fill="both")

        ttk.Label(
            team2_frame, text="Enter Team 2 Players:"
        ).pack(side="top", anchor="w")

        self.team2_var = tk.StringVar()
        self.team2_entry = ttk.Combobox(
            team2_frame, textvariable=self.team2_var, width=20
        )
        self.team2_entry.pack(side="top", anchor="w", padx=10, pady=(0, 5))
        self.team2_entry.bind("<KeyRelease>", self.autocomplete_team2)

        self.team2_listbox = tk.Listbox(team2_frame, height=5, width=30)
        self.team2_listbox.pack(side="top", anchor="w", padx=10, pady=5)

        ttk.Button(
            team2_frame, text="Add Player", command=self.add_team2_player
        ).pack(side="top", anchor="w", padx=10, pady=(0, 5))

        ttk.Button(
            team2_frame, text="Remove Player", command=self.remove_selected_player_team2
        ).pack(side="top", anchor="w", padx=10, pady=(0, 5))

        self.populate_dropdowns_with_players()  # Populate dropdowns with player names

        ttk.Button(self.main_frame, text="Compare", command=self.compare_teams).pack(
            side="bottom", pady=20, anchor="center"
        )

        self.result_label = ttk.Label(
            self.main_frame, text="", wraplength=400, justify="left"
        )
        self.result_label.pack(side="bottom", padx=10, pady=10, fill="both")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.team1_entry.bind("<Return>", lambda event: self.add_team1_player())
        self.team2_entry.bind("<Return>", lambda event: self.add_team2_player())

        self.team1_entry.bind("<FocusIn>", self.on_team1_entry_focus)
        self.team2_entry.bind("<FocusIn>", self.on_team2_entry_focus)
        
    def on_team1_entry_focus(self, event):
        self.team1_entry['values'] = self.all_player_names
        self.team1_entry['state'] = 'readonly' if self.all_player_names else 'normal'

    def on_team2_entry_focus(self, event):
        self.team2_entry['values'] = self.all_player_names
        self.team2_entry['state'] = 'readonly' if self.all_player_names else 'normal'

    def remove_selected_player_team1(self):
        selected_indices = self.team1_listbox.curselection()
        if selected_indices:
            index_to_remove = selected_indices[0]
            del self.team1_players[index_to_remove]
            self.team1_listbox.delete(index_to_remove)

    def remove_selected_player_team2(self):
        selected_indices = self.team2_listbox.curselection()
        if selected_indices:
            index_to_remove = selected_indices[0]
            del self.team2_players[index_to_remove]
            self.team2_listbox.delete(index_to_remove)

    def on_team1_name_click(self, event):
        selected_name = self.team1_entry.get()
        self.add_team1_player(selected_name)

    def on_team2_name_click(self, event):
        selected_name = self.team2_entry.get()
        self.add_team2_player(selected_name)

    def add_team1_player(self):
        player_name = self.team1_var.get().strip() or self.team1_highlighted_player
        if player_name:
            if player_name not in [player.name for player in self.team1_players]:
                player = self.api.get_player_by_name(player_name)

                if player:
                    self.team1_players.append(player)
                    player_info = f"{player_name} ({player.position})"
                    self.team1_listbox.insert(tk.END, player_info)
                    self.team1_entry.delete(0, tk.END)
                    self.animate_entry(self.team1_entry)

                    # Store playerid along with the player in team1_players
                    self.team1_players[-1].playerid = player.playerid
                else:
                    messagebox.showerror("Error", f"Player '{player_name}' not found.")
            else:
                messagebox.showinfo("Info", f"Player '{player_name}' already added.")

    def add_team2_player(self):
        player_name = self.team2_var.get().strip() or self.team2_highlighted_player
        if player_name:
            if player_name not in [player.name for player in self.team2_players]:
                player = self.api.get_player_by_name(player_name)
                if player:
                    self.team2_players.append(player)
                    player_info = f"{player_name} ({player.position})"
                    self.team2_listbox.insert(tk.END, player_info)
                    self.team2_entry.delete(0, tk.END)
                    self.animate_entry(self.team2_entry)

                    # Store playerid along with the player in team2_players
                    self.team2_players[-1].playerid = player.playerid
                else:
                    messagebox.showerror("Error", f"Player '{player_name}' not found.")
            else:
                messagebox.showinfo("Info", f"Player '{player_name}' already added.")

    def animate_entry(self, entry):
        original_bg = entry.cget("background")
        entry.config(background="lightblue")
        self.root.update()
        time.sleep(0.2)
        entry.config(background=original_bg)

    def compare_teams(self):
        team1_weight = sum(self.calculate_player_weight(player) for player in self.team1_players)
        team2_weight = sum(self.calculate_player_weight(player) for player in self.team2_players)

        weight_difference = abs(team1_weight - team2_weight)
        fairness_threshold = 0.05

        if weight_difference <= fairness_threshold:
            trade_result = "Fair Trade"
        else:
            trade_result = "Unfair Trade"

        # Clear the "Comparing..." text
        self.result_label.config(text="")

        result_window = tk.Toplevel(self.root)
        result_window.title("Trade Result")

        popup_width = 300
        popup_height = 90
        x = self.root.winfo_x() + (self.root.winfo_width() - popup_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - popup_height) // 2

        result_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        text_color = "green" if trade_result == "Fair Trade" else "red"
        result_label = ttk.Label(
            result_window, text=f"Trade Result: {trade_result}", font=("Helvetica", 16), foreground=text_color
        )
        result_label.pack(padx=20, pady=20)

    def autocomplete_team1(self, event):
        current_text = self.team1_var.get().lower()
        if len(current_text) >= 3:
            matching_names = [name for name in self.all_team_names if name.lower().startswith(current_text)]
            self.team1_entry['values'] = matching_names
            self.team1_entry['state'] = 'readonly' if matching_names else 'normal'
        else:
            self.team1_entry['values'] = []
            self.team1_entry['state'] = 'normal'
            # Autofill the entry if there's only one matching name
            if len(matching_names) == 1:
                self.team1_entry.set(matching_names[0])

    def autocomplete_team2(self, event):
        current_text = self.team2_var.get().lower()
        if len(current_text) >= 3:
            matching_names = [name for name in self.all_team_names if name.lower().startswith(current_text)]
            self.team2_entry['values'] = matching_names
            self.team2_entry['state'] = 'readonly' if matching_names else 'normal'
        else:
            self.team2_entry['values'] = []
            self.team2_entry['state'] = 'normal'
            # Autofill the entry if there's only one matching name
            if len(matching_names) == 1:
                self.team2_entry.set(matching_names[0])


if __name__ == "__main__":
    root = tk.Tk()

    api = NewFantasyAPI()

    app = FantasyFootballApp(root, api)

    root.mainloop()