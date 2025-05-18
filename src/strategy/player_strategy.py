from src.strategy.base_strategy import BaseStrategy

class PlayerStrategy(BaseStrategy):
    """
    Configurable player strategy for blackjack simulation.
    """
    
    def __init__(self, stand_threshold=17, hit_soft_17=False, hit_rules=None):
        """
        Initialize the player strategy with configurable rules.
        
        Args:
            stand_threshold (int): The value at which to stand (default 17)
            hit_soft_17 (bool): Whether to hit on soft 17
            hit_rules (dict, optional): A dict mapping specific scenarios to hit decisions
                Format: {(player_total, dealer_up_card_value): should_hit_bool}
                Example: {(16, 10): True}  # Hit on 16 when dealer shows 10
                If player_total is "soft X", it means a soft hand with value X
        """
        super().__init__()
        self.stand_threshold = stand_threshold
        self.hit_soft_17 = hit_soft_17
        self.hit_rules = hit_rules or {}
        
    def should_hit(self, player_hand, dealer_up_card=None):
        """
        Determine if the player should hit based on configured rules.
        
        Args:
            player_hand (Hand): The player's current hand
            dealer_up_card (Card, optional): The dealer's up card
            
        Returns:
            bool: True if the player should hit, False otherwise
        """
        hand_value = player_hand.get_value()
        
        # Check for specific rules for this scenario
        if dealer_up_card and self.hit_rules:
            dealer_value = dealer_up_card.get_value()
            
            # Check for hard hand specific rule
            if not player_hand.is_soft() and (hand_value, dealer_value) in self.hit_rules:
                return self.hit_rules[(hand_value, dealer_value)]
                
            # Check for soft hand specific rule
            if player_hand.is_soft() and (f"soft {hand_value}", dealer_value) in self.hit_rules:
                return self.hit_rules[(f"soft {hand_value}", dealer_value)]
        
        # Default rules if no specific rule matches
        if hand_value < self.stand_threshold:
            return True
            
        if hand_value == 17 and player_hand.is_soft() and self.hit_soft_17:
            return True
            
        return False