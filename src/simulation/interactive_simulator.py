from src.simulation.simulator import BlackjackSimulator
from src.game.hand import Hand

class InteractiveSimulator(BlackjackSimulator):
    """
    An interactive version of the BlackjackSimulator that allows step-by-step
    simulation of hands with visualization capabilities.
    """
    
    def __init__(self, config=None):
        """Initialize the interactive simulator with the given configuration."""
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
            'house_edge': 0.0
        }
    
    def start_new_hand(self):
        """Start a new hand for interactive play."""
        self.current_phase = "init"
        self.current_player_hands = [Hand() for _ in range(self.config.num_players)]
        self.current_dealer_hand = Hand()
        self.current_dealer_hand.is_dealer_hand = True
        self.current_hand_result = None
        self.step_count = 0
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
            return {"error": "Not in dealer phase."}
            
        # Check if dealer should hit
        if self.dealer_strategy.should_hit(self.current_dealer_hand):
            self.current_dealer_hand.add_card(self.shoe.draw())
            self.step_count += 1
            
            # If dealer busts or hits 21, end the hand
            if self.current_dealer_hand.is_bust() or self.current_dealer_hand.get_value() >= 21:
                return self.complete_hand()
                
            return self.get_current_state()
        else:
            # Dealer stands
            return self.complete_hand()
    
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
        
        self.update_statistics(result, player_value, dealer_value)
        self.update_current_stats()
        
        self.hand_history.append({
            "player_hand": [str(card) for card in player_hand.cards],
            "dealer_hand": [str(card) for card in self.current_dealer_hand.cards],
            "result": result,
            "player_value": player_value,
            "dealer_value": dealer_value
        })
        
        self.current_phase = "result"
        return self.get_current_state()
    
    def update_current_stats(self):
        """Update the current real-time statistics."""
        if self.results['total_bets'] > 0:
            house_edge = -self.results['net_win_amount'] / self.results['total_bets'] * 100
        else:
            house_edge = 0.0
            
        self.current_stats = {
            'total_hands': self.results['total_bets'],
            'player_wins': self.results['player_wins'],
            'dealer_wins': self.results['dealer_wins'],
            'pushes': self.results['pushes'],
            'player_busts': self.results['player_busts'],
            'dealer_busts': self.results['dealer_busts'],
            'house_edge': house_edge
        }
    
    def get_current_state(self):
        """Get the current state of the interactive simulation."""
        return {
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
    
    def get_hand_history(self):
        """Get the history of hands played in this session."""
        return self.hand_history