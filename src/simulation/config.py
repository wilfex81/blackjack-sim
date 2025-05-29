class SimulationConfig:
    """
    Configuration settings for the blackjack simulation.
    """
    
    def __init__(self, 
                 num_hands=100000000,
                 num_decks=6,
                 player_hit_soft_17=False,
                 dealer_hit_soft_17=False,
                 reshuffle_cutoff=52,
                 commission_pct=5.0,
                 blackjack_payout=1.0,
                 num_players=1,
                 player_hit_rules=None,
                 commission_on_blackjack=True,
                 hit_against_blackjack=False,
                 sidebet_payout_mode="total",
                 sidebet_payouts=None):
        """
        Initialize simulation configuration.
        
        Args:
            num_hands (int): Number of hands to simulate
            num_decks (int): Number of decks in the shoe
            player_hit_soft_17 (bool): Whether the player hits on soft 17
            dealer_hit_soft_17 (bool): Whether the dealer hits on soft 17
            reshuffle_cutoff (int): Minimum cards before reshuffling (0 for continuous shuffle)
            commission_pct (float): Commission percentage taken on wins
            blackjack_payout (float): Payout ratio for blackjack
            num_players (int): Number of players at the table
            player_hit_rules (dict): Custom player hitting rules
            commission_on_blackjack (bool): Whether commission is applied to blackjack wins
            hit_against_blackjack (bool): Whether the player can hit against a dealer blackjack
            sidebet_payout_mode (str): Mode for sidebet payouts ("total" for hand totals or "cards" for card count)
            sidebet_payouts (dict): Payout multipliers for different push types
        """
        self.num_hands = num_hands
        self.num_decks = num_decks
        self.player_hit_soft_17 = player_hit_soft_17
        self.dealer_hit_soft_17 = dealer_hit_soft_17
        self.reshuffle_cutoff = reshuffle_cutoff
        self.commission_pct = commission_pct
        self.blackjack_payout = blackjack_payout
        self.num_players = num_players
        self.player_hit_rules = player_hit_rules or {}
        self.commission_on_blackjack = commission_on_blackjack
        self.hit_against_blackjack = hit_against_blackjack
        
        # Sidebet configuration
        self.sidebet_payout_mode = sidebet_payout_mode
        
        # Default sidebet payouts if none provided
        if sidebet_payouts is None:
            if sidebet_payout_mode == "total":
                self.sidebet_payouts = {
                    17: 1, 18: 1, 19: 1, 20: 1, 21: 1, 
                    'bust-bust': 1, 'blackjack-blackjack': 1
                }
            else:  # card count mode
                self.sidebet_payouts = {
                    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 
                    9: 1, 10: 1, 11: 1, '12+': 1
                }
        else:
            self.sidebet_payouts = sidebet_payouts
        
    def get_commission_multiplier(self):
        """
        Get the multiplier to apply to winnings after commission.
        
        Returns:
            float: The commission multiplier
        """
        return 1.0 - (self.commission_pct / 100.0)
        
    def __str__(self):
        """String representation of the configuration."""
        hit_rules_str = "Custom" if self.player_hit_rules else "Default"
        shuffle_type = "Continuous shuffle" if self.reshuffle_cutoff == 0 else f"Reshuffle at {self.reshuffle_cutoff} cards"
        
        sidebet_mode = "Hand Total" if self.sidebet_payout_mode == "total" else "Card Count"
        
        return (f"Simulation Config:\n"
                f"  Hands: {self.num_hands}\n"
                f"  Decks: {self.num_decks}\n"
                f"  Player hit soft 17: {self.player_hit_soft_17}\n"
                f"  Dealer hit soft 17: {self.dealer_hit_soft_17}\n"
                f"  Shuffle: {shuffle_type}\n"
                f"  Commission: {self.commission_pct}%\n"
                f"  Commission on blackjack: {self.commission_on_blackjack}\n"
                f"  Blackjack payout: {self.blackjack_payout}:1\n"
                f"  Players: {self.num_players}\n"
                f"  Hit rules: {hit_rules_str}\n"
                f"  Hit against dealer blackjack: {self.hit_against_blackjack}\n"
                f"  Sidebet payout mode: {sidebet_mode}\n"
                f"  Sidebet payouts: {self.sidebet_payouts}")
                
    def to_dict(self):
        """
        Convert configuration to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of configuration
        """
        serializable_hit_rules = {}
        for key, value in self.player_hit_rules.items():
            if isinstance(key, tuple):
                serializable_hit_rules[str(key)] = value
            else:
                serializable_hit_rules[key] = value
                
        return {
            'num_hands': self.num_hands,
            'num_decks': self.num_decks,
            'player_hit_soft_17': self.player_hit_soft_17,
            'dealer_hit_soft_17': self.dealer_hit_soft_17,
            'reshuffle_cutoff': self.reshuffle_cutoff,
            'commission_pct': self.commission_pct,
            'blackjack_payout': self.blackjack_payout,
            'num_players': self.num_players,
            'player_hit_rules': serializable_hit_rules,
            'commission_on_blackjack': self.commission_on_blackjack,
            'hit_against_blackjack': self.hit_against_blackjack,
            'sidebet_payout_mode': self.sidebet_payout_mode,
            'sidebet_payouts': self.sidebet_payouts,
            'shuffle_type': "Continuous shuffle" if self.reshuffle_cutoff == 0 else f"Reshuffle at {self.reshuffle_cutoff} cards"
        }