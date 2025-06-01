#!/usr/bin/env python
import argparse
import os
import json
import sys
import time
import csv
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.config import SimulationConfig
from src.simulation.sidebet_simulator import SidebetSimulator
from src.reporting.report_generator import ReportGenerator

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run blackjack sidebet simulation from the command line')
    
    # Basic configuration
    parser.add_argument('--num-hands', type=int, default=10000, help='Number of hands to simulate')
    parser.add_argument('--num-decks', type=int, default=6, help='Number of decks')
    parser.add_argument('--num-players', type=int, default=1, help='Number of players at the table')
    parser.add_argument('--player-hits-soft-17', action='store_true', help='Player hits on soft 17')
    parser.add_argument('--dealer-hits-soft-17', action='store_true', help='Dealer hits on soft 17')
    parser.add_argument('--reshuffle-threshold', type=int, default=52, help='Reshuffle threshold (cards remaining)')
    parser.add_argument('--continuous-shuffle', action='store_true', help='Use continuous shuffle')
    parser.add_argument('--hit-against-blackjack', action='store_true', help='Allow player to hit against dealer blackjack')
    
    # Sidebet specific options
    parser.add_argument('--payout-mode', choices=['total', 'cards'], default='total',
                        help='Payout based on hand total or card count')
    
    # Payout configuration for hand totals
    parser.add_argument('--payout-17', type=float, default=1.0, help='Payout for 17 vs 17')
    parser.add_argument('--payout-18', type=float, default=1.0, help='Payout for 18 vs 18')
    parser.add_argument('--payout-19', type=float, default=1.0, help='Payout for 19 vs 19')
    parser.add_argument('--payout-20', type=float, default=1.0, help='Payout for 20 vs 20')
    parser.add_argument('--payout-21', type=float, default=1.0, help='Payout for 21 vs 21')
    parser.add_argument('--payout-bust-bust', type=float, default=1.0, help='Payout for bust vs bust')
    parser.add_argument('--payout-bj-bj', type=float, default=1.0, help='Payout for blackjack vs blackjack')
    
    # Payout configuration for card counts
    parser.add_argument('--payout-4-cards', type=float, default=1.0, help='Payout for 4 cards')
    parser.add_argument('--payout-5-cards', type=float, default=1.0, help='Payout for 5 cards')
    parser.add_argument('--payout-6-cards', type=float, default=1.0, help='Payout for 6 cards')
    parser.add_argument('--payout-7-cards', type=float, default=1.0, help='Payout for 7 cards')
    parser.add_argument('--payout-8-cards', type=float, default=1.0, help='Payout for 8 cards')
    parser.add_argument('--payout-9-cards', type=float, default=1.0, help='Payout for 9 cards')
    parser.add_argument('--payout-10-cards', type=float, default=1.0, help='Payout for 10 cards')
    parser.add_argument('--payout-11-cards', type=float, default=1.0, help='Payout for 11 cards')
    parser.add_argument('--payout-12plus-cards', type=float, default=1.0, help='Payout for 12+ cards')
    
    # Output configuration
    parser.add_argument('--output-dir', type=str, default='results', help='Directory to save results')
    parser.add_argument('--config-dir', type=str, default='config', help='Directory to save configuration')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to files')
    parser.add_argument('--config-file', type=str, help='Load configuration from file')
    
    return parser.parse_args()

