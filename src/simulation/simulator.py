from src.game.deck import Shoe
from src.game.hand import Hand
from src.strategy.dealer_strategy import DealerStrategy
from src.strategy.player_strategy import PlayerStrategy
from src.simulation.config import SimulationConfig
import time

class BlackjackSimulator:
    """
    Main blackjack simulation engine.
    """
    
    def __init__(self, config=None):
        """
        Initialize the blackjack simulator.
        
        Args:
            config (SimulationConfig, optional): Configuration settings
        """
        self.config = config or SimulationConfig()
        self.shoe = None
        self.dealer_strategy = None
        self.player_strategy = None
        self.results = None
        
    def setup(self):
        """
        Set up the simulator with fresh shoe and strategies.
        """
        # shoe
        self.shoe = Shoe(
            num_decks=self.config.num_decks,
            reshuffle_cutoff=self.config.reshuffle_cutoff
        )
        
        #strategies
        self.dealer_strategy = DealerStrategy(
            hit_soft_17=self.config.dealer_hit_soft_17
        )
        
        self.player_strategy = PlayerStrategy(
            stand_threshold=17,
            hit_soft_17=self.config.player_hit_soft_17,
            hit_rules=self.config.player_hit_rules
        )
        
        # Results tracking
        self.results = {
            'player_wins': 0,
            'dealer_wins': 0,
            'pushes': 0,
            'blackjacks': 0,
            'player_busts': 0,
            'dealer_busts': 0,
            'net_win_amount': 0,
            'total_bets': 0,
            'outcome_matrix': {},  # {(player_total, dealer_total): count}
            'outcome_details': {},  # {(player_total, dealer_total, result): count}
        }
        
    def deal_initial_cards(self, player_hands, dealer_hand):
        """
        Deal the initial two cards to each hand.
        
        Args:
            player_hands (list): List of player Hand objects
            dealer_hand (Hand): The dealer's hand
        """
        # Deal first card to each player
        for hand in player_hands:
            hand.add_card(self.shoe.draw())
            
        # Deal first card to dealer (face up)
        dealer_hand.add_card(self.shoe.draw())
        dealer_hand.is_dealer_hand = True
        
        # Deal second card to each player
        for hand in player_hands:
            hand.add_card(self.shoe.draw())
            
        # Deal second card to dealer (face down)
        dealer_hand.add_card(self.shoe.draw())
    
    def play_hand(self, player_hand, dealer_hand):
        """
        Play out a single hand of blackjack.
        
        Args:
            player_hand (Hand): The player's hand
            dealer_hand (Hand): The dealer's hand
            
        Returns:
            tuple: (result, player_final_value, dealer_final_value)
            where result is one of: "player_win", "dealer_win", "push"
        """
        # Check for blackjack first
        player_blackjack = player_hand.is_blackjack()
        dealer_blackjack = dealer_hand.is_blackjack()
        
        # If both have blackjack, it's a push
        if player_blackjack and dealer_blackjack:
            return "push", 21, 21
            
        # If dealer has blackjack, we win with 3:2 payout (no commission)
        if dealer_blackjack and not player_blackjack:
            return "dealer_blackjack", player_hand.get_value(), 21
            
        # If player has blackjack, we lose
        if player_blackjack and not dealer_blackjack:
            return "player_blackjack", 21, dealer_hand.get_value()
        
        # Get dealer's up card for strategy decisions
        dealer_up_card = dealer_hand.get_dealer_up_card()
        
        # Player draws cards
        while self.player_strategy.should_hit(player_hand, dealer_up_card):
            player_hand.add_card(self.shoe.draw())
            
        player_value = player_hand.get_value()
        player_busted = player_hand.is_bust()
        
        # Dealer draws cards
        while self.dealer_strategy.should_hit(dealer_hand):
            dealer_hand.add_card(self.shoe.draw())
            
        dealer_value = dealer_hand.get_value()
        dealer_busted = dealer_hand.is_bust()
        
        # In this variant, betting on dealer:
        # If dealer wins the hand, we win (since we bet on dealer)
        # If player wins the hand, we lose (since we bet on dealer)
        if player_busted and dealer_busted:
            return "push", player_value, dealer_value
        elif player_busted:
            return "dealer_win", player_value, dealer_value  # Regular win
        elif dealer_busted:
            return "player_win", player_value, dealer_value  # Loss
        elif player_value > dealer_value:
            return "player_win", player_value, dealer_value  # Loss
        elif dealer_value > player_value:
            return "dealer_win", player_value, dealer_value  # Regular win
        else:
            return "push", player_value, dealer_value
    
    def update_statistics(self, result, player_value, dealer_value, player_hand, dealer_hand):
        """
        Update simulation statistics.
        
        Args:
            result (str): Result of the hand ("dealer_win", "player_win", "push", "dealer_blackjack", "player_blackjack")
            player_value (int): Final value of the player's hand
            dealer_value (int): Final value of the dealer's hand
            player_hand (Hand): The player's hand
            dealer_hand (Hand): The dealer's hand
        """
        # Track win/loss/push counts and calculate payouts
        if result == "dealer_win":
            self.results['player_wins'] += 1  # We win when dealer wins
            # Regular win - apply commission
            win_amount = self.config.get_commission_multiplier()
            self.results['net_win_amount'] += win_amount
            
        elif result == "dealer_blackjack":
            self.results['player_wins'] += 1
            self.results['blackjacks'] += 1
            # Blackjack win - 3:2 payout with no commission
            win_amount = self.config.blackjack_payout
            self.results['net_win_amount'] += win_amount
            
        elif result in ["player_win", "player_blackjack"]:
            self.results['dealer_wins'] += 1  # We lose when player wins
            # Lose entire bet
            self.results['net_win_amount'] -= 1
            
        else:  # push
            self.results['pushes'] += 1
            
        # Update bust statistics
        if player_value > 21:
            self.results['player_busts'] += 1
        if dealer_value > 21:
            self.results['dealer_busts'] += 1
            
        # Track outcome frequencies
        player_key = min(player_value, 30)  # Cap at 30 for matrix
        dealer_key = min(dealer_value, 30)
        
        # Update outcome matrix
        outcome_key = (player_key, dealer_key)
        if outcome_key not in self.results['outcome_matrix']:
            self.results['outcome_matrix'][outcome_key] = 0
        self.results['outcome_matrix'][outcome_key] += 1
        
        # Update detailed outcomes
        detail_key = (player_key, dealer_key, result)
        if detail_key not in self.results['outcome_details']:
            self.results['outcome_details'][detail_key] = 0
        self.results['outcome_details'][detail_key] += 1
        
        # Count total hands
        self.results['total_bets'] += 1
    
    def run_simulation(self):
        """
        Run the configured number of blackjack hands.
        
        Returns:
            dict: Simulation results including win/loss statistics
        """
        self.setup()
        
        start_time = time.time()
        progress_interval = max(self.config.num_hands // 20, 1)  # Report progress ~20 times
        
        for hand_num in range(self.config.num_hands):
            # Initialize hands for this round
            player_hands = [Hand() for _ in range(self.config.num_players)]
            dealer_hand = Hand()
            dealer_hand.is_dealer_hand = True
            
            # Deal initial cards
            self.deal_initial_cards(player_hands, dealer_hand)
            
            # Process each player hand
            used_cards = []
            for player_hand in player_hands:
                result, player_value, dealer_value = self.play_hand(player_hand, dealer_hand)
                
                # Update stats
                self.update_statistics(result, player_value, dealer_value, player_hand, dealer_hand)
                
                # Collect used cards
                used_cards.extend(player_hand.cards)
            
            # Add dealer cards to used pile
            used_cards.extend(dealer_hand.cards)
            
            # Return cards to shoe
            self.shoe.return_to_discard(used_cards)
            
            # Progress updates
            if (hand_num + 1) % progress_interval == 0:
                progress_pct = 100 * (hand_num + 1) / self.config.num_hands
                elapsed = time.time() - start_time
                est_total = elapsed / (hand_num + 1) * self.config.num_hands
                remaining = est_total - elapsed
                
                print(f"Progress: {progress_pct:.1f}% ({hand_num + 1}/{self.config.num_hands}) "
                      f"- Est. time remaining: {remaining:.1f}s")
        
        # Calculate final house edge
        if self.results['total_bets'] > 0:
            total_hands = self.results['total_bets']
            blackjack_hands = self.results['blackjacks']
            
            # Calculate win rates excluding blackjacks
            reg_win_rate = (self.results['player_wins'] - blackjack_hands) / total_hands
            blackjack_rate = blackjack_hands / total_hands
            lose_rate = self.results['dealer_wins'] / total_hands
            
            # Expected value calculation:
            # Regular wins: Pay 1:1 with commission
            # Blackjack wins: Pay 3:2 with no commission
            # Losses: Lose entire bet
            commission_mult = 1.0 - (self.config.commission_pct / 100.0)
            expected_value = (reg_win_rate * commission_mult)  # Regular wins after commission
            expected_value += (blackjack_rate * self.config.blackjack_payout)  # Blackjack wins
            expected_value -= lose_rate  # Losses
            
            # House edge is negative of player expectation
            self.results['house_edge'] = -expected_value * 100
        else:
            self.results['house_edge'] = 0
            
        elapsed_time = time.time() - start_time
        self.results['simulation_time'] = elapsed_time
        
        return self.results

    def get_results_summary(self):
        """
        Get a formatted summary of the simulation results.
        
        Returns:
            str: Formatted results summary
        """
        if not self.results:
            return "No simulation results available."
        
        total_hands = self.results['total_bets']
        player_win_pct = 100 * self.results['player_wins'] / total_hands if total_hands > 0 else 0
        dealer_win_pct = 100 * self.results['dealer_wins'] / total_hands if total_hands > 0 else 0
        push_pct = 100 * self.results['pushes'] / total_hands if total_hands > 0 else 0
        
        summary = [
            f"Simulation Results Summary",
            f"=========================",
            f"",
            f"{self.config}",
            f"",
            f"Total hands: {total_hands}",
            f"Simulation time: {self.results['simulation_time']:.2f} seconds",
            f"",
            f"Player wins: {self.results['player_wins']} ({player_win_pct:.2f}%)",
            f"Dealer wins: {self.results['dealer_wins']} ({dealer_win_pct:.2f}%)",
            f"Pushes: {self.results['pushes']} ({push_pct:.2f}%)",
            f"",
            f"Player busts: {self.results['player_busts']} ({100 * self.results['player_busts'] / total_hands:.2f}%)",
            f"Dealer busts: {self.results['dealer_busts']} ({100 * self.results['dealer_busts'] / total_hands:.2f}%)",
            f"",
            f"House edge: {self.results['house_edge']:.2f}%"
        ]
        
        return "\n".join(summary)