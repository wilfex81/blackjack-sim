#!/usr/bin/env python3

import argparse
import ast
import sys
import os

# Add the project root to the path so we can use absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.simulation.config import SimulationConfig
from src.simulation.simulator import BlackjackSimulator
from src.reporting.report_generator import ReportGenerator

def parse_hit_rules(rules_str):
    """
    Parse hit rules from string format into dictionary.
    
    Args:
        rules_str (str): String representation of hit rules
            Format: "hard:16,10:hit;soft:17:hit"
            means hit on hard 16 when dealer shows 10, and hit on soft 17
            
    Returns:
        dict: Dictionary mapping (player_total, dealer_card) to boolean hit decision
    """
    if not rules_str:
        return {}
        
    hit_rules = {}
    
    rule_parts = rules_str.strip().split(';')
    
    for rule in rule_parts:
        if not rule:
            continue
            
        # Parse rule components
        components = rule.strip().split(':')
        
        if len(components) < 3:
            print(f"Warning: Skipping invalid rule format: {rule}")
            continue
            
        hand_type = components[0].lower()  # "hard" or "soft"
        total = components[1]  # player total
        dealer_cards_action = components[2]  # dealer cards and action
        
        # Handle dealer cards and action
        if ',' in dealer_cards_action:
            dealer_card_str, action = dealer_cards_action.split(',')
            dealer_cards = [int(c) for c in dealer_card_str.split('|')]
        else:
            dealer_cards = list(range(2, 12))  # All possible dealer cards
            action = dealer_cards_action
            
        # Convert action to boolean
        should_hit = action.lower() in ('hit', 'h', 'true', 't', 'yes', 'y', '1')
        
        # Add rules to dictionary
        for dealer_card in dealer_cards:
            if hand_type == 'hard':
                hit_rules[(int(total), dealer_card)] = should_hit
            else:
                hit_rules[(f"soft {total}", dealer_card)] = should_hit
                
    return hit_rules

def main():
    parser = argparse.ArgumentParser(description="Blackjack Simulator")
    
    # Simulation parameters
    parser.add_argument('--num-hands', type=int, default=10000,
                        help='Number of hands to simulate (default: 10000)')
    parser.add_argument('--num-decks', type=int, default=6,
                        help='Number of decks in shoe (default: 6)')
    parser.add_argument('--player-hit-soft-17', action='store_true', default=False,
                        help='Player hits on soft 17')
    parser.add_argument('--dealer-hit-soft-17', action='store_true', default=False,
                        help='Dealer hits on soft 17')
    parser.add_argument('--continuous-shuffle', action='store_true', default=False,
                        help='Use continuous shuffle instead of traditional shoe')
    parser.add_argument('--reshuffle-cutoff', type=int, default=52,
                        help='Minimum cards before reshuffling (default: 52, 0 for continuous)')
    parser.add_argument('--commission', type=float, default=5.0,
                        help='Commission percentage taken on wins (default: 5.0)')
    parser.add_argument('--blackjack-payout', type=float, default=1.0,
                        help='Payout ratio for blackjack (default: 1.0)')
    parser.add_argument('--num-players', type=int, default=1,
                        help='Number of players at the table (default: 1)')
    parser.add_argument('--hit-rules', type=str, default="",
                        help='Custom hit rules (format: "hard:16,10:hit;soft:17:hit")')
    
    # Reporting options
    parser.add_argument('--summary-file', type=str,
                        help='Output file for summary report')
    parser.add_argument('--matrix-file', type=str,
                        help='Output file for outcome matrix CSV')
    parser.add_argument('--detailed-file', type=str,
                        help='Output file for detailed outcomes CSV')
    parser.add_argument('--config-file', type=str,
                        help='Output file for saving configuration')
    
    args = parser.parse_args()
    
    # Set reshuffle cutoff for continuous shuffle
    if args.continuous_shuffle:
        args.reshuffle_cutoff = 0
        
    # Parse hit rules
    hit_rules = parse_hit_rules(args.hit_rules)
    
    # Create configuration
    config = SimulationConfig(
        num_hands=args.num_hands,
        num_decks=args.num_decks,
        player_hit_soft_17=args.player_hit_soft_17,
        dealer_hit_soft_17=args.dealer_hit_soft_17,
        reshuffle_cutoff=args.reshuffle_cutoff,
        commission_pct=args.commission,
        blackjack_payout=args.blackjack_payout,
        num_players=args.num_players,
        player_hit_rules=hit_rules
    )
    
    # Print configuration
    print(config)
    print("\nStarting simulation...\n")
    
    # Run simulation
    simulator = BlackjackSimulator(config)
    results = simulator.run_simulation()
    
    # Print summary to console
    print("\n" + simulator.get_results_summary())
    
    # Generate reports
    report_gen = ReportGenerator(simulator)
    
    summary_path = report_gen.generate_summary_report(args.summary_file)
    matrix_path = report_gen.generate_outcome_matrix_csv(args.matrix_file)
    detailed_path = report_gen.generate_detailed_report(args.detailed_file)
    config_path = report_gen.save_config(args.config_file)
    
    print(f"\nSimulation complete. Reports generated in the 'results' directory.")

if __name__ == "__main__":
    main()