def main():
    """Main entry point for the CLI application."""
    args = parse_arguments()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.config_file:
        with open(args.config_file, 'r') as f:
            config_dict = json.load(f)
        sim_config = SimulationConfig.from_dict(config_dict)
        print(f"Loaded configuration from {args.config_file}")
    else:
        # Set up payouts based on mode
        if args.payout_mode == 'total':
            sidebet_payouts = {
                17: args.payout_17,
                18: args.payout_18,
                19: args.payout_19,
                20: args.payout_20,
                21: args.payout_21,
                'bust-bust': args.payout_bust_bust,
                'blackjack-blackjack': args.payout_bj_bj
            }
        else:  # card count mode
            sidebet_payouts = {
                4: args.payout_4_cards,
                5: args.payout_5_cards,
                6: args.payout_6_cards,
                7: args.payout_7_cards,
                8: args.payout_8_cards,
                9: args.payout_9_cards,
                10: args.payout_10_cards,
                11: args.payout_11_cards,
                '12+': args.payout_12plus_cards
            }
        
        # Create simulation configuration
        sim_config = SimulationConfig(
            num_decks=args.num_decks,
            num_hands=args.num_hands,
            num_players=args.num_players,
            player_hit_soft_17=args.player_hits_soft_17,
            dealer_hit_soft_17=args.dealer_hits_soft_17,  
            reshuffle_cutoff=0 if args.continuous_shuffle else args.reshuffle_threshold,
            hit_against_blackjack=args.hit_against_blackjack,
            sidebet_payout_mode=args.payout_mode,
            sidebet_payouts=sidebet_payouts
        )
    
    if not args.no_save:
        os.makedirs(args.config_dir, exist_ok=True)
        config_file = f"{args.config_dir}/sidebet_config_cli_{timestamp}.json"
        with open(config_file, "w") as f:
            json.dump(sim_config.to_dict(), f, indent=4)
        print(f"Configuration saved to {config_file}")
    
    # Run the simulation
    print(f"Running sidebet simulation with {args.num_hands} hands...")
    simulator = SidebetSimulator(sim_config)
    start_time = time.time()
    results = simulator.run_simulation()
    end_time = time.time()
    simulation_time = end_time - start_time
    
    # Print summary results
    total_hands = results['total_bets']
    total_pushes = results['total_pushes']
    push_rate = total_pushes / total_hands * 100 if total_hands > 0 else 0
    
    print("\nSimulation Results Summary:")
    print(f"Total hands: {total_hands}")
    print(f"Simulation time: {simulation_time:.2f} seconds")
    print(f"Total pushes: {total_pushes} ({push_rate:.2f}%)")
    print(f"Player blackjacks: {results['player_blackjacks']} ({results['player_blackjacks']/total_hands*100:.2f}%)")
    print(f"Dealer blackjacks: {results['dealer_blackjacks']} ({results['dealer_blackjacks']/total_hands*100:.2f}%)")
    
    # Print push breakdown by value
    if args.payout_mode == 'total':
        print("\nPush Breakdown by Hand Value:")
        for value, count in results['pushes_by_value'].items():
            percentage = count / total_pushes * 100 if total_pushes > 0 else 0
            payout = sim_config.sidebet_payouts.get(value, 0) if isinstance(value, int) else sim_config.sidebet_payouts.get(str(value), 0)
            print(f"{value}: {count} ({percentage:.2f}%) - Payout: {payout}:1")
    else:
        print("\nPush Breakdown by Card Count:")
        for cards, count in results['pushes_by_card_count'].items():
            percentage = count / total_pushes * 100 if total_pushes > 0 else 0
            payout = sim_config.sidebet_payouts.get(cards, 0) if isinstance(cards, int) else sim_config.sidebet_payouts.get(str(cards), 0)
            print(f"{cards} cards: {count} ({percentage:.2f}%) - Payout: {payout}:1")
    
    # Print house edge
    print(f"\nSidebet House Edge: {results['sidebet_edge']:.2f}%")
    print(f"Main Bet House Edge: {results['house_edge']:.2f}%")
    
    if not args.no_save:
        os.makedirs(args.output_dir, exist_ok=True)
        
        report_generator = ReportGenerator(simulator)

        summary_file = f"sidebet_sim_summary_cli_{timestamp}.txt"
        detailed_file = f"sidebet_sim_detailed_cli_{timestamp}.csv"
        matrix_file = f"sidebet_sim_matrix_cli_{timestamp}.csv"
        push_matrix_file = f"sidebet_push_matrix_cli_{timestamp}.csv"
        
        report_generator.generate_summary_report(summary_file)
        report_generator.generate_detailed_report(detailed_file)
        report_generator.generate_outcome_matrix_csv(matrix_file)
        
        # Generate the detailed push matrix CSV
        generate_detailed_push_matrix_csv(results, os.path.join(args.output_dir, push_matrix_file))
        
        print(f"\nResults have been saved to the following files:")
        print(f"- Summary: {args.output_dir}/{summary_file}")
        print(f"- Detailed CSV: {args.output_dir}/{detailed_file}")
        print(f"- Matrix CSV: {args.output_dir}/{matrix_file}")
        print(f"- Detailed Push Matrix: {args.output_dir}/{push_matrix_file}")

def generate_detailed_push_matrix_csv(results, filepath):
    """Generate a CSV file with detailed push statistics correlating hand total and card count"""
    if not results or 'pushes_detail_matrix' not in results:
        raise ValueError("No push detail matrix available in the results")
    
    # Get all unique hand values and card counts
    hand_values = set()
    card_counts = set()
    
    for (value, count) in results['pushes_detail_matrix'].keys():
        hand_values.add(value)
        card_counts.add(count)
        
    # Sort the values and counts for better readability
    # Convert to list and sort
    hand_values = sorted([v for v in hand_values if isinstance(v, int)] + 
                        [v for v in hand_values if not isinstance(v, int)],
                        key=lambda x: float('inf') if not isinstance(x, int) else x)
    
    card_counts = sorted([c for c in card_counts if isinstance(c, int)] + 
                        [c for c in card_counts if not isinstance(c, int)])
    
    # Create a 2D matrix representation
    matrix = {}
    for value in hand_values:
        matrix[value] = {}
        for count in card_counts:
            matrix[value][count] = results['pushes_detail_matrix'].get((value, count), 0)

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        header = ['Hand Value\\Card Count'] + [str(count) for count in card_counts]
        writer.writerow(header)
        
        for value in hand_values:
            row = [str(value)]
            for count in card_counts:
                row.append(matrix[value][count])
            writer.writerow(row)
            
    print(f"Detailed push matrix saved to {filepath}")
    return filepath

if __name__ == '__main__':
    main()
