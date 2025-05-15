class Card:
    """
    Represents a playing card with a suit and rank.
    """
    SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    
    def __init__(self, suit, rank):
        """
        Initialize a card with a suit and rank.
        
        Args:
            suit (str): The card suit (Hearts, Diamonds, Clubs, Spades)
            rank (str): The card rank (2-10, Jack, Queen, King, Ace)
        """
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
            
        self.suit = suit
        self.rank = rank
        
    def get_value(self):
        """
        Returns the blackjack value of the card.
        
        Returns:
            int: Card value (1-11 for Ace, 10 for face cards, numerical value otherwise)
        """
        if self.rank == "Ace":
            return 11  # Ace's value will be adjusted as needed in the Hand class
        elif self.rank in ["Jack", "Queen", "King"]:
            return 10
        else:
            return int(self.rank)
            
    def __str__(self):
        """String representation of the card."""
        return f"{self.rank} of {self.suit}"
    
    def __repr__(self):
        """Formal string representation of the card."""
        return f"Card('{self.suit}', '{self.rank}')"