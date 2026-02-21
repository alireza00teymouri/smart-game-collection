

import random
import json
import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import customtkinter as ctk
from tkinter import messagebox


# -------------------- Game Logic --------------------
class Move:
    def __init__(self, code: str, name: str, display_name: str):
        self.code = code
        self.name = name
        self.display_name = display_name

    def __repr__(self):
        return f"Move({self.code})"

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.code == other.code
        return False


class Rules:
    def __init__(self, moves: List[Move], beats_map: Dict[str, List[str]]):
        self.moves = moves
        self.move_by_code = {m.code: m for m in moves}
        self.beats: Dict[Move, List[Move]] = {}
        self.loses_to: Dict[Move, List[Move]] = {m: [] for m in moves}
        for winner_code, loser_codes in beats_map.items():
            winner = self.move_by_code[winner_code]
            self.beats[winner] = [self.move_by_code[code] for code in loser_codes]
            for loser_code in loser_codes:
                loser = self.move_by_code[loser_code]
                self.loses_to[loser].append(winner)

    def get_winner(self, move1: Move, move2: Move) -> Optional[Move]:
        if move1 == move2:
            return None
        if move2 in self.beats.get(move1, []):
            return move1
        if move1 in self.beats.get(move2, []):
            return move2
        raise ValueError(f"No rule defined between {move1.code} and {move2.code}")

    def get_counter(self, move: Move) -> List[Move]:
        return self.loses_to.get(move, [])

    def get_random_move(self) -> Move:
        return random.choice(self.moves)


def get_classic_rules() -> Rules:
    moves = [
        Move('r', 'rock', 'Rock'),
        Move('p', 'paper', 'Paper'),
        Move('s', 'scissors', 'Scissors')
    ]
    beats_map = {
        'r': ['s'],
        'p': ['r'],
        's': ['p']
    }
    return Rules(moves, beats_map)


def get_extended_rules() -> Rules:
    moves = [
        Move('r', 'rock', 'Rock'),
        Move('p', 'paper', 'Paper'),
        Move('s', 'scissors', 'Scissors'),
        Move('l', 'lizard', 'Lizard'),
        Move('k', 'spock', 'Spock')
    ]
    beats_map = {
        'r': ['s', 'l'],
        'p': ['r', 'k'],
        's': ['p', 'l'],
        'l': ['p', 'k'],
        'k': ['r', 's']
    }
    return Rules(moves, beats_map)


