class Hand:
    """
    Represents a blackjack hand with cards and related operations.
    """
    
    def __init__(self):
        """Initialize an empty hand."""
        self.cards = []
        self.is_dealer_hand = False
        
    def add_card(self, card):
        """
        Add a card to the hand.
        
        Args:
            card (Card): The card to add to the hand
        """
        self.cards.append(card)
        
    def clear(self):
        """Clear all cards from the hand."""
        self.cards = []
        
    def get_value(self):
        """
        Calculate the total value of the hand, accounting for aces.
        
        Returns:
            int: The optimal value of the hand (highest possible without busting)
        """
        total_value = 0
        ace_count = 0
        
        # Sum up the value of all cards
        for card in self.cards:
            if card.rank == "Ace":
                ace_count += 1
                total_value += 11
            else:
                total_value += card.get_value()
        
        # Adjust for aces if necessary (convert from 11 to 1)
        while total_value > 21 and ace_count > 0:
            total_value -= 10  # Reduce value by 10 (11 - 1)
            ace_count -= 1
            
        return total_value
        
    def is_blackjack(self):
        """
        Check if the hand is a blackjack (21 with exactly 2 cards).
        
        Returns:
            bool: True if the hand is a blackjack, False otherwise
        """
        return len(self.cards) == 2 and self.get_value() == 21
        
    def is_bust(self):
        """
        Check if the hand has busted (value over 21).
        
        Returns:
            bool: True if the hand busted, False otherwise
        """
        return self.get_value() > 21
        
    def is_soft(self):
        """
        Check if the hand is a soft hand (contains an ace counted as 11).
        
        Returns:
            bool: True if the hand is soft, False otherwise
        """
        # Check each card for an ace
        has_ace = any(card.rank == "Ace" for card in self.cards)
        if not has_ace:
            return False
            
        # Calculate the value without one ace being 11
        non_ace_value = sum(card.get_value() for card in self.cards 
                          if card.rank != "Ace")
        ace_count = sum(1 for card in self.cards if card.rank == "Ace")
        
        # Add aces as 1 each, except possibly one as 11
        test_value = non_ace_value + ace_count
        
        # If we can add 10 more (making one ace=11) without busting, it's soft
        return test_value + 10 <= 21
    
    def get_dealer_up_card(self):
        """
        Get the dealer's up card (first card) if this is a dealer's hand.
        
        Returns:
            Card: The dealer's up card or None if this is not a dealer hand
            or if the hand is empty.
        """
        if self.is_dealer_hand and self.cards:
            return self.cards[0]
        return None
    
    def __str__(self):
        """String representation of the hand."""
        if not self.cards:
            return "Empty hand"
            
        card_list = ", ".join(str(card) for card in self.cards)
        value = self.get_value()
        soft = " (soft)" if self.is_soft() else ""
        
        return f"Hand [{value}{soft}]: {card_list}"