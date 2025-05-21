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
        # Check for blackjack first - if either has blackjack, the hand ends immediately
        player_blackjack = player_hand.is_blackjack()
        dealer_blackjack = dealer_hand.is_blackjack()
        
        # If both have blackjack, it's a push
        if player_blackjack and dealer_blackjack:
            self.results['blackjacks'] += 1
            return "push", 21, 21
            
        # If player has blackjack, player hand > dealer hand
        if player_blackjack:
            self.results['blackjacks'] += 1
            return "dealer_win", 21, dealer_hand.get_value()  # In this variant, dealer wins means player loses
            
        # If dealer has blackjack, dealer hand > player hand
        if dealer_blackjack:
            self.results['blackjacks'] += 1
            # Mark this as a dealer blackjack win for the payout calculation
            return "player_win_blackjack", player_hand.get_value(), 21  # Special result code for blackjack payout
        
        # Get the dealer's up card for strategy decisions
        dealer_up_card = dealer_hand.get_dealer_up_card()
        
        # Player draws cards
        while self.player_strategy.should_hit(player_hand, dealer_up_card):
            player_hand.add_card(self.shoe.draw())
            
        # Remember player's final hand value
        player_value = player_hand.get_value()
        
        # If player busts, dealer doesn't need to play (custom rule: if both bust, it's a push)
        player_busted = player_hand.is_bust()
        
        # Dealer draws cards
        while self.dealer_strategy.should_hit(dealer_hand):
            dealer_hand.add_card(self.shoe.draw())
            
        # Calculate final results
        dealer_value = dealer_hand.get_value()
        dealer_busted = dealer_hand.is_bust()
        
        # In the custom variant, the player bets on the dealer winning
        # Player busts but dealer doesn't = dealer wins = player wins their bet
        # Player doesn't bust but dealer does = dealer loses = player loses their bet
        # Both bust or both don't bust with same value = push
        
        if player_busted and dealer_busted:
            result = "push"
        elif player_busted:
            result = "player_win"  # Player busts, dealer doesn't - player wins (betting on dealer)
        elif dealer_busted:
            result = "dealer_win"  # Dealer busts, player doesn't - dealer wins (player loses bet)
        elif player_value > dealer_value:
            result = "dealer_win"  # Player hand > dealer hand - dealer wins (player loses bet)
        elif dealer_value > player_value:
            result = "player_win"  # Dealer hand > player hand - player wins their bet
        else:
            result = "push"  # Equal values
            
        return result, player_value, dealer_value
    
    def update_statistics(self, result, player_value, dealer_value):
        """
        Update simulation statistics.
        
        Args:
            result (str): Result of the hand ("player_win", "dealer_win", "push", "player_win_blackjack")
            player_value (int): Final value of the player's hand
            dealer_value (int): Final value of the dealer's hand
        """
        # Update win/loss/push counts
        if result == "player_win" or result == "player_win_blackjack":
            self.results['player_wins'] += 1
            
            if result == "player_win_blackjack":
                # For blackjack payout, we need to calculate the net win amount
                # For a 1.5:1 blackjack payout, the player gets their bet back (1) plus 0.5
                # We need to normalize to the base bet amount of 1
                win_amount = (self.config.blackjack_payout - 1.0) + 1.0  # Adjust to actual net win amount
                
                # Apply commission only if commission_on_blackjack is enabled
                if self.config.commission_on_blackjack:
                    win_amount *= self.config.get_commission_multiplier()
            else:
                # Regular win with commission
                win_amount = self.config.get_commission_multiplier()
                
            self.results['net_win_amount'] += win_amount
        elif result == "dealer_win":
            self.results['dealer_wins'] += 1
            self.results['net_win_amount'] -= 1
        else:  # push
            self.results['pushes'] += 1
            
        # Update bust statistics
        if player_value > 21:
            self.results['player_busts'] += 1
        if dealer_value > 21:
            self.results['dealer_busts'] += 1
            
        # Track outcome matrix frequencies
        player_key = min(player_value, 30)  # Cap at 30 to keep matrix manageable
        dealer_key = min(dealer_value, 30)
        
        outcome_key = (player_key, dealer_key)
        if outcome_key not in self.results['outcome_matrix']:
            self.results['outcome_matrix'][outcome_key] = 0
        self.results['outcome_matrix'][outcome_key] += 1
        
        # Detailed outcomes - standardize result for storage
        result_for_storage = "player_win" if result == "player_win_blackjack" else result
        detail_key = (player_key, dealer_key, result_for_storage)
        if detail_key not in self.results['outcome_details']:
            self.results['outcome_details'][detail_key] = 0
        self.results['outcome_details'][detail_key] += 1
        
        # Increment total bets
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
                self.update_statistics(result, player_value, dealer_value)
                
                # Collect used cards for return to shoe
                used_cards.extend(player_hand.cards)
            
            # Add dealer cards to used pile
            used_cards.extend(dealer_hand.cards)
            
            # Return cards to shoe
            self.shoe.return_to_discard(used_cards)
            
            # Periodic progress update
            if (hand_num + 1) % progress_interval == 0:
                progress_pct = 100 * (hand_num + 1) / self.config.num_hands
                elapsed = time.time() - start_time
                est_total = elapsed / (hand_num + 1) * self.config.num_hands
                remaining = est_total - elapsed
                
                print(f"Progress: {progress_pct:.1f}% ({hand_num + 1}/{self.config.num_hands}) "
                      f"- Est. time remaining: {remaining:.1f}s")
        
        # Calculate final house edge
        if self.results['total_bets'] > 0:
            self.results['house_edge'] = -self.results['net_win_amount'] / self.results['total_bets']
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