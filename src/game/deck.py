import random
from src.game.card import Card

class Deck:
    """
    Represents a standard 52-card deck of playing cards.
    """
    
    def __init__(self):
        """Initialize a new deck of 52 cards in order."""
        self.cards = []
        self._build()
        
    def _build(self):
        """Build a new deck of 52 cards."""
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
        
    def shuffle(self):
        """Shuffle the deck of cards."""
        random.shuffle(self.cards)
        
    def draw(self):
        """
        Draw a card from the top of the deck.
        
        Returns:
            Card: The card drawn from the top of the deck
            
        Raises:
            IndexError: If the deck is empty
        """
        if not self.cards:
            raise IndexError("Cannot draw from an empty deck")
        return self.cards.pop(0)
    
    def __len__(self):
        """Return the number of cards in the deck."""
        return len(self.cards)
        
    def __str__(self):
        """String representation of the deck."""
        return f"Deck with {len(self.cards)} cards"


class Shoe:
    """
    Represents a shoe of multiple decks used in casino games.
    """
    
    def __init__(self, num_decks=6, reshuffle_cutoff=52):
        """
        Initialize a shoe with multiple decks.
        
        Args:
            num_decks (int): Number of decks to use in the shoe
            reshuffle_cutoff (int): Minimum number of cards before reshuffling
        """
        self.num_decks = num_decks
        self.reshuffle_cutoff = reshuffle_cutoff
        self.cards = []
        self.discard_pile = []
        self.continuous_shuffle = (reshuffle_cutoff == 0)
        self.build_and_shuffle()
        
    def build_and_shuffle(self):
        """Build and shuffle the shoe with the specified number of decks."""
        self.cards = []
        # Create multiple decks
        for _ in range(self.num_decks):
            deck = Deck()
            self.cards.extend(deck.cards)
        
        # Return any cards from discard pile if we're reshuffling
        if self.discard_pile:
            self.cards.extend(self.discard_pile)
            self.discard_pile = []
            
        # Shuffle all cards
        random.shuffle(self.cards)
        
    def draw(self):
        """
        Draw a card from the top of the shoe.
        
        Returns:
            Card: The card drawn from the top of the shoe
        """
        if len(self.cards) <= self.reshuffle_cutoff and not self.continuous_shuffle:
            self.build_and_shuffle()
            
        if not self.cards:
            raise IndexError("Cannot draw from an empty shoe")
            
        return self.cards.pop(0)
        
    def return_to_discard(self, cards):
        """
        Return used cards to the discard pile.
        
        Args:
            cards (list): List of Card objects to discard
        """
        self.discard_pile.extend(cards)
        
        if self.continuous_shuffle:
            # For continuous shuffle, immediately return cards to the shoe and reshuffle
            self.cards.extend(self.discard_pile)
            self.discard_pile = []
            random.shuffle(self.cards)
            
    def __len__(self):
        """Return the number of cards in the shoe."""
        return len(self.cards)
        
    def __str__(self):
        """String representation of the shoe."""
        return f"Shoe with {len(self.cards)} cards from {self.num_decks} decks"