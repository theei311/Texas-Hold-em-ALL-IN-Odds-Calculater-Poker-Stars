import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import random
from dataclasses import dataclass
from typing import List, Tuple
import time
import threading
import base64
import os
from treys import Card as TreysCard, Deck, Evaluator
from PIL import Image, ImageTk
import sys

@dataclass
class PokerCard:
    rank: str
    suit: str
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
        
    def to_treys_card(self):
        rank_map = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
                   '8': '8', '9': '9', 'T': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
        suit_map = {'h': 'h', 'd': 'd', 'c': 'c', 's': 's'}
        
        rank = rank_map.get(self.rank.upper())
        suit = suit_map.get(self.suit.lower())
        
        if rank and suit:
            return TreysCard.new(rank + suit)
        return None

class PokerOddsCalculator:
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title("Texas Hold'em ALL-IN Odds Calculator")
        self.root.geometry("600x500")
        self.set_icon()
        
        # Card ranks and suits
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.suits = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades
        
        # UI Elements
        self.setup_ui()
        
        # Initialize variables
        self.hole_cards = []
        self.simulation_thread = None
        self.simulation_running = False
        self.stop_simulation = False
        
    def setup_ui(self):
        # Configure styles for larger fonts
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Large.TLabel', font=('Arial', 12))
        style.configure('Large.TButton', font=('Arial', 12))
        style.configure('Large.TCombobox', font=('Arial', 12))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header frame with title and logo
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame, 
            text="Texas Hold'em ALL-IN Odds Calculator",
            style='Title.TLabel',
            anchor='center'
        )
        title_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Logo in top-right corner
        self.add_logo(header_frame)
        
        # Card selection frame
        card_frame = ttk.LabelFrame(main_frame, text="Select Your Hole Cards", padding=10)
        card_frame.pack(fill=tk.X, pady=10)
        
        # Card rank and suit options with full names
        self.rank_names = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
            '8': '8', '9': '9', 'T': '10', 'J': 'Jack', 'Q': 'Queen', 
            'K': 'King', 'A': 'Ace'
        }
        # Internal ranks used by the poker engine
        self.ranks = list(self.rank_names.keys())
        self.suit_symbols = ['♥', '♦', '♣', '♠']
        self.suit_names = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        
        # Card 1 selection
        card1_frame = ttk.Frame(card_frame)
        card1_frame.pack(fill=tk.X, pady=5)
        ttk.Label(card1_frame, text="Card 1:", style='Large.TLabel', width=8).pack(side=tk.LEFT, padx=5)
        
        # Card 1 Rank
        self.card1_rank = ttk.Combobox(
            card1_frame, 
            values=[self.rank_names[r] for r in self.ranks], 
            width=6, 
            state='readonly',
            style='Large.TCombobox'
        )
        self.card1_rank.current(0)
        self.card1_rank.pack(side=tk.LEFT, padx=5)
        self.card1_rank.bind('<Return>', lambda e: self.card1_suit.focus())
        self.card1_rank.bind('<KeyPress>', lambda e: self.on_keypress(e, self.card1_rank))
        
        # Card 1 Suit with larger font
        self.card1_suit = ttk.Combobox(
            card1_frame, 
            values=[f"{sym} {name}" for sym, name in zip(self.suit_symbols, self.suit_names)],
            width=10,
            state='readonly',
            style='Large.TCombobox'
        )
        self.card1_suit.current(0)
        self.card1_suit.pack(side=tk.LEFT, padx=5)
        self.card1_suit.bind('<Return>', lambda e: self.card2_rank.focus())
        self.card1_suit.bind('<KeyPress>', lambda e: self.on_keypress(e, self.card1_suit))
        
        # Card 2 selection
        card2_frame = ttk.Frame(card_frame)
        card2_frame.pack(fill=tk.X, pady=5)
        ttk.Label(card2_frame, text="Card 2:", style='Large.TLabel', width=8).pack(side=tk.LEFT, padx=5)
        
        # Card 2 Rank
        self.card2_rank = ttk.Combobox(
            card2_frame, 
            values=[self.rank_names[r] for r in self.ranks], 
            width=6, 
            state='readonly',
            style='Large.TCombobox'
        )
        self.card2_rank.current(1)
        self.card2_rank.pack(side=tk.LEFT, padx=5)
        self.card2_rank.bind('<Return>', lambda e: self.card2_suit.focus())
        self.card2_rank.bind('<KeyPress>', lambda e: self.on_keypress(e, self.card2_rank))
        
        # Card 2 Suit with larger font
        self.card2_suit = ttk.Combobox(
            card2_frame, 
            values=[f"{sym} {name}" for sym, name in zip(self.suit_symbols, self.suit_names)],
            width=10,
            state='readonly',
            style='Large.TCombobox'
        )
        self.card2_suit.current(1)
        self.card2_suit.pack(side=tk.LEFT, padx=5)
        self.card2_suit.bind('<Return>', lambda e: self.num_opponents.focus())
        self.card2_suit.bind('<KeyPress>', lambda e: self.on_keypress(e, self.card2_suit))
        
        # Number of opponents selection
        opponents_frame = ttk.Frame(card_frame)
        opponents_frame.pack(fill=tk.X, pady=5)
        ttk.Label(opponents_frame, text="Opponents:", style='Large.TLabel', width=8).pack(side=tk.LEFT, padx=5)
        self.num_opponents = tk.Spinbox(
            opponents_frame,
            from_=1,
            to=8,
            width=5,
            font=('Arial', 12),
            justify='center'
        )
        self.num_opponents.delete(0, tk.END)
        self.num_opponents.insert(0, '1')
        self.num_opponents.pack(side=tk.LEFT, padx=5)
        self.num_opponents.bind('<Return>', lambda e: self.start_simulation())
        
        # Calculate button
        self.calc_button = ttk.Button(main_frame, text="Calculate Odds", command=self.start_simulation)
        self.calc_button.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=5, fill=tk.X, padx=20)
        
        # Results
        self.result_var = tk.StringVar()
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        result_label = ttk.Label(result_frame, textvariable=self.result_var, justify=tk.LEFT, wraplength=500)
        result_label.pack(anchor='w')
        
        # Recommendation
        self.recommendation_var = tk.StringVar()
        recommendation_frame = ttk.Frame(main_frame)
        recommendation_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(recommendation_frame, text="Recommendation: ", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT)
        recommendation_label = ttk.Label(recommendation_frame, textvariable=self.recommendation_var, 
                                      font=('TkDefaultFont', 10, 'bold'), foreground='blue')
        recommendation_label.pack(side=tk.LEFT)
        
    def on_keypress(self, event, combobox):
        """Handle keypress for combobox quick selection"""
        key = event.char.upper()
        values = combobox['values']
        
        # Find first matching value
        for i, value in enumerate(values):
            if str(value).upper().startswith(key):
                combobox.current(i)
                combobox.event_generate('<<ComboboxSelected>>')
                return 'break'
        return None
    
    def get_rank_from_display(self, display_rank):
        """Convert displayed rank back to internal representation"""
        rank_map = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
            '8': '8', '9': '9', '10': 'T', 'Jack': 'J', 'Queen': 'Q',
            'King': 'K', 'Ace': 'A'
        }
        return rank_map.get(display_rank, '2')  # Default to '2' if not found

    def get_suit_from_display(self, display_suit):
        """Convert displayed suit back to internal representation"""
        suit_map = {
            '♥': 'h', 'Hearts': 'h',
            '♦': 'd', 'Diamonds': 'd',
            '♣': 'c', 'Clubs': 'c',
            '♠': 's', 'Spades': 's'
        }
        # Get the first character if it's in format "♥ Hearts"
        symbol = display_suit[0] if display_suit else 'h'
        return suit_map.get(symbol, 'h').lower()  # Default to hearts if not found

    def start_simulation(self):
        """Start the simulation in a separate thread"""
        if self.simulation_running:
            self.simulation_running = False
            self.calc_button.config(text="Calculate Odds")
            return
            
        self.simulation_running = True
        self.calc_button.config(text="Stop")
        self.progress['value'] = 0
        self.result_var.set("Running simulation...")
        self.recommendation_var.set("")
        
        try:
            # Get cards and number of opponents from UI
            card1 = f"{self.get_rank_from_display(self.card1_rank.get())}{self.get_suit_from_display(self.card1_suit.get())}"
            card2 = f"{self.get_rank_from_display(self.card2_rank.get())}{self.get_suit_from_display(self.card2_suit.get())}"
            
            if not card1 or not card2:
                raise ValueError("Invalid card selection")
                
            num_opponents = int(self.num_opponents.get())
            if num_opponents < 1 or num_opponents > 8:
                num_opponents = 1
                
            # Start simulation in a separate thread
            self.simulation_thread = threading.Thread(
                target=self.run_simulation,
                args=([card1, card2], 1500, num_opponents),  # 1500 simulations for fast results
                daemon=True
            )
            self.simulation_thread.start()
            
        except Exception as e:
            self.result_var.set(f"Error: {str(e)}")
            self.simulation_running = False
            self.calc_button.config(text="Calculate Odds")
        
    def run_simulation(self, hole_cards, num_simulations, num_opponents):
        """Run the simulation and update the UI"""
        wins = 0
        ties = 0
        total = 0
        
        try:
            for i in range(num_simulations):
                if not self.simulation_running:
                    break
                    
                result = self.simulate_hand(hole_cards, num_opponents)
                
                if result == "win":
                    wins += 1
                elif result == "tie":
                    ties += 1
                    
                total += 1
                
                # Update progress every 50 simulations for better performance
                if i % 50 == 0 or i == num_simulations - 1:
                    win_pct = (wins / total * 100) if total > 0 else 0
                    tie_pct = (ties / total * 100) if total > 0 else 0
                    
                    self.root.after(0, self.update_results, win_pct, tie_pct, i + 1, num_simulations, num_opponents)
            
            # Final update
            win_pct = (wins / total * 100) if total > 0 else 0
            tie_pct = (ties / total * 100) if total > 0 else 0
            self.root.after(0, self.update_results, win_pct, tie_pct, total, num_simulations, num_opponents, final=True)
            
        except Exception as e:
            self.root.after(0, lambda: self.result_var.set(f"Error in simulation: {str(e)}"))
            
        finally:
            self.simulation_running = False
            self.root.after(0, lambda: self.calc_button.config(text="Calculate Odds"))
        
    def update_results(self, win_pct, tie_pct, current, total, num_opponents, final=False):
        """Update the results in the UI"""
        try:
            loss_pct = max(0, 100 - win_pct - tie_pct)  # Ensure we don't show negative loss percentage
            
            if final:
                result_text = (
                    f"=== Final Results ===\n"
                    f"Against {num_opponents} opponent{'s' if num_opponents > 1 else ''}:\n"
                    f"Win: {win_pct:.1f}%\n"
                    f"Tie: {tie_pct:.1f}%\n"
                    f"Loss: {loss_pct:.1f}%\n"
                    f"Equity (win + tie/2): {win_pct + tie_pct/2:.1f}%\n"
                    f"Simulations: {current}/{total}"
                )
                self.result_var.set(result_text)
                
                # Calculate equity (win % + tie%/2) for better decision making
                equity = win_pct + (tie_pct / 2)
                
                # Fixed threshold at 53% equity for calling/raising
                call_threshold = 53.0
                
                # Generate simple recommendation
                if equity >= call_threshold:
                    # For very strong hands, suggest raising
                    if equity >= 65.0:  # Strongly ahead
                        action = "RAISE"
                        reasoning = "Strong hand with {:.1f}% equity".format(equity)
                    else:  # Slight favorite
                        action = "CALL"
                        reasoning = "Positive expectation with {:.1f}% equity".format(equity)
                    
                    self.recommendation_var.set(
                        f"CALL/RAISE\n"
                        f"Equity: {equity:.1f}% | Win: {win_pct:.1f}% | Tie: {tie_pct:.1f}%\n"
                        f"{action} - {reasoning}. Against {num_opponents} opponent{'s' if num_opponents > 1 else ''}."
                    )
                else:
                    self.recommendation_var.set(
                        f"FOLD\n"
                        f"Equity: {equity:.1f}% | Win: {win_pct:.1f}% | Tie: {tie_pct:.1f}%\n"
                        f"FOLD - Only {equity:.1f}% equity (need 53%+) against {num_opponents} opponent{'s' if num_opponents > 1 else ''}."
                    )
            else:
                result_text = (
                    f"Running simulation...\n"
                    f"Against {num_opponents} opponent{'s' if num_opponents > 1 else ''}:\n"
                    f"Win: {win_pct:.1f}%\n"
                    f"Tie: {tie_pct:.1f}%\n"
                    f"Loss: {loss_pct:.1f}%\n"
                    f"Simulations: {current}/{total}"
                )
                self.result_var.set(result_text)
            
            # Update progress bar
            progress_value = (current / total) * 100 if total > 0 else 0
            self.progress['value'] = progress_value
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error updating results: {e}")
        
    def simulate_hand(self, hole_cards: List[str], num_opponents: int) -> str:
        try:
            evaluator = Evaluator()
            deck = Deck()
            
            # Convert our cards to treys format
            our_cards = []
            for card in hole_cards:
                if len(card) != 2:
                    continue
                rank = card[0].upper()
                suit = card[1].lower()
                try:
                    card_int = TreysCard.new(rank + suit)
                    our_cards.append(card_int)
                except Exception as e:
                    print(f"Error converting card {card}: {e}")
                    continue
            
            if len(our_cards) != 2:
                print("Error: Need exactly 2 valid hole cards")
                return "lose"
            
            # Remove our cards from the deck
            deck.cards = [c for c in deck.cards if c not in our_cards]
            
            # Check if we have enough cards for board and opponents
            if len(deck.cards) < (5 + num_opponents * 2):
                print("Error: Not enough cards in deck")
                return "tie"
            
            # Deal the board (5 community cards)
            board = deck.draw(5)
            
            # Evaluate our hand
            our_score = evaluator.evaluate(our_cards, board)
            
            # Track results against all opponents
            best_opponent_score = 9999  # Lower is better in treys
            
            # Simulate each opponent's hand
            for _ in range(num_opponents):
                if len(deck.cards) < 2:
                    break
                    
                # Deal 2 cards to opponent
                opp_cards = [deck.draw(1)[0], deck.draw(1)[0]]
                
                # Evaluate opponent's hand
                opp_score = evaluator.evaluate(opp_cards, board)
                
                # Track the best (lowest) score among opponents
                if opp_score < best_opponent_score:
                    best_opponent_score = opp_score
                
                # Return cards to deck for next simulation
                deck.cards.extend(opp_cards)
            
            # Compare our hand to the best opponent's hand
            if our_score < best_opponent_score:
                return "win"
            elif our_score > best_opponent_score:
                return "lose"
            else:
                return "tie"
            
        except Exception as e:
            print(f"Error in simulate_hand: {e}")
            import traceback
            traceback.print_exc()
            return "lose"  # Default to lose on error
        
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def add_logo(self, parent_frame):
        """Add logo to the GUI in top-right corner"""
        try:
            logo_path = self.get_resource_path('transparent logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((50, 50), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                logo_label = tk.Label(parent_frame, image=self.logo_photo, bg=parent_frame.cget('background'))
                logo_label.pack(side=tk.RIGHT, padx=10)
        except Exception as e:
            print(f"Could not load logo: {e}")
    
    def set_icon(self):
        """Set the application icon using transparent logo.png"""
        try:
            logo_path = self.get_resource_path('transparent logo.png')
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                icon_sizes = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]
                img.save('temp_icon.ico', format='ICO', sizes=icon_sizes)
                self.root.iconbitmap(default='temp_icon.ico')
            else:
                icon_path = self.get_resource_path('icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Could not set application icon: {e}")

    def get_hand_rank_value(self, rank_name):
        # Convert treys rank class to a numerical value for comparison
        rank_order = {
            'High Card': 0,
            'One Pair': 1,
            'Two Pair': 2,
            'Three of a Kind': 3,
            'Straight': 4,
            'Flush': 5,
            'Full House': 6,
            'Four of a Kind': 7,
            'Straight Flush': 8,
            'Royal Flush': 9
        }
        return rank_order.get(rank_name, 0)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PokerOddsCalculator()
    app.run()
