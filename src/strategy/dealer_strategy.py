from src.strategy.base_strategy import BaseStrategy

class DealerStrategy(BaseStrategy):
    """
    Standard dealer strategy - hits until reaching a certain threshold.
    """
    
    def __init__(self, hit_soft_17=False):
        """
        Initialize the dealer strategy.
        
        Args:
            hit_soft_17 (bool): Whether the dealer hits on soft 17
        """
        super().__init__()
        self.hit_soft_17 = hit_soft_17
        
    def should_hit(self, player_hand, dealer_up_card=None):
        """
        Determine if the dealer should hit based on standard casino rules.
        Dealer hits until hard 17 or higher, or soft 18 or higher if hitting soft 17.
        
        Args:
            player_hand (Hand): The dealer's current hand
            dealer_up_card (Card, optional): Not used for dealer strategy
            
        Returns:
            bool: True if the dealer should hit, False otherwise
        """
        hand_value = player_hand.get_value()
        
        # Always hit if below 17
        if hand_value < 17:
            return True
            
        # Hit on soft 17 if that's the rule
        if hand_value == 17 and player_hand.is_soft() and self.hit_soft_17:
            return True
            
        # Stand in all other cases
        return False