import os
import csv
import json
from datetime import datetime

class ReportGenerator:
    """
    Handles generation of reports from simulation results.
    """
    
    def __init__(self, simulator):
        """
        Initialize the report generator.
        
        Args:
            simulator (BlackjackSimulator): The simulator containing results to report
        """
        self.simulator = simulator
        self.results_dir = os.path.join(os.getcwd(), 'results')
        
    def generate_summary_report(self, filename=None):
        """
        Generate a text summary report of the simulation results.
        
        Args:
            filename (str, optional): Output filename. If None, a default name is generated.
            
        Returns:
            str: Path to the generated report file
        """
        if not self.simulator.results:
            raise ValueError("No simulation results available to report")
            
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blackjack_sim_summary_{timestamp}.txt"
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Get the summary text
        summary = self.simulator.get_results_summary()
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write(summary)
            
        print(f"Summary report saved to {filepath}")
        return filepath
        
    def generate_outcome_matrix_csv(self, filename=None):
        """
        Generate a CSV file with the outcome matrix data.
        
        Args:
            filename (str, optional): Output filename. If None, a default name is generated.
            
        Returns:
            str: Path to the generated CSV file
        """
        if not self.simulator.results:
            raise ValueError("No simulation results available to report")
            
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blackjack_sim_matrix_{timestamp}.csv"
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Create a 2D matrix from the outcome data
        outcome_matrix = self.simulator.results['outcome_matrix']
        
        # Find the maximum values to define matrix dimensions
        max_player = 21
        max_dealer = 21
        for player_total, dealer_total in outcome_matrix.keys():
            max_player = max(max_player, player_total)
            max_dealer = max(max_dealer, dealer_total)
            
        # Initialize matrix with zeros
        matrix = []
        for _ in range(max_player + 1):
            matrix.append([0] * (max_dealer + 1))
            
        # Fill in matrix values
        for (player_total, dealer_total), count in outcome_matrix.items():
            if player_total <= max_player and dealer_total <= max_dealer:
                matrix[player_total][dealer_total] = count
                
        # Write matrix to CSV file
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row with dealer totals
            header = ['Player\\Dealer'] + list(range(max_dealer + 1))
            writer.writerow(header)
            
            # Write each player total row
            for player_total in range(max_player + 1):
                row = [player_total] + matrix[player_total]
                writer.writerow(row)
                
        print(f"Outcome matrix saved to {filepath}")
        return filepath
    
    def generate_detailed_report(self, filename=None):
        """
        Generate a detailed CSV report with all outcomes.
        
        Args:
            filename (str, optional): Output filename. If None, a default name is generated.
            
        Returns:
            str: Path to the generated CSV file
        """
        if not self.simulator.results:
            raise ValueError("No simulation results available to report")
            
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blackjack_sim_detailed_{timestamp}.csv"
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Get results details
        outcome_details = self.simulator.results['outcome_details']
        
        # Prepare data for CSV
        detailed_data = []
        for (player_total, dealer_total, result), count in outcome_details.items():
            win_loss = "Win" if result == "player_win" else ("Loss" if result == "dealer_win" else "Push")
            
            entry = {
                'player_total': player_total,
                'dealer_total': dealer_total,
                'result': win_loss,
                'count': count,
                'percentage': (count / self.simulator.results['total_bets']) * 100
            }
            detailed_data.append(entry)
            
        # Sort by player total, then dealer total
        detailed_data.sort(key=lambda x: (x['player_total'], x['dealer_total'], x['result']))
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['player_total', 'dealer_total', 'result', 'count', 'percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in detailed_data:
                writer.writerow(entry)
                
        print(f"Detailed report saved to {filepath}")
        return filepath
    
    def save_config(self, filename=None):
        """
        Save the simulation configuration to a JSON file.
        
        Args:
            filename (str, optional): Output filename. If None, a default name is generated.
            
        Returns:
            str: Path to the generated JSON file
        """
        config = self.simulator.config
        
        # Create config directory if it doesn't exist
        config_dir = os.path.join(os.getcwd(), 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_config_{timestamp}.json"
            
        filepath = os.path.join(config_dir, filename)
        
        # Create a JSON serializable config dictionary
        config_dict = {
            'num_hands': config.num_hands,
            'num_decks': config.num_decks,
            'player_hit_soft_17': config.player_hit_soft_17,
            'dealer_hit_soft_17': config.dealer_hit_soft_17,
            'reshuffle_cutoff': config.reshuffle_cutoff,
            'commission_pct': config.commission_pct,
            'blackjack_payout': config.blackjack_payout,
            'num_players': config.num_players,
            'player_hit_rules': str(config.player_hit_rules)  # Convert dict to string for JSON serialization
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=4)
            
        print(f"Configuration saved to {filepath}")
        return filepath