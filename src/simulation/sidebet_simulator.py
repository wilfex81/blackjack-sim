from src.simulation.simulator import BlackjackSimulator
from src.game.hand import Hand
import time

class SidebetSimulator(BlackjackSimulator):
    """
    A simulator for the push sidebet which pays when the player and dealer push (tie).
    """
    
    def __init__(self, config=None):
        """
        Initialize the sidebet simulator.
        
        Args:
            config (SimulationConfig, optional): Configuration settings
        """
        super().__init__(config)
    
    def setup(self):
        """
        Set up the simulator with fresh shoe, strategies, and results tracking.
        """
        super().setup()
        
        # Add sidebet-specific results tracking
        self.results.update({
            'total_pushes': 0,
            'pushes_by_value': {17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 'bust': 0, 'blackjack': 0},
            'pushes_by_card_count': {4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, '12+': 0},
            'pushes_detail_matrix': {},  # Detailed breakdown: {(value_type, card_count): count}
            'sidebet_wins': 0,
            'sidebet_payouts': 0,
            'sidebet_edge': 0,
            'player_blackjacks': 0,
            'dealer_blackjacks': 0
        })
    
    def play_hand(self, player_hand, dealer_hand):
        """
        Play out a single hand of blackjack, focusing on push outcomes.
        
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
        
        # Track blackjacks
        if player_blackjack:
            self.results['player_blackjacks'] += 1
        if dealer_blackjack:
            self.results['dealer_blackjacks'] += 1
        
        # If both have blackjack, it's a push
        if player_blackjack and dealer_blackjack:
            return "push", 21, 21
            
        # If dealer has blackjack and player doesn't, dealer wins
        if dealer_blackjack and not player_blackjack:
            # Allow player to hit against a dealer blackjack if configured
            if self.config.hit_against_blackjack:
                dealer_up_card = dealer_hand.get_dealer_up_card()
                while self.player_strategy.should_hit(player_hand, dealer_up_card):
                    player_hand.add_card(self.shoe.draw())
                player_value = player_hand.get_value()
                return "dealer_win", player_value, 21
            else:
                return "dealer_win", player_hand.get_value(), 21
            
        # If player has blackjack and dealer doesn't, player wins
        if player_blackjack and not dealer_blackjack:
            return "player_win", 21, dealer_hand.get_value()
        
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
        
        # Determine outcome
        if player_busted and dealer_busted:
            return "push", player_value, dealer_value
        elif player_busted:
            return "dealer_win", player_value, dealer_value
        elif dealer_busted:
            return "player_win", player_value, dealer_value
        elif player_value > dealer_value:
            return "player_win", player_value, dealer_value
        elif dealer_value > player_value:
            return "dealer_win", player_value, dealer_value
        else:
            return "push", player_value, dealer_value
    
    def update_statistics(self, result, player_value, dealer_value, player_hand, dealer_hand):
        """
        Update simulation statistics.
        
        Args:
            result (str): Result of the hand ("dealer_win", "player_win", "push")
            player_value (int): Final value of the player's hand
            dealer_value (int): Final value of the dealer's hand
            player_hand (Hand): The player's hand
            dealer_hand (Hand): The dealer's hand
        """
        super().update_statistics(result, player_value, dealer_value, player_hand, dealer_hand)
        
        # Track push-specific statistics for the sidebet
        if result == "push":
            self.results['total_pushes'] += 1
            
            # Determine value type for categorization
            value_type = None
            if player_value > 21:  # Both busted
                value_type = 'bust'
                self.results['pushes_by_value']['bust'] += 1
            elif player_hand.is_blackjack() and dealer_hand.is_blackjack():
                value_type = 'blackjack'
                self.results['pushes_by_value']['blackjack'] += 1
            elif player_value == 21:
                # Differentiate between blackjack and non-blackjack 21
                if player_hand.is_blackjack() or dealer_hand.is_blackjack():
                    # This is a case where one side has blackjack and other has 21
                    value_type = '21_with_bj'
                else:
                    value_type = 21
                self.results['pushes_by_value'][21] += 1
            elif player_value in self.results['pushes_by_value']:
                value_type = player_value
                self.results['pushes_by_value'][player_value] += 1
                
            # Track pushes by card count
            total_cards = len(player_hand.cards) + len(dealer_hand.cards)
            card_count_key = '12+' if total_cards >= 12 else total_cards
            if total_cards >= 12:
                self.results['pushes_by_card_count']['12+'] += 1
            elif total_cards in self.results['pushes_by_card_count']:
                self.results['pushes_by_card_count'][total_cards] += 1
                
            # Update the detailed matrix
            matrix_key = (value_type, card_count_key)
            if matrix_key not in self.results['pushes_detail_matrix']:
                self.results['pushes_detail_matrix'][matrix_key] = 0
            self.results['pushes_detail_matrix'][matrix_key] += 1
                
            # Calculate sidebet payout based on configuration
            payout_multiplier = 0
            if self.config.sidebet_payout_mode == "total":
                # Payout based on total value
                if player_value > 21:  # Both busted
                    payout_multiplier = self.config.sidebet_payouts.get('bust-bust', 0)
                elif player_hand.is_blackjack() and dealer_hand.is_blackjack():
                    payout_multiplier = self.config.sidebet_payouts.get('blackjack-blackjack', 0)
                else:
                    payout_multiplier = self.config.sidebet_payouts.get(player_value, 0)
            else:  # card count mode
                # Payout based on total cards
                if total_cards >= 12:
                    payout_multiplier = self.config.sidebet_payouts.get('12+', 0)
                else:
                    payout_multiplier = self.config.sidebet_payouts.get(total_cards, 0)
            
            # Update sidebet stats
            self.results['sidebet_wins'] += 1
            self.results['sidebet_payouts'] += payout_multiplier
        
        # Calculate sidebet edge after each hand
        if self.results['total_bets'] > 0:
            self.results['sidebet_edge'] = (self.results['sidebet_payouts'] - self.results['total_bets']) / self.results['total_bets'] * 100
    
    def run_simulation(self):
        """
        Run the simulation for the specified number of hands.
        
        Returns:
            dict: The simulation results
        """
        self.setup()
        
        start_time = time.time()
        
        for _ in range(self.config.num_hands):
            # Reshuffle if needed
            if self.config.reshuffle_cutoff > 0 and len(self.shoe) < self.config.reshuffle_cutoff:
                self.shoe.build_and_shuffle()
                
            # Create player and dealer hands
            player_hand = Hand()
            dealer_hand = Hand()
            dealer_hand.is_dealer_hand = True
            
            # Deal initial cards
            self.deal_initial_cards([player_hand], dealer_hand)
            
            # Play the hand
            result, player_value, dealer_value = self.play_hand(player_hand, dealer_hand)
            
            # Update statistics
            self.update_statistics(result, player_value, dealer_value, player_hand, dealer_hand)
            
            if self.results['total_bets'] % 1000000 == 0:
                print(f"Simulated {self.results['total_bets']} hands...")
                
        end_time = time.time()
        simulation_time = end_time - start_time
        
        # Add simulation time to results
        self.results['simulation_time'] = simulation_time
        
        # Calculate house edge for main bet
        if self.results['total_bets'] > 0:
            self.results['house_edge'] = -self.results['net_win_amount'] / self.results['total_bets'] * 100
            
        return self.results


class InteractiveSidebetSimulator(SidebetSimulator):
    """
    An interactive version of the SidebetSimulator for hand-by-hand simulation.
    """
    
    def __init__(self, config=None):
        """Initialize the interactive sidebet simulator."""
        super().__init__(config)
        self.current_player_hands = []
        self.current_dealer_hand = None
        self.current_phase = "init"  # Phases: init, deal, player_turn, dealer_turn, result
        self.hand_history = []
        self.current_hand_result = None
        self.step_count = 0
        self.current_stats = {
            'total_hands': 0,
            'player_wins': 0,
            'dealer_wins': 0, 
            'pushes': 0,
            'player_busts': 0,
            'dealer_busts': 0,
            'house_edge': None,
            'sidebet_stats': {
                'total_pushes': 0,
                'by_value': {},
                'by_cards': {},
                'edge': None
            }
        }
    
    def start_new_hand(self, player_initial_cards=None, dealer_initial_cards=None):
        """
        Start a new hand for interactive play with optional initial cards.
        
        Args:
            player_initial_cards (list, optional): Initial cards for the player
            dealer_initial_cards (list, optional): Initial cards for the dealer
        """
        self.current_phase = "init"
        self.current_player_hands = [Hand() for _ in range(self.config.num_players)]
        self.current_dealer_hand = Hand()
        self.current_dealer_hand.is_dealer_hand = True
        self.current_hand_result = None
        self.step_count = 0
        
        # If initial cards are provided, set them up
        if player_initial_cards and dealer_initial_cards:
            player_hand = self.current_player_hands[0]
            for card in player_initial_cards:
                player_hand.add_card(card)
                
            for card in dealer_initial_cards:
                self.current_dealer_hand.add_card(card)
                
            self.current_phase = "player_turn"
            self.step_count += 1
            
            # If either side has blackjack, complete the hand immediately
            if any(hand.is_blackjack() for hand in self.current_player_hands) or self.current_dealer_hand.is_blackjack():
                return self.complete_hand()
        
        return self.get_current_state()
    
    def deal_cards(self):
        """Deal the initial cards for the current hand."""
        if self.current_phase != "init":
            return {"error": "Cannot deal cards now. Wrong phase."}
            
        self.deal_initial_cards(self.current_player_hands, self.current_dealer_hand)
        self.current_phase = "player_turn"
        self.step_count += 1
        
        # If either side has blackjack, complete the hand immediately
        if any(hand.is_blackjack() for hand in self.current_player_hands) or self.current_dealer_hand.is_blackjack():
            return self.complete_hand()
        
        return self.get_current_state()
    
    def player_hit(self):
        """Execute a player hit action."""
        if self.current_phase != "player_turn":
            return {"error": "Cannot hit now. Wrong phase."}
            
        player_hand = self.current_player_hands[0]
        dealer_up_card = self.current_dealer_hand.get_dealer_up_card()
        
        # Check if player should hit according to strategy
        if self.player_strategy.should_hit(player_hand, dealer_up_card):
            player_hand.add_card(self.shoe.draw())
            self.step_count += 1
            
            # Check if player busted or reached 21
            if player_hand.is_bust() or player_hand.get_value() == 21:
                return self.dealer_turn()
                
            return self.get_current_state()
        else:
            # Player should stand according to strategy
            return self.dealer_turn()
    
    def player_stand(self):
        """Execute a player stand action."""
        if self.current_phase != "player_turn":
            return {"error": "Cannot stand now. Wrong phase."}
            
        return self.dealer_turn()
    
    def dealer_turn(self):
        """Execute the dealer's turn."""
        if self.current_phase != "player_turn":
            return {"error": "Cannot start dealer turn now. Wrong phase."}
            
        self.current_phase = "dealer_turn"
        return self.dealer_step()
    
    def dealer_step(self):
        """Execute a single step in the dealer's turn."""
        if self.current_phase != "dealer_turn":
            return {"error": "Not in dealer turn phase."}
            
        if self.dealer_strategy.should_hit(self.current_dealer_hand):
            self.current_dealer_hand.add_card(self.shoe.draw())
            self.step_count += 1
            
            # Check if dealer is done
            if not self.dealer_strategy.should_hit(self.current_dealer_hand):
                return self.complete_hand()
                
            return self.get_current_state()
        else:
            # Dealer is done
            return self.complete_hand()
    
    def update_current_stats(self):
        """Update the current real-time statistics."""
        total_hands = self.results['total_bets']
        
        if total_hands > 0:
            # Calculate house edge from net win amount
            house_edge = -self.results['net_win_amount'] / total_hands
        else:
            house_edge = None

        self.current_stats = {
            'total_hands': total_hands,
            'player_wins': self.results['player_wins'],
            'dealer_wins': self.results['dealer_wins'],
            'pushes': self.results['pushes'],
            'player_busts': self.results['player_busts'],
            'dealer_busts': self.results['dealer_busts'],
            'house_edge': house_edge,
            'player_blackjacks': self.results.get('player_blackjacks', 0),
            'dealer_blackjacks': self.results.get('dealer_blackjacks', 0)
        }
        
        # Add sidebet-specific stats
        if self.results['total_bets'] > 0:
            self.current_stats['sidebet_stats'] = {
                'total_pushes': self.results['total_pushes'],
                'by_value': self.results['pushes_by_value'],
                'by_cards': self.results['pushes_by_card_count'],
                'edge': self.results['sidebet_edge']
            }
    
    def get_current_state(self):
        """Get the current state of the interactive simulation."""
        state = {
            "phase": self.current_phase,
            "step": self.step_count,
            "player_hands": [{
                "cards": [str(card) for card in hand.cards],
                "value": hand.get_value(),
                "is_soft": hand.is_soft(),
                "is_blackjack": hand.is_blackjack(),
                "is_bust": hand.is_bust()
            } for hand in self.current_player_hands],
            "dealer_hand": {
                "cards": [str(card) for card in self.current_dealer_hand.cards],
                "value": self.current_dealer_hand.get_value(),
                "is_soft": self.current_dealer_hand.is_soft(),
                "is_blackjack": self.current_dealer_hand.is_blackjack(),
                "is_bust": self.current_dealer_hand.is_bust(),
                "visible_card": str(self.current_dealer_hand.get_dealer_up_card()) if self.current_dealer_hand.get_dealer_up_card() else None
            } if self.current_dealer_hand else None,
            "result": self.current_hand_result,
            "stats": self.current_stats,
            "history_length": len(self.hand_history)
        }
        
        # Add sidebet-specific state information
        if self.current_phase == "result" and self.current_hand_result and self.current_hand_result["result"] == "push":
            player_hand = self.current_player_hands[0]
            dealer_hand = self.current_dealer_hand
            total_cards = len(player_hand.cards) + len(dealer_hand.cards)
            
            state["sidebet_result"] = {
                "is_push": True,
                "value": self.current_hand_result["player_value"],
                "total_cards": total_cards,
                "is_blackjack_push": player_hand.is_blackjack() and dealer_hand.is_blackjack(),
                "is_bust_push": player_hand.is_bust() and dealer_hand.is_bust()
            }
        else:
            state["sidebet_result"] = {"is_push": False}
        
        return state
        
    def complete_hand(self):
        """Complete the current hand and determine the result."""
        if self.current_phase not in ["player_turn", "dealer_turn"]:
            return {"error": "Hand cannot be completed now."}
            
        player_hand = self.current_player_hands[0]
        
        result, player_value, dealer_value = self.play_hand(player_hand, self.current_dealer_hand)
        
        self.current_hand_result = {
            "result": result,
            "player_value": player_value,
            "dealer_value": dealer_value,
            "player_busted": player_hand.is_bust(),
            "dealer_busted": self.current_dealer_hand.is_bust(),
            "display_result": "Player Win" if result == "player_win" else ("Dealer Win" if result == "dealer_win" else "Push")
        }
        
        self.update_statistics(result, player_value, dealer_value, player_hand, self.current_dealer_hand)
        self.update_current_stats()
        
        self.hand_history.append({
            "player_hand": [str(card) for card in player_hand.cards],
            "dealer_hand": [str(card) for card in self.current_dealer_hand.cards],
            "result": result,
            "player_value": player_value,
            "dealer_value": dealer_value,
            "total_cards": len(player_hand.cards) + len(self.current_dealer_hand.cards)
        })
        
        self.current_phase = "result"
        return self.get_current_state()
    
    def get_hand_history(self):
        """Get the history of hands played in this session."""
        return self.hand_history
