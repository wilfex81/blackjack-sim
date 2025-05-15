class BaseStrategy:
    """
    Base class for blackjack playing strategies.
    """
    
    def __init__(self):
        """Initialize the strategy."""
        pass
        
    def should_hit(self, player_hand, dealer_up_card=None):
        """
        Determine if the player should hit based on their hand and dealer's up card.
        
        Args:
            player_hand (Hand): The player's current hand
            dealer_up_card (Card, optional): The dealer's up card
            
        Returns:
            bool: True if the player should hit, False otherwise
        """
        raise NotImplementedError("Subclasses must implement should_hit()")