# -------------------- Statistics Management --------------------
class StatsManager:
    STATS_FILE = "game_stats.json"

    def __init__(self):
        self.stats = self.load_stats()

    def load_stats(self) -> dict:
        if os.path.exists(self.STATS_FILE):
            try:
                with open(self.STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.default_stats()
        else:
            return self.default_stats()

    def default_stats(self) -> dict:
        return {
            "classic": {"player_wins": 0, "computer_wins": 0, "ties": 0, "games": 0},
            "extended": {"player_wins": 0, "computer_wins": 0, "ties": 0, "games": 0},
            "coin": {"player_wins": 0, "computer_wins": 0, "ties": 0, "games": 0}
        }

    def save_stats(self):
        with open(self.STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=4)

    def increment(self, game_type: str, result: str):
        """result: 'player', 'computer', 'tie'"""
        if game_type not in self.stats:
            return
        self.stats[game_type]["games"] += 1
        if result == 'player':
            self.stats[game_type]["player_wins"] += 1
        elif result == 'computer':
            self.stats[game_type]["computer_wins"] += 1
        else:  # tie
            self.stats[game_type]["ties"] += 1
        self.save_stats()

    def get_summary(self, game_type: str) -> str:
        s = self.stats.get(game_type, {})
        total = s.get("games", 0)
        pw = s.get("player_wins", 0)
        cw = s.get("computer_wins", 0)
        ties = s.get("ties", 0)
        return f"Games played: {total}\nYour wins: {pw}\nComputer wins: {cw}\nTies: {ties}"


# -------------------- Base Game Frame with Timer --------------------
class GameFrame(ctk.CTkFrame):
    def __init__(self, master, best_of: int, game_type: str, timer_seconds: int = 10, **kwargs):
        super().__init__(master, **kwargs)
        self.best_of = best_of
        self.game_type = game_type
        self.timer_seconds = timer_seconds
        self.player_score = 0
        self.computer_score = 0
        self.round = 0
        self.timer_id = None
        self.timer_remaining = 0
        self.waiting_for_choice = False
        self.create_widgets()
        self.pack(fill="both", expand=True)

    def create_widgets(self):
        self.title_label = ctk.CTkLabel(self, text="", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=10)

        # Timer and progress bar
        self.timer_frame = ctk.CTkFrame(self)
        self.timer_frame.pack(pady=5, fill="x", padx=20)
        self.timer_label = ctk.CTkLabel(self.timer_frame, text="Time left: ", font=("Arial", 14))
        self.timer_label.pack(side="left", padx=5)
        self.progress_bar = ctk.CTkProgressBar(self.timer_frame, width=250)
        self.progress_bar.pack(side="left", padx=5)
        self.progress_bar.set(1.0)

        self.score_frame = ctk.CTkFrame(self)
        self.score_frame.pack(pady=10)
        self.player_score_label = ctk.CTkLabel(self.score_frame, text="You: 0", font=("Arial", 18, "bold"))
        self.player_score_label.grid(row=0, column=0, padx=30)
        self.computer_score_label = ctk.CTkLabel(self.score_frame, text="Computer: 0", font=("Arial", 18, "bold"))
        self.computer_score_label.grid(row=0, column=1, padx=30)

        self.result_label = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.result_label.pack(pady=10)

        self.back_button = ctk.CTkButton(
            self,
            text="Back to Menu",
            command=self.back_to_menu,
            width=200,
            height=50,
            font=("Arial", 16)
        )
        self.back_button.pack(pady=10)

    def update_score_display(self):
        self.player_score_label.configure(text=f"You: {self.player_score}")
        self.computer_score_label.configure(text=f"Computer: {self.computer_score}")

    def start_timer(self):
        self.timer_remaining = self.timer_seconds
        self.progress_bar.set(1.0)
        self.waiting_for_choice = True
        self.update_timer()

    def update_timer(self):
        if not self.waiting_for_choice:
            return
        self.timer_remaining -= 1
        progress = self.timer_remaining / self.timer_seconds
        self.progress_bar.set(max(0, progress))
        self.timer_label.configure(text=f"Time left: {self.timer_remaining} s")
        if self.timer_remaining <= 0:
            self.handle_timeout()
        else:
            self.timer_id = self.after(1000, self.update_timer)

    def handle_timeout(self):
        self.waiting_for_choice = False
        self.force_loss()

    def force_loss(self):
        """User forced to lose due to timeout"""
        pass  # Implement in subclass

    def stop_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.waiting_for_choice = False

    def check_game_over(self):
        required = (self.best_of // 2) + 1
        if self.player_score >= required:
            messagebox.showinfo("Game Over", "🏆 Congratulations! You are the champion!")
            self.master.stats_manager.increment(self.game_type, 'player')
            self.back_to_menu()
            return True
        elif self.computer_score >= required:
            messagebox.showinfo("Game Over", "😞 Computer is the champion! Better luck next time.")
            self.master.stats_manager.increment(self.game_type, 'computer')
            self.back_to_menu()
            return True
        return False

    def back_to_menu(self):
        self.stop_timer()
        self.master.show_main_menu()


# -------------------- Rock Paper Scissors Game --------------------
class RPSGameFrame(GameFrame):
    def __init__(self, master, rules: Rules, best_of: int, game_type: str, smart_level: int, timer_seconds: int = 10, **kwargs):
        super().__init__(master, best_of, game_type, timer_seconds, **kwargs)
        self.rules = rules
        self.smart_level = smart_level
        self.history: List[Move] = []
        self.title_label.configure(text="Rock Paper Scissors" + (" (Extended)" if len(rules.moves) > 3 else ""))
        self.create_game_widgets()
        self.start_timer()

    def create_game_widgets(self):
        self.buttons_frame = ctk.CTkFrame(self)
        self.buttons_frame.pack(pady=20)

        # Larger buttons for moves
        for i, move in enumerate(self.rules.moves):
            btn = ctk.CTkButton(
                self.buttons_frame,
                text=f"{move.display_name} ({move.code})",
                command=lambda m=move: self.player_choice(m),
                width=150,
                height=60,
                font=("Arial", 18, "bold"),
                corner_radius=10
            )
            row = i // 3
            col = i % 3
            btn.grid(row=row, column=col, padx=15, pady=10)

    def get_computer_choice(self) -> Move:
        if len(self.history) < 3 or self.smart_level == 0:
            return self.rules.get_random_move()

        if self.smart_level == 1:
            # Simple prediction: most frequent overall move
            freq = defaultdict(int)
            for move in self.history:
                freq[move] += 1
            predicted = max(freq.items(), key=lambda x: x[1])[0]
        else:  # smart_level >= 2: Markov chain based on last move
            if len(self.history) < 2:
                return self.rules.get_random_move()
            last_move = self.history[-1]
            transitions = defaultdict(int)
            for i in range(len(self.history) - 1):
                if self.history[i] == last_move:
                    transitions[self.history[i+1]] += 1
            if transitions:
                predicted = max(transitions.items(), key=lambda x: x[1])[0]
            else:
                predicted = last_move  # fallback

        counters = self.rules.get_counter(predicted)
        if counters:
            return random.choice(counters)
        else:
            return self.rules.get_random_move()

    def player_choice(self, player_move: Move):
        if not self.waiting_for_choice:
            return
        self.stop_timer()
        self.play_round(player_move)

    def force_loss(self):
        computer_move = self.get_computer_choice()
        dummy_move = self.rules.moves[0]  # just for display
        self.play_round(dummy_move, force_loss=True, computer_override=computer_move)

    def play_round(self, player_move: Move, force_loss=False, computer_override: Move = None):
        if computer_override:
            computer_move = computer_override
        else:
            computer_move = self.get_computer_choice()

        if not force_loss:
            self.history.append(player_move)

        winner_move = self.rules.get_winner(player_move, computer_move)
        if winner_move is None:
            result_text = "It's a tie!"
            result_type = 'tie'
        elif winner_move == player_move:
            result_text = "🎉 You win this round!"
            result_type = 'player'
            self.player_score += 1
        else:
            result_text = "💻 Computer wins this round!"
            result_type = 'computer'
            self.computer_score += 1

        if force_loss:
            result_text = "⏰ Time's up! " + result_text
            result_type = 'computer'
            self.computer_score += 1

        self.round += 1
        self.update_score_display()

        self.result_label.configure(
            text=f"Round {self.round}: You chose {player_move.display_name}, Computer chose {computer_move.display_name}\n{result_text}"
        )

        if not self.check_game_over():
            self.start_timer()

    def check_game_over(self):
        if super().check_game_over():
            return True
        return False


# -------------------- Coin Toss Game --------------------
class CoinTossGameFrame(GameFrame):
    def __init__(self, master, best_of: int, game_type: str, timer_seconds: int = 10, **kwargs):
        super().__init__(master, best_of, game_type, timer_seconds, **kwargs)
        self.title_label.configure(text="Coin Toss")
        self.sides = {'h': 'Heads', 't': 'Tails'}
        self.create_game_widgets()
        self.start_timer()

    def create_game_widgets(self):
        self.buttons_frame = ctk.CTkFrame(self)
        self.buttons_frame.pack(pady=20)

        ctk.CTkButton(
            self.buttons_frame,
            text="Heads (h)",
            command=lambda: self.player_choice('h'),
            width=200,
            height=70,
            font=("Arial", 20, "bold"),
            corner_radius=10
        ).grid(row=0, column=0, padx=20, pady=10)

        ctk.CTkButton(
            self.buttons_frame,
            text="Tails (t)",
            command=lambda: self.player_choice('t'),
            width=200,
            height=70,
            font=("Arial", 20, "bold"),
            corner_radius=10
        ).grid(row=0, column=1, padx=20, pady=10)

    def player_choice(self, player_choice: str):
        if not self.waiting_for_choice:
            return
        self.stop_timer()
        self.play_round(player_choice)

    def force_loss(self):
        computer_choice = random.choice(['h', 't'])
        self.play_round(None, force_loss=True, computer_override=computer_choice)

    def play_round(self, player_choice: Optional[str], force_loss=False, computer_override=None):
        if computer_override:
            computer_choice = computer_override
        else:
            computer_choice = random.choice(['h', 't'])

        if force_loss or player_choice is None:
            result_type = 'computer'
            result_text = f"⏰ Time's up! Computer chose {self.sides[computer_choice]}"
            self.computer_score += 1
        else:
            if player_choice == computer_choice:
                result_type = 'player'
                result_text = f"🎉 You win this round! (Both {self.sides[computer_choice]})"
                self.player_score += 1
            else:
                result_type = 'computer'
                result_text = f"💻 Computer wins this round! (You {self.sides[player_choice]}, Computer {self.sides[computer_choice]})"
                self.computer_score += 1

        self.round += 1
        self.update_score_display()
        self.result_label.configure(text=f"Round {self.round}: {result_text}")

        if not self.check_game_over():
            self.start_timer()

    def check_game_over(self):
        if super().check_game_over():
            return True
        return False


# -------------------- Main Application --------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Game Collection")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.stats_manager = StatsManager()
        self.main_menu_frame = None
        self.current_game_frame = None

        self.show_main_menu()

    def show_main_menu(self):
        if self.current_game_frame:
            self.current_game_frame.destroy()
            self.current_game_frame = None

        if self.main_menu_frame:
            self.main_menu_frame.destroy()

        self.main_menu_frame = ctk.CTkFrame(self)
        self.main_menu_frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(self.main_menu_frame, text="🎮 Smart Game Collection", font=("Arial", 28, "bold"))
        title.pack(pady=40)

        # Theme selection
        theme_frame = ctk.CTkFrame(self.main_menu_frame)
        theme_frame.pack(pady=10)
        ctk.CTkLabel(theme_frame, text="Theme:", font=("Arial", 16)).pack(side="left", padx=5)
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["dark", "light", "system"],
                                       command=self.change_theme, variable=theme_var,
                                       width=150, font=("Arial", 14))
        theme_menu.pack(side="left", padx=5)

        # Game buttons (larger)
        btn_classic = ctk.CTkButton(
            self.main_menu_frame,
            text="Classic Rock Paper Scissors (3 moves)",
            command=self.start_classic,
            width=400,
            height=70,
            font=("Arial", 18, "bold"),
            corner_radius=10
        )
        btn_classic.pack(pady=15)

        btn_extended = ctk.CTkButton(
            self.main_menu_frame,
            text="Extended Rock Paper Scissors (5 moves)",
            command=self.start_extended,
            width=400,
            height=70,
            font=("Arial", 18, "bold"),
            corner_radius=10
        )
        btn_extended.pack(pady=15)

        btn_coin = ctk.CTkButton(
            self.main_menu_frame,
            text="Coin Toss",
            command=self.start_coin_toss,
            width=400,
            height=70,
            font=("Arial", 18, "bold"),
            corner_radius=10
        )
        btn_coin.pack(pady=15)

        # Statistics button
        btn_stats = ctk.CTkButton(
            self.main_menu_frame,
            text="Statistics",
            command=self.show_stats,
            width=350,
            height=60,
            font=("Arial", 16),
            fg_color="gray",
            corner_radius=10
        )
        btn_stats.pack(pady=8)

        # Help button
        btn_help = ctk.CTkButton(
            self.main_menu_frame,
            text="Help",
            command=self.show_help,
            width=350,
            height=60,
            font=("Arial", 16),
            fg_color="gray",
            corner_radius=10
        )
        btn_help.pack(pady=8)

        btn_exit = ctk.CTkButton(
            self.main_menu_frame,
            text="Exit",
            command=self.quit,
            width=350,
            height=60,
            font=("Arial", 18, "bold"),
            fg_color="red",
            hover_color="darkred",
            corner_radius=10
        )
        btn_exit.pack(pady=20)

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)

    def show_stats(self):
        stats_window = ctk.CTkToplevel(self)
        stats_window.title("Game Statistics")
        stats_window.geometry("450x450")
        stats_window.transient(self)

        notebook = ctk.CTkTabview(stats_window)
        notebook.pack(fill="both", expand=True)

        for game in ["classic", "extended", "coin"]:
            tab = notebook.add(game)
            summary = self.stats_manager.get_summary(game)
            label = ctk.CTkLabel(tab, text=summary, font=("Arial", 16), justify="left")
            label.pack(pady=30)

    def show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Help")
        help_window.geometry("550x500")
        help_window.transient(self)

        text = """
        Game Help:

        1. Classic Rock Paper Scissors:
           - Rock beats Scissors
           - Scissors beats Paper
           - Paper beats Rock

        2. Extended Rock Paper Scissors (5 moves):
           - Rock beats Scissors and Lizard
           - Paper beats Rock and Spock
           - Scissors beats Paper and Lizard
           - Lizard beats Paper and Spock
           - Spock beats Rock and Scissors

        3. Coin Toss:
           - Choose Heads or Tails; if it matches the computer's, you win.

        Game Settings:
        - Number of rounds: Must be odd.
        - Smart level: 0 = random, 1 = simple prediction (most frequent), 2 = advanced prediction (based on last move).
        - Timer: You have 10 seconds per round; otherwise you lose the round.

        Game statistics are saved in a JSON file.
        """
        label = ctk.CTkLabel(help_window, text=text, font=("Arial", 14), justify="left")
        label.pack(pady=20, padx=20)

    def get_game_settings(self) -> Tuple[Optional[int], Optional[int]]:
        settings_dialog = ctk.CTkToplevel(self)
        settings_dialog.title("Game Settings")
        settings_dialog.geometry("450x350")
        settings_dialog.transient(self)
        settings_dialog.grab_set()

        best_of_var = ctk.IntVar(value=3)
        smart_var = ctk.IntVar(value=1)

        ctk.CTkLabel(settings_dialog, text="Number of rounds (odd number):", font=("Arial", 14)).pack(pady=10)
        best_of_entry = ctk.CTkEntry(settings_dialog, textvariable=best_of_var, width=100, font=("Arial", 14))
        best_of_entry.pack(pady=5)

        ctk.CTkLabel(settings_dialog, text="Computer smart level:", font=("Arial", 14)).pack(pady=10)
        smart_frame = ctk.CTkFrame(settings_dialog)
        smart_frame.pack(pady=5)
        ctk.CTkRadioButton(smart_frame, text="Random (0)", variable=smart_var, value=0, font=("Arial", 13)).pack(side="left", padx=10)
        ctk.CTkRadioButton(smart_frame, text="Simple (1)", variable=smart_var, value=1, font=("Arial", 13)).pack(side="left", padx=10)
        ctk.CTkRadioButton(smart_frame, text="Advanced (2)", variable=smart_var, value=2, font=("Arial", 13)).pack(side="left", padx=10)

        result = [None, None]

        def confirm():
            try:
                best = best_of_var.get()
                if best <= 0 or best % 2 == 0:
                    messagebox.showerror("Error", "Number of rounds must be odd and positive.")
                    return
                result[0] = best
                result[1] = smart_var.get()
                settings_dialog.destroy()
            except:
                messagebox.showerror("Error", "Invalid input.")

        ctk.CTkButton(settings_dialog, text="Start", command=confirm, width=150, height=40, font=("Arial", 14)).pack(pady=20)

        self.wait_window(settings_dialog)
        return result[0], result[1]

    def start_classic(self):
        best_of, smart = self.get_game_settings()
        if best_of is None:
            return
        self.main_menu_frame.destroy()
        self.main_menu_frame = None
        self.current_game_frame = RPSGameFrame(
            self,
            rules=get_classic_rules(),
            best_of=best_of,
            game_type="classic",
            smart_level=smart,
            timer_seconds=10
        )

    def start_extended(self):
        best_of, smart = self.get_game_settings()
        if best_of is None:
            return
        self.main_menu_frame.destroy()
        self.main_menu_frame = None
        self.current_game_frame = RPSGameFrame(
            self,
            rules=get_extended_rules(),
            best_of=best_of,
            game_type="extended",
            smart_level=smart,
            timer_seconds=10
        )

    def start_coin_toss(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Coin Toss Settings")
        dialog.geometry("350x200")
        dialog.transient(self)
        dialog.grab_set()

        best_of_var = ctk.IntVar(value=3)
        ctk.CTkLabel(dialog, text="Number of rounds (odd number):", font=("Arial", 14)).pack(pady=10)
        entry = ctk.CTkEntry(dialog, textvariable=best_of_var, width=100, font=("Arial", 14))
        entry.pack(pady=5)

        result = [None]

        def confirm():
            try:
                best = best_of_var.get()
                if best <= 0 or best % 2 == 0:
                    messagebox.showerror("Error", "Number of rounds must be odd and positive.")
                    return
                result[0] = best
                dialog.destroy()
            except:
                messagebox.showerror("Error", "Invalid input.")

        ctk.CTkButton(dialog, text="Start", command=confirm, width=150, height=40, font=("Arial", 14)).pack(pady=10)

        self.wait_window(dialog)
        if result[0] is None:
            return

        self.main_menu_frame.destroy()
        self.main_menu_frame = None
        self.current_game_frame = CoinTossGameFrame(
            self,
            best_of=result[0],
            game_type="coin",
            timer_seconds=10
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()