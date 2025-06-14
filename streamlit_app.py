import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import sys
import time
import csv
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.config import SimulationConfig
from src.simulation.simulator import BlackjackSimulator
from src.simulation.interactive_simulator import InteractiveSimulator
from src.simulation.sidebet_simulator import SidebetSimulator, InteractiveSidebetSimulator
from src.reporting.report_generator import ReportGenerator

# Custom CSS for card styling
def load_custom_css():
    st.markdown("""
    <style>
    .card {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 40px;
        height: 60px;
        margin-right: 5px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 5px;
        border: 1px solid #ccc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        background-color: white;
    }
    
    .card.hearts, .card.diamonds {
        color: red;
    }
    
    .card.clubs, .card.spades {
        color: black;
    }
    
    .progress-bar {
        background-color: #22c55e;
        height: 4px;
        margin-bottom: 15px;
        border-radius: 2px;
    }
    
    .hand-value {
        margin-top: 5px;
        font-weight: bold;
    }
    
    .hand-label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .result-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 3px;
        color: white;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .result-win {
        background-color: #22c55e;
    }
    
    .result-loss {
        background-color: #ef4444;
    }
    
    .result-push {
        background-color: #f59e0b;
    }
    </style>
    """, unsafe_allow_html=True)

# Card rendering utility function
def render_card(card_str):
    if not card_str:
        return ""
        
    parts = card_str.split(" of ")
    if len(parts) != 2:
        return card_str
        
    rank, suit = parts
    
    suit_class = suit.lower()
    rank_display = rank
    if rank == "10":
        rank_display = "10"
    elif rank == "Jack":
        rank_display = "J"
    elif rank == "Queen":
        rank_display = "Q"
    elif rank == "King":
        rank_display = "K"
    elif rank == "Ace":
        rank_display = "A"
        
    return f'<div class="card {suit_class}">{rank_display}</div>'

class StreamlitReportGenerator:
    """
    Streamlit-specific version of ReportGenerator that works with direct results
    rather than requiring a simulator instance.
    """
    
    def __init__(self, results, config):
        """
        Initialize the report generator for Streamlit.
        
        Args:
            results (dict): The simulation results
            config (SimulationConfig): Configuration used for the simulation
        """
        self.results = results
        self.config = config
        self.results_dir = os.path.join(os.getcwd(), 'results')
        
    def generate_summary(self, filename):
        """Generate a summary report of the results"""
        if not self.results:
            raise ValueError("No simulation results available to report")

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)

        total_hands = self.results['total_bets']
        player_win_pct = 100 * self.results['player_wins'] / total_hands if total_hands > 0 else 0
        dealer_win_pct = 100 * self.results['dealer_wins'] / total_hands if total_hands > 0 else 0
        push_pct = 100 * self.results['pushes'] / total_hands if total_hands > 0 else 0
        
        summary = [
            f"Simulation Results Summary",
            f"=========================",
            f"",
            f"{self.config}",
            f"",
            f"Total hands: {total_hands}",
            f"Simulation time: {self.results['simulation_time']:.2f} seconds",
            f"",
            f"Player wins: {self.results['player_wins']} ({player_win_pct:.2f}%)",
            f"Dealer wins: {self.results['dealer_wins']} ({dealer_win_pct:.2f}%)",
            f"Pushes: {self.results['pushes']} ({push_pct:.2f}%)",
            f"",
            f"Player busts: {self.results['player_busts']} ({100 * self.results['player_busts'] / total_hands:.2f}%)",
            f"Dealer busts: {self.results['dealer_busts']} ({100 * self.results['dealer_busts'] / total_hands:.2f}%)",
            f""
        ]
        
        # Add blackjack statistics if available
        if 'blackjacks' in self.results:
            blackjack_count = self.results.get('blackjacks', 0)
            blackjack_pct = 100 * blackjack_count / total_hands if total_hands > 0 else 0
            summary.append(f"Blackjacks: {blackjack_count} ({blackjack_pct:.2f}%)")
            
            # Count blackjack pushes from detailed outcome data
            blackjack_pushes = 0
            for (player_total, dealer_total, result), count in self.results.get('outcome_details', {}).items():
                if result == "push" and player_total == 21 and dealer_total == 21:
                    # This is an approximation as we can't distinguish blackjack vs non-blackjack 21 in outcome_details
                    blackjack_pushes += count
            
            blackjack_push_pct = 100 * blackjack_pushes / total_hands if total_hands > 0 else 0
            summary.append(f"Blackjack pushes: {blackjack_pushes} ({blackjack_push_pct:.2f}%)")
            summary.append(f"")
        # Add sidebet-specific blackjack statistics if available
        elif 'player_blackjacks' in self.results and 'dealer_blackjacks' in self.results:
            player_bj_count = self.results.get('player_blackjacks', 0)
            dealer_bj_count = self.results.get('dealer_blackjacks', 0)
            player_bj_pct = 100 * player_bj_count / total_hands if total_hands > 0 else 0
            dealer_bj_pct = 100 * dealer_bj_count / total_hands if total_hands > 0 else 0
            
            summary.append(f"Player blackjacks: {player_bj_count} ({player_bj_pct:.2f}%)")
            summary.append(f"Dealer blackjacks: {dealer_bj_count} ({dealer_bj_pct:.2f}%)")
            
            # Get blackjack-blackjack pushes from pushes_by_value if available
            if 'pushes_by_value' in self.results and 'blackjack' in self.results['pushes_by_value']:
                bj_pushes = self.results['pushes_by_value']['blackjack']
                bj_push_pct = 100 * bj_pushes / total_hands if total_hands > 0 else 0
                summary.append(f"Blackjack pushes: {bj_pushes} ({bj_push_pct:.2f}%)")
            
            summary.append(f"")
            
        summary.append(f"House edge: {self.results['house_edge']:.2f}%")

        with open(filepath, 'w') as f:
            f.write("\n".join(summary))
            
        print(f"Summary report saved to {filepath}")
        return filepath
        
    def generate_matrix_csv(self, filename):
        """Generate a CSV file with the outcome matrix data"""
        if not self.results:
            raise ValueError("No simulation results available to report")

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Create a 2D matrix from the outcome data
        outcome_matrix = self.results['outcome_matrix']
        
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
                
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            header = ['Player\\Dealer'] + list(range(max_dealer + 1))
            writer.writerow(header)
            
            for player_total in range(max_player + 1):
                row = [player_total] + matrix[player_total]
                writer.writerow(row)
                
        print(f"Outcome matrix saved to {filepath}")
        return filepath
    
    def generate_detailed_csv(self, filename):
        """Generate a detailed CSV report with all outcomes"""
        if not self.results:
            raise ValueError("No simulation results available to report")
            

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)
        
        outcome_details = self.results['outcome_details']
        
        detailed_data = []
        for (player_total, dealer_total, result), count in outcome_details.items():
            win_loss = "Win" if result == "player_win" else ("Loss" if result == "dealer_win" else "Push")
            
            entry = {
                'player_total': player_total,
                'dealer_total': dealer_total,
                'result': win_loss,
                'count': count,
                'percentage': (count / self.results['total_bets']) * 100
            }
            detailed_data.append(entry)
            
        detailed_data.sort(key=lambda x: (x['player_total'], x['dealer_total'], x['result']))
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['player_total', 'dealer_total', 'result', 'count', 'percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in detailed_data:
                writer.writerow(entry)
                
        print(f"Detailed report saved to {filepath}")
        return filepath
    
    def get_detailed_dataframe(self):
        """Create a pandas DataFrame from the detailed outcome data for visualization"""
        if not self.results:
            raise ValueError("No simulation results available to report")
            
        outcome_details = self.results['outcome_details']
        
        detailed_data = []
        
        for (player_total, dealer_total, result), count in outcome_details.items():
            win_loss = "Win" if result == "player_win" else ("Loss" if result == "dealer_win" else "Push")
            
            for _ in range(count):
                detailed_data.append({
                    'player_total': player_total,
                    'dealer_total': dealer_total,
                    'result': win_loss,
                    'dealer_upcard': 0 
                })
    
        return pd.DataFrame(detailed_data)
    
    def generate_detailed_push_matrix_csv(self, filename):
        """Generate a CSV file with detailed push statistics correlating hand total and card count"""
        if not self.results or 'pushes_detail_matrix' not in self.results:
            raise ValueError("No push detail matrix available in the results")

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Get all unique hand values and card counts
        hand_values = set()
        card_counts = set()
        
        for (value, count) in self.results['pushes_detail_matrix'].keys():
            hand_values.add(value)
            card_counts.add(count)
            
        # Sort the values and counts for better readability
        # Convert to list and sort
        hand_values = sorted([v for v in hand_values if isinstance(v, int)] + 
                            [v for v in hand_values if not isinstance(v, int)],
                            key=lambda x: float('inf') if not isinstance(x, int) else x)
        
        # Sort card counts with integers first (in numeric order) followed by non-integers
        int_counts = sorted([c for c in card_counts if isinstance(c, int)])
        non_int_counts = sorted([c for c in card_counts if not isinstance(c, int)])
        card_counts = int_counts + non_int_counts
        
        # Create a 2D matrix representation
        matrix = {}
        for value in hand_values:
            matrix[value] = {}
            for count in card_counts:
                matrix[value][count] = self.results['pushes_detail_matrix'].get((value, count), 0)
        
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
    
st.set_page_config(
    page_title="Blackjack Simulator",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS for styling
load_custom_css()

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2563EB;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .result-container {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #DBEAFE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Blackjack Simulator</div>', unsafe_allow_html=True)
st.markdown("""
This application allows you to configure and run blackjack simulations to analyze house edge 
and game dynamics under various rule configurations. You can adjust parameters, 
run simulations, and visualize the results.
""")

def load_configs():
    """Load all saved configurations from the config directory"""
    configs = []
    try:
        config_dir = "config"
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(config_dir, filename), 'r') as f:
                        configs.append(json.load(f))
    except Exception as e:
        st.error(f"Error loading saved configurations: {e}")
    return configs

def load_simulation_results():
    """Load all simulation results from the results directory"""
    results = []
    try:
        results_dir = "results"
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if filename.startswith('blackjack_sim_summary_') and filename.endswith('.txt'):
                    timestamp = filename.replace('blackjack_sim_summary_', '').replace('.txt', '')
                    matrix_file = f"blackjack_sim_matrix_{timestamp}.csv"
                    detailed_file = f"blackjack_sim_detailed_{timestamp}.csv"
                    config_file = f"simulation_config_{timestamp}.json"
                    
                    result_entry = {
                        'timestamp': timestamp,
                        'summary_file': filename,
                        'matrix_file': matrix_file if os.path.exists(os.path.join(results_dir, matrix_file)) else None,
                        'detailed_file': detailed_file if os.path.exists(os.path.join(results_dir, detailed_file)) else None,
                        'config_file': config_file if os.path.exists(os.path.join("config", config_file)) else None,
                    }
                    results.append(result_entry)
    except Exception as e:
        st.error(f"Error loading simulation results: {e}")
    
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    return results

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Run Simulation", "Hand-by-Hand Simulation", "Sidebet Simulation", "Data Visualization", "Previous Results"])

with tab1:
    st.markdown('<div class="section-header">Configure and Run Simulation</div>', unsafe_allow_html=True)
    
    with st.form("simulation_config_advanced"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Game Rules")
            
            num_hands = st.number_input(
                "Number of Hands to Simulate", 
                min_value=100, 
                max_value=100000000, 
                value=10000,
                step=1000
            )
            
            num_decks = st.number_input(
                "Number of Decks", 
                min_value=1, 
                max_value=8, 
                value=6
            )
            
            player_hits_soft_17 = st.checkbox("Player Hits Soft 17", value=False)
            dealer_hits_soft_17 = st.checkbox("Dealer Hits Soft 17", value=False)
            
            shuffle_method = st.selectbox(
                "Shuffle Method",
                options=["Reshuffle at threshold", "Continuous shuffle"],
                index=0
            )
            
            if shuffle_method == "Reshuffle at threshold":
                reshuffle_threshold = st.number_input(
                    "Reshuffle Threshold (cards remaining)", 
                    min_value=0, 
                    max_value=104, 
                    value=52
                )
            else:
                reshuffle_threshold = 0
            
            num_players = st.number_input(
                "Number of Players",
                min_value=1,
                max_value=7,
                value=1
            )
        
        with col2:
            st.markdown("### Game Parameters")
            
            commission = st.slider(
                "Commission (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=5.0, 
                step=0.1
            )
            
            blackjack_payout = st.selectbox(
                "Blackjack Payout",
                options=["1:1", "6:5", "3:2", "2:1"],
                index=0
            )
            
            commission_on_blackjack = st.checkbox("Apply Commission to Blackjack Wins", value=True)
            
            hit_against_blackjack = st.checkbox(
                "Allow Hit Against Dealer Blackjack", 
                value=False,
                help="If checked, player can continue to hit when dealer has blackjack (will not result in a push if 21 is reached)"
            )
            
            st.markdown("### Simulation Options")
            
            save_results = st.checkbox("Save Simulation Results", value=True)
            generate_visuals = st.checkbox("Generate Visualizations", value=True)
        
        advanced_expander = st.expander("Advanced Strategy Options")
        with advanced_expander:
            custom_hit_rules = st.text_area(
                "Custom Hit Rules", 
                value="",
                help="Format: 'hard:16,10:hit;soft:17:hit' means hit on hard 16 when dealer shows 10, and hit on soft 17"
            )
        
        submit_button = st.form_submit_button("Run Simulation")

    def parse_ratio(ratio_str):
        """Convert a ratio string (e.g. "6:5") to a decimal multiplier."""
        try:
            num, denom = map(float, ratio_str.split(':'))
            return num / denom
        except:
            return 1.0  # Default to 1:1 payout if parsing fails

    def run_simulation_advanced(config):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        hit_rules_dict = {}
        if config.get("custom_hit_rules"):
            try:
                for rule in config["custom_hit_rules"].split(';'):
                    if not rule:
                        continue
                    components = rule.strip().split(':')
                    if len(components) < 3:
                        st.warning(f"Skipping invalid rule format: {rule}")
                        continue
                    
                    hand_type = components[0].lower()  # "hard" or "soft"
                    total = components[1]  # player total
                    dealer_cards_action = components[2]  # dealer cards and action
                    
                    if ',' in dealer_cards_action:
                        dealer_card_str, action = dealer_cards_action.split(',')
                        dealer_cards = [int(c) for c in dealer_card_str.split('|')]
                    else:
                        dealer_cards = list(range(2, 12))  # All possible dealer cards
                        action = dealer_cards_action
                    
                    should_hit = action.lower() in ('hit', 'h', 'true', 't', 'yes', 'y', '1')
                    
                    for dealer_card in dealer_cards:
                        if hand_type == 'hard':
                            hit_rules_dict[(int(total), dealer_card)] = should_hit
                        else:
                            hit_rules_dict[(f"soft {total}", dealer_card)] = should_hit
            except Exception as e:
                st.warning(f"Error parsing custom hit rules: {e}. Default rules will be used.")
        
        sim_config = SimulationConfig(
            num_decks=config["num_decks"],
            num_hands=config["num_hands"],
            player_hit_soft_17=config["player_hits_soft_17"],
            dealer_hit_soft_17=config["dealer_hits_soft_17"],  
            reshuffle_cutoff=config.get("reshuffle_threshold", 52) if config["shuffle_method"] != "Continuous shuffle" else 0,
            commission_pct=config["commission"],
            blackjack_payout=parse_ratio(config["blackjack_payout"]),
            num_players=config.get("num_players", 1),
            player_hit_rules=hit_rules_dict if hit_rules_dict else None,
            commission_on_blackjack=config["commission_on_blackjack"],
            hit_against_blackjack=config.get("hit_against_blackjack", False)
        )
        
        if config["save_results"]:
            os.makedirs("config", exist_ok=True)
            config_file = f"config/simulation_config_{timestamp}.json"
            with open(config_file, "w") as f:
                json.dump(sim_config.to_dict(), f, indent=4)
        
        simulator = BlackjackSimulator(sim_config)
        start_time = time.time()
        results = simulator.run_simulation()
        end_time = time.time()
        simulation_time = end_time - start_time
        
        report_generator = StreamlitReportGenerator(results, sim_config)
        
        if config["save_results"]:
            os.makedirs("results", exist_ok=True)
            report_generator.generate_detailed_csv(f"blackjack_sim_detailed_{timestamp}.csv")
            report_generator.generate_matrix_csv(f"blackjack_sim_matrix_{timestamp}.csv")
            report_generator.generate_summary(f"blackjack_sim_summary_{timestamp}.txt")
        
        total_hands = results['total_bets']
        # Raw percentages
        player_win_rate = results['player_wins'] / total_hands if total_hands > 0 else 0
        dealer_win_rate = results['dealer_wins'] / total_hands if total_hands > 0 else 0
        push_rate = results['pushes'] / total_hands if total_hands > 0 else 0
        player_bust_rate = results['player_busts'] / total_hands if total_hands > 0 else 0
        dealer_bust_rate = results['dealer_busts'] / total_hands if total_hands > 0 else 0
        blackjack_rate = results.get('blackjacks', 0) / total_hands if total_hands > 0 else 0
        
        # Count blackjack pushes from detailed outcome data
        blackjack_pushes = 0
        for (player_total, dealer_total, result), count in results.get('outcome_details', {}).items():
            if result == "push" and player_total == 21 and dealer_total == 21:
                # This is an approximation as we can't distinguish blackjack vs non-blackjack 21 in outcome_details
                blackjack_pushes += count
        
        blackjack_push_rate = blackjack_pushes / total_hands if total_hands > 0 else 0
        
        # Raw edge (basic win/loss difference before commission)
        raw_edge = (player_win_rate - dealer_win_rate) * 100
        
        # True house edge calculation including commission
        # Use the simulator's house edge calculation which properly accounts for all payouts
        house_edge = results['house_edge']
        
        summary_data = {
            "timestamp": timestamp,
            "config": sim_config.to_dict(),
            "results": results,
            "simulation_time": simulation_time,
            "house_edge": house_edge,
            "raw_edge": raw_edge,
            "player_win_rate": player_win_rate,
            "dealer_win_rate": dealer_win_rate,
            "push_rate": push_rate,
            "player_bust_rate": player_bust_rate,
            "dealer_bust_rate": dealer_bust_rate,
            "blackjack_rate": blackjack_rate,
            "blackjack_push_rate": blackjack_push_rate
        }
        
        if config["generate_visuals"]:
            detailed_results_df = report_generator.get_detailed_dataframe()
            summary_data["detailed_df"] = detailed_results_df
        
        return summary_data

    if submit_button:
        with st.spinner('Running simulation... This may take a moment.'):
            config = {
                "num_hands": num_hands,
                "num_decks": num_decks,
                "player_hits_soft_17": player_hits_soft_17,
                "dealer_hits_soft_17": dealer_hits_soft_17,
                "shuffle_method": shuffle_method,
                "reshuffle_threshold": reshuffle_threshold if shuffle_method == "Reshuffle at threshold" else 0,
                "commission": commission,
                "blackjack_payout": blackjack_payout,
                "commission_on_blackjack": commission_on_blackjack,
                "hit_against_blackjack": hit_against_blackjack,
                "num_players": num_players,
                "save_results": save_results,
                "generate_visuals": generate_visuals,
                "custom_hit_rules": custom_hit_rules
            }
            
            simulation_results = run_simulation_advanced(config)
            st.session_state.latest_results = simulation_results
            
        st.success(f"Simulation completed! {num_hands} hands simulated in {simulation_results['simulation_time']:.2f} seconds.")

        results = simulation_results
        
        st.markdown('<div class="section-header">Simulation Results</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Raw Edge", f"{results['raw_edge']:.2f}%",
                     help="Raw win/loss difference before payouts and commissions")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("True House Edge", f"{results['house_edge']:.2f}%", 
                     help="House edge after applying payouts and commissions")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Player Win Rate", f"{results['player_win_rate']*100:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Dealer Win Rate", f"{results['dealer_win_rate']*100:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        col4, col5, col6 = st.columns(3)
        with col4:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Push Rate", f"{results['push_rate']*100:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col5:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Player Bust Rate", f"{results['player_bust_rate']*100:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col6:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Dealer Bust Rate", f"{results['dealer_bust_rate']*100:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

        # Add blackjack statistics
        col7, col8 = st.columns(2)
        with col7:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Blackjack Rate", f"{results['blackjack_rate']*100:.2f}%",
                     help="Percentage of hands where player or dealer got a blackjack")
            st.markdown('</div>', unsafe_allow_html=True)

        with col8:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Blackjack Push Rate", f"{results['blackjack_push_rate']*100:.2f}%",
                     help="Percentage of hands where both player and dealer got blackjack")
            st.markdown('</div>', unsafe_allow_html=True)
            
        if save_results:
            st.info(f"""
            Results have been saved to the following files:
            - Configuration: `config/simulation_config_{results['timestamp']}.json`
            - Detailed CSV: `results/blackjack_sim_detailed_{results['timestamp']}.csv`
            - Matrix CSV: `results/blackjack_sim_matrix_{results['timestamp']}.csv`
            - Summary: `results/blackjack_sim_summary_{results['timestamp']}.txt`
            """)

with tab2:
    st.markdown('<div class="section-header">Interactive Hand-by-Hand Simulation</div>', unsafe_allow_html=True)
    st.markdown("""
    This mode allows you to see each hand being played step-by-step and observe how the 
    statistics evolve in real-time as more hands are played.
    """)
    
    st.markdown("""
    <style>
        .card {
            display: inline-block;
            width: 70px;
            height: 100px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            margin: 5px;
            text-align: center;
            font-size: 24px;
            line-height: 100px;
            font-weight: bold;
        }
        .card.spades, .card.clubs {
            color: #222;
        }
        .card.hearts, .card.diamonds {
            color: #D22;
        }
        .card-hand {
            margin: 15px 0;
            padding: 10px;
            background-color: #1E5631;
            border-radius: 8px;
            display: inline-block;
            min-width: 300px;
        }
        .hand-value {
            color: white;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .hand-label {
            font-weight: bold;
            color: white;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .result-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            margin-top: 10px;
        }
        .result-win {
            background-color: #10B981;
            color: white;
        }
        .result-loss {
            background-color: #EF4444;
            color: white;
        }
        .result-push {
            background-color: #F59E0B;
            color: white;
        }
        .stats-box {
            background-color: #EEF2FF;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }
        .step-btn {
            min-width: 120px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if "interactive_simulator" not in st.session_state:
        st.session_state.interactive_simulator = None
        st.session_state.current_state = None
    
    with st.expander("Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            num_decks = st.number_input(
                "Number of Decks", 
                min_value=1, 
                max_value=8, 
                value=6,
                key="interactive_num_decks"
            )
            
            player_hits_soft_17 = st.checkbox(
                "Player Hits Soft 17", 
                value=False,
                key="interactive_player_hits_soft_17"
            )
            
            shuffle_method = st.selectbox(
                "Shuffle Method",
                options=["Reshuffle at threshold", "Continuous shuffle"],
                index=0,
                key="interactive_shuffle_method"
            )
            
            if shuffle_method == "Reshuffle at threshold":
                reshuffle_threshold = st.number_input(
                    "Reshuffle Threshold (cards remaining)", 
                    min_value=0, 
                    max_value=104, 
                    value=52,
                    key="interactive_reshuffle_threshold"
                )
            else:
                reshuffle_threshold = 0
                
        with col2:
            dealer_hits_soft_17 = st.checkbox(
                "Dealer Hits Soft 17", 
                value=False,
                key="interactive_dealer_hits_soft_17"
            )
            
            commission = st.slider(
                "Commission (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=5.0, 
                step=0.1,
                key="interactive_commission"
            )
            
            blackjack_payout = st.selectbox(
                "Blackjack Payout",
                options=["1:1", "6:5", "3:2", "2:1"],
                index=0,
                key="interactive_blackjack_payout"
            )
            
            commission_on_blackjack = st.checkbox("Apply Commission to Blackjack Wins", value=True, key="interactive_commission_on_blackjack")
            
            hit_against_blackjack = st.checkbox(
                "Allow Hit Against Dealer Blackjack", 
                value=False,
                key="interactive_hit_against_blackjack",
                help="If checked, player can continue to hit when dealer has blackjack (will not result in a push if 21 is reached)"
            )
            
            st.markdown("### Advanced Strategy Options")
            custom_hit_rules = st.text_area(
                "Custom Hit Rules", 
                value="",
                help="Format: 'hard:16,10:hit;soft:17:hit' means hit on hard 16 when dealer shows 10, and hit on soft 17",
                key="interactive_custom_hit_rules"
            )
        
        initialize_button = st.button("Initialize Simulator", use_container_width=True)
        
        if initialize_button:
            hit_rules_dict = {}
            if custom_hit_rules:
                try:
                    for rule in custom_hit_rules.split(';'):
                        if not rule:
                            continue
                        components = rule.strip().split(':')
                        if len(components) < 3:
                            st.warning(f"Skipping invalid rule format: {rule}")
                            continue
                        
                        hand_type = components[0].lower()  # "hard" or "soft"
                        total = components[1]  # player total
                        dealer_cards_action = components[2]  # dealer cards and action
                        
                        if ',' in dealer_cards_action:
                            dealer_card_str, action = dealer_cards_action.split(',')
                            dealer_cards = [int(c) for c in dealer_card_str.split('|')]
                        else:
                            dealer_cards = list(range(2, 12))  # All possible dealer cards
                            action = dealer_cards_action
                        
                        should_hit = action.lower() in ('hit', 'h', 'true', 't', 'yes', 'y', '1')
                        
                        for dealer_card in dealer_cards:
                            if hand_type == 'hard':
                                hit_rules_dict[(int(total), dealer_card)] = should_hit
                            else:
                                hit_rules_dict[(f"soft {total}", dealer_card)] = should_hit
                except Exception as e:
                    st.warning(f"Error parsing custom hit rules: {e}. Default rules will be used.")
            
            sim_config = SimulationConfig(
                num_decks=num_decks,
                num_hands=100000000,
                player_hit_soft_17=player_hits_soft_17,
                dealer_hit_soft_17=dealer_hits_soft_17,  
                reshuffle_cutoff=reshuffle_threshold if shuffle_method != "Continuous shuffle" else 0,
                commission_pct=commission,
                blackjack_payout=parse_ratio(blackjack_payout),
                num_players=1,
                player_hit_rules=hit_rules_dict if hit_rules_dict else None,
                commission_on_blackjack=commission_on_blackjack,
                hit_against_blackjack=hit_against_blackjack
            )
            
            st.session_state.interactive_simulator = InteractiveSimulator(sim_config)
            st.session_state.interactive_simulator.setup()
            
            st.session_state.current_state = st.session_state.interactive_simulator.start_new_hand()
            st.rerun()

    if st.session_state.interactive_simulator is not None and st.session_state.current_state is not None:
        st.markdown("### Simulation Controls")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.session_state.current_state["phase"] == "init":
                deal_button = st.button("Deal New Hand", key="deal_btn", use_container_width=True, type="primary")
                if deal_button:
                    st.session_state.current_state = st.session_state.interactive_simulator.deal_cards()
                    st.rerun()
            elif st.session_state.current_state["phase"] == "player_turn":
                hit_button = st.button("Hit", key="hit_btn", use_container_width=True)
                if hit_button:
                    st.session_state.current_state = st.session_state.interactive_simulator.player_hit()
                    st.rerun()
        
        with col2:
            if st.session_state.current_state["phase"] == "player_turn":
                stand_button = st.button("Stand", key="stand_btn", use_container_width=True)
                if stand_button:
                    st.session_state.current_state = st.session_state.interactive_simulator.player_stand()
                    st.rerun()
            elif st.session_state.current_state["phase"] == "dealer_turn":
                step_button = st.button("Dealer Step", key="step_btn", use_container_width=True)
                if step_button:
                    st.session_state.current_state = st.session_state.interactive_simulator.dealer_step()
                    st.rerun()
            elif st.session_state.current_state["phase"] == "result":
                next_hand_button = st.button("Next Hand", key="next_hand_btn", use_container_width=True, type="primary")
                if next_hand_button:
                    st.session_state.current_state = st.session_state.interactive_simulator.start_new_hand()
                    st.rerun()
                    
        with col3:
            st.info(f"Current Phase: {st.session_state.current_state['phase'].replace('_', ' ').title()}")
        
        st.markdown("### Current Hand")
        
        def render_hand(hand_data, is_dealer=False, hide_second_card=False):
            html = '<div class="card-hand">'
            
            if is_dealer:
                html += '<div class="hand-label">Dealer Hand</div>'
            else:
                html += '<div class="hand-label">Player Hand</div>'
            
            if is_dealer and hide_second_card:
                html += '<div class="hand-value">Value: ?</div>'
            else:
                value = hand_data["value"]
                soft_text = " (soft)" if hand_data["is_soft"] else ""
                html += f'<div class="hand-value">Value: {value}{soft_text}</div>'
            
            for i, card_str in enumerate(hand_data["cards"]):
                if is_dealer and i == 1 and hide_second_card:
                    html += '<div class="card" style="background-color: #6B7280; color: white;">?</div>'
                else:
                    html += render_card(card_str)
            
            html += '</div>'
            return html
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.current_state["player_hands"]:
                player_hand = st.session_state.current_state["player_hands"][0]
                st.markdown(render_hand(player_hand), unsafe_allow_html=True)
                
                if player_hand["is_bust"]:
                    st.error("Player Bust!")
                elif player_hand["is_blackjack"]:
                    st.success("Player Blackjack!")
        
        with col2:
            if st.session_state.current_state["dealer_hand"]:
                dealer_hand = st.session_state.current_state["dealer_hand"]
                hide_hole_card = st.session_state.current_state["phase"] in ["init", "player_turn"]
                
                st.markdown(
                    render_hand(dealer_hand, is_dealer=True, hide_second_card=hide_hole_card),
                    unsafe_allow_html=True
                )
                
                if st.session_state.current_state["phase"] == "result":
                    if dealer_hand["is_bust"]:
                        st.error("Dealer Bust!")
                    elif dealer_hand["is_blackjack"]:
                        st.success("Dealer Blackjack!")
        
        if st.session_state.current_state["result"]:
            result = st.session_state.current_state["result"]
            
            if "display_result" in result:
                if result["display_result"] == "Player Win":
                    st.markdown('<div class="result-badge result-win">Player Win</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — your bet was correct. Dealer won.*")
                elif result["display_result"] == "Dealer Win":
                    st.markdown('<div class="result-badge result-loss">Dealer Win</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — your bet was incorrect. Dealer lost.*")
                else: 
                    st.markdown('<div class="result-badge result-push">Push</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — the result was a tie.*")
            else:
                if result["result"] == "player_win":
                    st.markdown('<div class="result-badge result-win">Player Win</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — your bet was correct. Dealer won.*")
                elif result["result"] == "dealer_win":
                    st.markdown('<div class="result-badge result-loss">Dealer Win</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — your bet was incorrect. Dealer lost.*")
                else:  # push
                    st.markdown('<div class="result-badge result-push">Push</div>', unsafe_allow_html=True)
                    st.markdown("*You bet on the dealer — the result was a tie.*")
                
            st.write(f"Final: Player: {result['player_value']} vs Dealer: {result['dealer_value']}")
        
        st.markdown("### Real-time Statistics")
        
        stats = st.session_state.current_state["stats"]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("Hands Played", stats["total_hands"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            if stats['house_edge'] is not None:
                st.metric("True House Edge", f"{stats['house_edge']*100:.2f}%",
                         help="House edge after applying payouts and commissions")
                # Calculate and store raw edge
                stats['raw_edge'] = ((stats['player_wins'] - stats['dealer_wins']) / 
                                   max(stats['total_hands'], 1) * 100)
                st.metric("Raw Edge", f"{stats['raw_edge']:.2f}%",
                         help="Raw win/loss difference before payouts and commissions")
            else:
                st.metric("House Edge", "Calculating...")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("Dealer Wins", f"{stats['dealer_wins']} ({100*stats['dealer_wins']/max(stats['total_hands'],1):.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("Dealer Busts", f"{stats['dealer_busts']} ({100*stats['dealer_busts']/max(stats['total_hands'],1):.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("Player Wins", f"{stats['player_wins']} ({100*stats['player_wins']/max(stats['total_hands'],1):.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="stats-box">', unsafe_allow_html=True)
            st.metric("Player Busts", f"{stats['player_busts']} ({100*stats['player_busts']/max(stats['total_hands'],1):.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stats-box">', unsafe_allow_html=True)
        st.metric("Pushes", f"{stats['pushes']} ({100*stats['pushes']/max(stats['total_hands'],1):.1f}%)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.current_state["history_length"] > 0:
            with st.expander("Hand History", expanded=False):
                history = st.session_state.interactive_simulator.get_hand_history()
                history_df = pd.DataFrame(history)
                
                history_df["player_cards"] = history_df["player_hand"].apply(lambda x: ", ".join(x))
                history_df["dealer_cards"] = history_df["dealer_hand"].apply(lambda x: ", ".join(x))
                
                history_df["outcome"] = history_df["result"].map({
                    "player_win": "Player Win", 
                    "dealer_win": "Dealer Win",
                    "push": "Push"
                })
                
                display_df = history_df[["player_value", "dealer_value", "outcome", "player_cards", "dealer_cards"]]
                display_df.index = display_df.index + 1  # 1-based indexing for hand number
                
                st.dataframe(display_df.iloc[::-1])
        
        # Auto-play option
        with st.expander("Auto-play Options", expanded=False):
            st.write("Set up auto-play to automatically simulate multiple hands in succession.")
            
            num_auto_hands = st.number_input(
                "Number of Hands to Auto-Play", 
                min_value=1,
                max_value=100,
                value=10,
                key="auto_play_hands_1"
            )
            
            delay = st.slider(
                "Delay Between Steps (seconds)",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                key="delay_slider_1"
            )
            
            auto_play = st.button("Start Auto-Play", key="auto_play_btn")
            
            if auto_play:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(num_auto_hands):
                    # Start a new hand
                    st.session_state.current_state = st.session_state.interactive_simulator.start_new_hand()
                    status_text.text(f"Hand {i+1}/{num_auto_hands}: Dealing cards...")
                    time.sleep(delay)
                    
                    # Deal cards
                    st.session_state.current_state = st.session_state.interactive_simulator.deal_cards()
                    
                    # If not in player_turn phase, the hand might already be complete (blackjack)
                    if st.session_state.current_state["phase"] == "player_turn":
                        status_text.text(f"Hand {i+1}/{num_auto_hands}: Player's turn...")
                        time.sleep(delay)
                        
                        # Play player's hand
                        while st.session_state.current_state["phase"] == "player_turn":
                            st.session_state.current_state = st.session_state.interactive_simulator.player_hit()
                            time.sleep(delay/2)
                    
                    # If needed, play dealer's hand
                    if st.session_state.current_state["phase"] == "dealer_turn":
                        status_text.text(f"Hand {i+1}/{num_auto_hands}: Dealer's turn...")
                        time.sleep(delay)
                        
                        while st.session_state.current_state["phase"] == "dealer_turn":
                            st.session_state.current_state = st.session_state.interactive_simulator.dealer_step()
                            time.sleep(delay/2)
                    
                    # Show result
                    status_text.text(f"Hand {i+1}/{num_auto_hands}: Complete!")
                    time.sleep(delay)
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / num_auto_hands)
                
                status_text.text(f"Auto-play complete! {num_auto_hands} hands played.")
                st.rerun()
    else:
        st.info("Initialize the simulator to begin playing hands interactively.")
        
    # Add documentation about the custom variant
    with st.expander("About This Blackjack Variant", expanded=False):
        st.markdown("""
        ### Custom Blackjack Variant Rules
        
        This simulator implements a custom variant of blackjack where:
        
        1. The player bets on the dealer's hand winning against their own hand
        2. The player hits using the same rules as the dealer by default (unless custom hit rules are specified)
        3. If player and dealer both bust, the hand pushes
        4. If player and dealer both get blackjack, the hand pushes
        5. A commission is taken from player wins (configurable %)
        
        ### How to Use the Hand-by-Hand Simulator
        
        1. Configure your game settings and click "Initialize Simulator"
        2. Use the "Deal New Hand" button to start a new hand
        3. During the player's turn, use "Hit" to take another card or "Stand" to end your turn
        4. During the dealer's turn, use "Dealer Step" to deal one card at a time to the dealer
        5. After the hand is complete, view the result and statistics, then click "Next Hand" to continue
        6. The "Auto-play" option allows you to simulate multiple hands automatically
        
        ### Understanding the Statistics
        
        The real-time statistics show:
        - House Edge: The mathematical advantage the house has over the player
        - Win/Loss/Push rates: The percentage of hands that result in each outcome
        - Bust rates: How often the player and dealer bust their hands
        
        These statistics become more accurate as more hands are played.
        """)

with tab3:
    st.markdown('<div class="section-header">Push Sidebet Simulation</div>', unsafe_allow_html=True)
    st.markdown("""
    This tab allows you to simulate the sidebet that pays when the player and dealer push (tie).
    You can choose to have payouts based on either the total hand value or the total number of cards.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Sidebet Configuration")
        
        sidebet_mode = st.radio(
            "Payout Mode",
            options=["Hand Total", "Card Count"],
            index=0,
            help="Choose to pay based on the total value of the hand or the total number of cards between player and dealer"
        )
        
        # Convert to the mode string used in the config
        sidebet_payout_mode = "total" if sidebet_mode == "Hand Total" else "cards"
        
        st.markdown("### Game Rules")
        
        num_hands = st.number_input(
            "Number of Hands to Simulate", 
            min_value=100, 
            max_value=100000000, 
            value=10000,
            step=1000,
            key="sidebet_num_hands"
        )
        
        num_decks = st.number_input(
            "Number of Decks", 
            min_value=1, 
            max_value=8, 
            value=6,
            key="sidebet_num_decks"
        )
        
        player_hits_soft_17 = st.checkbox("Player Hits Soft 17", value=False, key="sidebet_player_hits_soft17")
        dealer_hits_soft_17 = st.checkbox("Dealer Hits Soft 17", value=False, key="sidebet_dealer_hits_soft17")
        
        num_players = st.number_input(
            "Number of Players",
            min_value=1,
            max_value=7,
            value=1,
            key="sidebet_num_players"
        )
        
        hit_against_blackjack = st.checkbox(
            "Allow Hit Against Dealer Blackjack", 
            value=False,
            help="If checked, player can continue to hit when dealer has blackjack (will not result in a push if 21 is reached)"
        )
        
        shuffle_method = st.selectbox(
            "Shuffle Method",
            options=["Reshuffle at threshold", "Continuous shuffle"],
            index=0,
            key="sidebet_shuffle_method"
        )
        
        if shuffle_method == "Reshuffle at threshold":
            reshuffle_threshold = st.number_input(
                "Reshuffle Threshold (cards remaining)", 
                min_value=0, 
                max_value=104, 
                value=52,
                key="sidebet_reshuffle_threshold"
            )
        else:
            reshuffle_threshold = 0
    
    with col2:
        st.markdown("### Payout Configuration")
        
        if sidebet_mode == "Hand Total":
            # Hand total payouts
            st.markdown("#### Payout Multipliers by Hand Total")
            col_a, col_b = st.columns(2)
            
            with col_a:
                payout_17 = st.number_input("17 vs 17 Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_18 = st.number_input("18 vs 18 Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_19 = st.number_input("19 vs 19 Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_bust = st.number_input("Bust vs Bust Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
            
            with col_b:
                payout_20 = st.number_input("20 vs 20 Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_21 = st.number_input("21 vs 21 Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_bj = st.number_input("Blackjack vs Blackjack Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
            
            sidebet_payouts = {
                17: payout_17,
                18: payout_18,
                19: payout_19,
                20: payout_20,
                21: payout_21,
                'bust-bust': payout_bust,
                'blackjack-blackjack': payout_bj
            }
        else:
            # Card count payouts
            st.markdown("#### Payout Multipliers by Card Count")
            col_a, col_b = st.columns(2)
            
            with col_a:
                payout_4 = st.number_input("4 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_5 = st.number_input("5 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_6 = st.number_input("6 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_7 = st.number_input("7 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_8 = st.number_input("8 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
            
            with col_b:
                payout_9 = st.number_input("9 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_10 = st.number_input("10 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_11 = st.number_input("11 Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
                payout_12plus = st.number_input("12+ Cards Payout (X:1)", min_value=0, max_value=100, value=1, step=1)
            
            sidebet_payouts = {
                4: payout_4,
                5: payout_5,
                6: payout_6,
                7: payout_7,
                8: payout_8,
                9: payout_9,
                10: payout_10,
                11: payout_11,
                '12+': payout_12plus
            }
        
        st.markdown("### Simulation Options")
        save_results = st.checkbox("Save Simulation Results", value=True, key="sidebet_save_results")
        generate_visuals = st.checkbox("Generate Visualizations", value=True, key="sidebet_generate_visuals")
    
    run_sidebet_sim = st.button("Run Sidebet Simulation", type="primary", use_container_width=True)
    
    if run_sidebet_sim:
        with st.spinner('Running sidebet simulation... This may take a moment.'):
            # Create the simulation configuration
            sim_config = SimulationConfig(
                num_decks=num_decks,
                num_hands=num_hands,
                num_players=num_players,
                player_hit_soft_17=player_hits_soft_17,
                dealer_hit_soft_17=dealer_hits_soft_17,  
                reshuffle_cutoff=reshuffle_threshold if shuffle_method != "Continuous shuffle" else 0,
                hit_against_blackjack=hit_against_blackjack,
                sidebet_payout_mode=sidebet_payout_mode,
                sidebet_payouts=sidebet_payouts
            )
            
            # Save config if requested
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if save_results:
                os.makedirs("config", exist_ok=True)
                config_file = f"config/sidebet_config_{timestamp}.json"
                with open(config_file, "w") as f:
                    json.dump(sim_config.to_dict(), f, indent=4)
            
            # Run the simulation
            simulator = SidebetSimulator(sim_config)
            start_time = time.time()
            results = simulator.run_simulation()
            end_time = time.time()
            simulation_time = end_time - start_time
            
            # Generate reports
            report_generator = StreamlitReportGenerator(results, sim_config)
            
            if save_results:
                os.makedirs("results", exist_ok=True)
                report_generator.generate_detailed_csv(f"sidebet_sim_detailed_{timestamp}.csv")
                report_generator.generate_matrix_csv(f"sidebet_sim_matrix_{timestamp}.csv")
                report_generator.generate_summary(f"sidebet_sim_summary_{timestamp}.txt")
                # Generate the new detailed push matrix
                report_generator.generate_detailed_push_matrix_csv(f"sidebet_push_matrix_{timestamp}.csv")
            
            # Display results
            st.success(f"Simulation completed! {num_hands} hands simulated in {simulation_time:.2f} seconds.")
            
            st.markdown('<div class="section-header">Sidebet Simulation Results</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Total Push Rate", f"{results['total_pushes'] / results['total_bets'] * 100:.2f}%",
                        help="How often the player and dealer push")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Sidebet House Edge", f"{results['sidebet_edge']:.2f}%", 
                        help="House edge on the sidebet")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Main Bet House Edge", f"{results['house_edge']:.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Player Blackjacks", f"{results['player_blackjacks']} ({results['player_blackjacks'] / results['total_bets'] * 100:.2f}%)")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("Dealer Blackjacks", f"{results['dealer_blackjacks']} ({results['dealer_blackjacks'] / results['total_bets'] * 100:.2f}%)")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Display push breakdown
            st.markdown("### Push Breakdown")
            
            if sidebet_mode == "Hand Total":
                # Create a table for push breakdown by value
                pushes_by_value = results['pushes_by_value']
                total_pushes = results['total_pushes']
                
                value_data = []
                for value, count in pushes_by_value.items():
                    percentage = count / total_pushes * 100 if total_pushes > 0 else 0
                    payout = sidebet_payouts.get(value, 0) if isinstance(value, int) else sidebet_payouts.get(str(value), 0)
                    value_data.append({
                        "Value": value,
                        "Count": count,
                        "Percentage": f"{percentage:.2f}%",
                        "Payout": f"{payout}:1"
                    })
                
                value_df = pd.DataFrame(value_data)
                st.dataframe(value_df, use_container_width=True)
                
                # Plot the push distribution by value
                if generate_visuals:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    values = [str(v) for v in pushes_by_value.keys()]
                    counts = list(pushes_by_value.values())
                    
                    bars = ax.bar(values, counts)
                    
                    # Add value labels on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height}',
                                ha='center', va='bottom')
                    
                    ax.set_xlabel('Hand Value')
                    ax.set_ylabel('Number of Pushes')
                    ax.set_title('Push Distribution by Hand Value')
                    st.pyplot(fig)
            else:
                # Create a table for push breakdown by card count
                pushes_by_cards = results['pushes_by_card_count']
                total_pushes = results['total_pushes']
                
                card_data = []
                for cards, count in pushes_by_cards.items():
                    percentage = count / total_pushes * 100 if total_pushes > 0 else 0
                    payout = sidebet_payouts.get(cards, 0) if isinstance(cards, int) else sidebet_payouts.get(str(cards), 0)
                    card_data.append({
                        "Card Count": cards,
                        "Count": count,
                        "Percentage": f"{percentage:.2f}%",
                        "Payout": f"{payout}:1"
                    })
                
                card_df = pd.DataFrame(card_data)
                st.dataframe(card_df, use_container_width=True)
                
                # Plot the push distribution by card count
                if generate_visuals:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    cards = [str(c) for c in pushes_by_cards.keys()]
                    counts = list(pushes_by_cards.values())
                    
                    bars = ax.bar(cards, counts)
                    
                    # Add value labels on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height}',
                                ha='center', va='bottom')
                    
                    ax.set_xlabel('Total Cards')
                    ax.set_ylabel('Number of Pushes')
                    ax.set_title('Push Distribution by Card Count')
                    st.pyplot(fig)
            
            if save_results:
                st.info(f"""
                Results have been saved to the following files:
                - Configuration: `config/sidebet_config_{timestamp}.json`
                - Detailed CSV: `results/sidebet_sim_detailed_{timestamp}.csv`
                - Matrix CSV: `results/sidebet_sim_matrix_{timestamp}.csv`
                - Summary: `results/sidebet_sim_summary_{timestamp}.txt`
                - Detailed Push Matrix: `results/sidebet_push_matrix_{timestamp}.csv` (correlating hand totals and card counts)
                """)
    
    # Add a horizontal separator
    st.markdown("---")
    
    # Interactive Sidebet Simulator
    st.markdown('<div class="section-header">Interactive Sidebet Hand-by-Hand Simulation</div>', unsafe_allow_html=True)
    st.markdown("""
    This mode allows you to see each hand being played step-by-step and observe the sidebet outcomes
    as you play through individual hands.
    """)
    
    if "interactive_sidebet_simulator" not in st.session_state:
        st.session_state.interactive_sidebet_simulator = None
        st.session_state.sidebet_current_state = None
    
    with st.expander("Interactive Sidebet Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            int_sidebet_mode = st.radio(
                "Payout Mode",
                options=["Hand Total", "Card Count"],
                index=0,
                key="int_sidebet_mode",
                help="Choose to pay based on the total value of the hand or the total number of cards between player and dealer"
            )
            
            # Convert to the mode string used in the config
            int_sidebet_payout_mode = "total" if int_sidebet_mode == "Hand Total" else "cards"
            
            int_num_decks = st.number_input(
                "Number of Decks", 
                min_value=1, 
                max_value=8, 
                value=6,
                key="int_sidebet_num_decks"
            )
            
            int_player_hits_soft_17 = st.checkbox(
                "Player Hits Soft 17", 
                value=False,
                key="int_sidebet_player_hits_soft_17"
            )
            
            int_num_players = st.number_input(
                "Number of Players",
                min_value=1,
                max_value=7,
                value=1,
                key="int_sidebet_num_players"
            )
            
            int_hit_against_blackjack = st.checkbox(
                "Allow Hit Against Dealer Blackjack", 
                value=False,
                key="int_sidebet_hit_against_blackjack",
                help="If checked, player can continue to hit when dealer has blackjack (will not result in a push if 21 is reached)"
            )
                
        with col2:
            int_dealer_hits_soft_17 = st.checkbox(
                "Dealer Hits Soft 17", 
                value=False,
                key="int_sidebet_dealer_hits_soft_17"
            )
            
            int_shuffle_method = st.selectbox(
                "Shuffle Method",
                options=["Reshuffle at threshold", "Continuous shuffle"],
                index=0,
                key="int_sidebet_shuffle_method"
            )
            
            if int_shuffle_method == "Reshuffle at threshold":
                int_reshuffle_threshold = st.number_input(
                    "Reshuffle Threshold (cards remaining)", 
                    min_value=0, 
                    max_value=104, 
                    value=52,
                    key="int_sidebet_reshuffle_threshold"
                )
            else:
                int_reshuffle_threshold = 0
            
            # Add payouts based on the selected mode
            if int_sidebet_mode == "Hand Total":
                int_sidebet_payouts = {
                    17: st.number_input("17 vs 17 Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_17"),
                    18: st.number_input("18 vs 18 Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_18"),
                    19: st.number_input("19 vs 19 Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_19"),
                    20: st.number_input("20 vs 20 Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_20"),
                    21: st.number_input("21 vs 21 Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_21"),
                    'bust-bust': st.number_input("Bust vs Bust Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_bust"),
                    'blackjack-blackjack': st.number_input("BJ vs BJ Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_bj")
                }
            else:
                int_sidebet_payouts = {
                    4: st.number_input("4 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_4"),
                    5: st.number_input("5 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_5"),
                    6: st.number_input("6 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_6"),
                    7: st.number_input("7 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_7"),
                    8: st.number_input("8 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_8"),
                    9: st.number_input("9 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_9"),
                    10: st.number_input("10 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_10"),
                    11: st.number_input("11 Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_11"),
                    '12+': st.number_input("12+ Cards Payout", min_value=0, max_value=100, value=1, step=1, key="int_payout_12plus")
                }
            
        initialize_sidebet_button = st.button("Initialize Sidebet Simulator", use_container_width=True, key="init_sidebet_btn")
        
        if initialize_sidebet_button:
            sim_config = SimulationConfig(
                num_decks=int_num_decks,
                num_hands=100000000,
                num_players=int_num_players,
                player_hit_soft_17=int_player_hits_soft_17,
                dealer_hit_soft_17=int_dealer_hits_soft_17,  
                reshuffle_cutoff=int_reshuffle_threshold if int_shuffle_method != "Continuous shuffle" else 0,
                hit_against_blackjack=int_hit_against_blackjack,
                sidebet_payout_mode=int_sidebet_payout_mode,
                sidebet_payouts=int_sidebet_payouts
            )
            
            st.session_state.interactive_sidebet_simulator = InteractiveSidebetSimulator(sim_config)
            st.session_state.interactive_sidebet_simulator.setup()
            
            st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.start_new_hand()
            st.rerun()
    
    # Setup UI to deal specific hands if the simulator is initialized
    if st.session_state.interactive_sidebet_simulator is not None:
        with st.expander("Set Up Specific Hand", expanded=False):
            st.markdown("Use this section to set up a specific starting hand configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Player Cards")
                player_card1_rank = st.selectbox("Player Card 1 Rank", 
                                              ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"], 
                                              key="player_card1_rank")
                player_card1_suit = st.selectbox("Player Card 1 Suit", 
                                              ["Hearts", "Diamonds", "Clubs", "Spades"], 
                                              key="player_card1_suit")
                
                player_card2_rank = st.selectbox("Player Card 2 Rank", 
                                              ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"], 
                                              key="player_card2_rank")
                player_card2_suit = st.selectbox("Player Card 2 Suit", 
                                              ["Hearts", "Diamonds", "Clubs", "Spades"], 
                                              key="player_card2_suit")
            
            with col2:
                st.markdown("### Dealer Cards")
                dealer_card1_rank = st.selectbox("Dealer Card 1 Rank", 
                                              ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"], 
                                              key="dealer_card1_rank")
                dealer_card1_suit = st.selectbox("Dealer Card 1 Suit", 
                                              ["Hearts", "Diamonds", "Clubs", "Spades"], 
                                              key="dealer_card1_suit")
                
                dealer_card2_rank = st.selectbox("Dealer Card 2 Rank", 
                                              ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"], 
                                              key="dealer_card2_rank")
                dealer_card2_suit = st.selectbox("Dealer Card 2 Suit", 
                                              ["Hearts", "Diamonds", "Clubs", "Spades"], 
                                              key="dealer_card2_suit")
            
            setup_hand_btn = st.button("Set Up Specific Hand", use_container_width=True)
            
            if setup_hand_btn:
                from src.game.card import Card
                
                # Create the cards
                player_card1 = Card(player_card1_suit, player_card1_rank)
                player_card2 = Card(player_card2_suit, player_card2_rank)
                dealer_card1 = Card(dealer_card1_suit, dealer_card1_rank)
                dealer_card2 = Card(dealer_card2_suit, dealer_card2_rank)
                
                # Set up the hand
                st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.start_new_hand(
                    player_initial_cards=[player_card1, player_card2],
                    dealer_initial_cards=[dealer_card1, dealer_card2]
                )
                st.rerun()
    
    if st.session_state.interactive_sidebet_simulator is not None and st.session_state.sidebet_current_state is not None:
        st.markdown("### Interactive Simulation Controls")
        
        # Create a 2-column layout for the main controls
        col1, col2 = st.columns(2)
        
        with col1:
            # Input field for Hit
            st.text_input("Hit", placeholder="Hit", disabled=True)
        
        with col2:
            # Input field for Stand
            st.text_input("Stand", placeholder="Stand", disabled=True)
        
        # Create a row for the current phase information that spans the full width
        st.info(f"Current Phase: {st.session_state.sidebet_current_state['phase'].replace('_', ' ').title()}")
        
        # Create buttons row
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.session_state.sidebet_current_state["phase"] == "init":
                deal_button = st.button("Deal New Hand", key="sidebet_deal_btn", use_container_width=True, type="primary")
                if deal_button:
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.deal_cards()
                    st.rerun()
            elif st.session_state.sidebet_current_state["phase"] == "player_turn":
                hit_button = st.button("Hit", key="sidebet_hit_btn", use_container_width=True)
                if hit_button:
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.player_hit()
                    st.rerun()
        
        with col2:
            if st.session_state.sidebet_current_state["phase"] == "player_turn":
                stand_button = st.button("Stand", key="sidebet_stand_btn", use_container_width=True)
                if stand_button:
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.player_stand()
                    st.rerun()
            elif st.session_state.sidebet_current_state["phase"] == "dealer_turn":
                step_button = st.button("Dealer Step", key="sidebet_step_btn", use_container_width=True)
                if step_button:
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.dealer_step()
                    st.rerun()
            elif st.session_state.sidebet_current_state["phase"] == "result":
                next_hand_button = st.button("Next Hand", key="sidebet_next_hand_btn", use_container_width=True, type="primary")
                if next_hand_button:
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.start_new_hand()
                    st.rerun()
        
        # Show the current hand status
        st.markdown("### Current Hand")
        
        state = st.session_state.sidebet_current_state
        
        # Create a progress bar for player hand
        st.markdown('<div style="background-color: #22c55e; height: 4px; margin-bottom: 15px;"></div>', unsafe_allow_html=True)
        
        # Player hand section
        st.markdown("**Player Hand: {}**".format(state["player_hands"][0]["value"] if state["player_hands"] else ""))
        
        # Display player cards in a row
        if state["player_hands"]:
            player_hand = state["player_hands"][0]
            
            # Display cards horizontally
            cards_html = ""
            for card in player_hand["cards"]:
                cards_html += render_card(card)
            
            st.markdown(f'<div style="display: flex; gap: 10px; margin-bottom: 20px;">{cards_html}</div>', unsafe_allow_html=True)
            
        # Dealer hand section
        st.markdown("**Dealer Hand: {}**".format(
            state["dealer_hand"]["value"] if state["dealer_hand"] and state["phase"] in ["dealer_turn", "result"] else "?"
        ))
        
        # Create a progress bar for dealer hand
        st.markdown('<div style="background-color: #22c55e; height: 4px; margin-bottom: 15px;"></div>', unsafe_allow_html=True)
        
        # Display dealer cards in a row
        if state["dealer_hand"]:
            dealer_hand = state["dealer_hand"]
            
            # Display cards horizontally
            cards_html = ""
            
            # In dealer turn or result phase, show all cards
            if state["phase"] in ["dealer_turn", "result"]:
                for card in dealer_hand["cards"]:
                    cards_html += render_card(card)
            else:
                # In other phases, show only the first card and a face-down card
                if dealer_hand["cards"]:
                    cards_html += render_card(dealer_hand["cards"][0])
                    cards_html += '<div class="card" style="background-color: #6B7280; color: white; height: 60px; width: 40px; display: flex; justify-content: center; align-items: center; border-radius: 5px; font-weight: bold;">?</div>'
            
            st.markdown(f'<div style="display: flex; gap: 10px; margin-bottom: 20px;">{cards_html}</div>', unsafe_allow_html=True)
        
        # Show status information
        col1, col2 = st.columns(2)
        
        with col1:
            if state["player_hands"] and state["player_hands"][0]:
                player_hand = state["player_hands"][0]
                if player_hand["is_blackjack"]:
                    st.success("Player: Blackjack!")
                elif player_hand["is_bust"]:
                    st.error("Player: Bust!")
                elif player_hand["is_soft"]:
                    st.info("Player: Soft Hand")
                    
        with col2:
            if state["dealer_hand"] and state["phase"] in ["dealer_turn", "result"]:
                dealer_hand = state["dealer_hand"]
                if dealer_hand["is_blackjack"]:
                    st.success("Dealer: Blackjack!")
                elif dealer_hand["is_bust"]:
                    st.error("Dealer: Bust!")
                elif dealer_hand["is_soft"]:
                    st.info("Dealer: Soft Hand")
                
        # Show the result if available
        if state["phase"] == "result" and state["result"]:
            result = state["result"]
            result_class = "result-win" if result["result"] == "player_win" else ("result-loss" if result["result"] == "dealer_win" else "result-push")
            
            st.markdown(f'<div class="result-badge {result_class}">{result["display_result"]}</div>', unsafe_allow_html=True)
            
            # Display sidebet result if it's a push
            if state["sidebet_result"]["is_push"]:
                sidebet = state["sidebet_result"]
                sidebet_value = sidebet["value"]
                total_cards = sidebet["total_cards"]
                
                # Determine the payout based on simulator mode
                if st.session_state.interactive_sidebet_simulator.config.sidebet_payout_mode == "total":
                    # Payout based on total value
                    if sidebet["is_blackjack_push"]:
                        sidebet_outcome = "Blackjack Push"
                        payout_key = 'blackjack-blackjack'
                    elif sidebet["is_bust_push"]:
                        sidebet_outcome = "Bust Push"
                        payout_key = 'bust-bust'
                    else:
                        sidebet_outcome = f"{sidebet_value} Push"
                        payout_key = sidebet_value
                    
                    payout = st.session_state.interactive_sidebet_simulator.config.sidebet_payouts.get(payout_key, 0)
                else:
                    # Payout based on card count
                    sidebet_outcome = f"{total_cards} Cards Push"
                    payout_key = total_cards if total_cards < 12 else '12+'
                    payout = st.session_state.interactive_sidebet_simulator.config.sidebet_payouts.get(payout_key, 0)
                
                st.markdown(f"""
                <div style="background-color: #10B981; color: white; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>Sidebet Win!</strong> {sidebet_outcome} - Pays {payout}:1
                </div>
                """, unsafe_allow_html=True)
            elif state["phase"] == "result":
                st.markdown(f"""
                <div style="background-color: #EF4444; color: white; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>Sidebet Loss!</strong> No Push
                </div>
                """, unsafe_allow_html=True)
        
        # Display stats
        if "stats" in state:
            stats = state["stats"]
            
            st.markdown("### Statistics")
            
            # Create a 3x2 grid for the statistics that matches the layout in the screenshot
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Player Wins**")
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats['player_wins']}</h2>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Dealer Wins**")  
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats['dealer_wins']}</h2>", unsafe_allow_html=True)
                
            with col3:
                st.markdown("**Player Blackjacks**")
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats.get('player_blackjacks', 0)}</h2>", unsafe_allow_html=True)
                
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Hands Played**")
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats['total_hands']}</h2>", unsafe_allow_html=True)
                
            with col2:
                st.markdown("**Pushes**")
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats['pushes']}</h2>", unsafe_allow_html=True)
                
            with col3:
                st.markdown("**Dealer Blackjacks**")
                st.markdown(f"<h2 style='margin:0; padding:0;'>{stats.get('dealer_blackjacks', 0)}</h2>", unsafe_allow_html=True)
            
            # Sidebet stats
            if "sidebet_stats" in stats and stats["total_hands"] > 0:
                sidebet_stats = stats["sidebet_stats"]
                
                st.markdown("### Sidebet Statistics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Pushes", f"{sidebet_stats['total_pushes']} ({sidebet_stats['total_pushes']/stats['total_hands']*100:.1f}%)" if stats["total_hands"] > 0 else "0")
                
                with col2:
                    edge = sidebet_stats.get("edge")
                    st.metric("Sidebet Edge", f"{edge:.2f}%" if edge is not None else "N/A")
                
                # Show push breakdown
                if st.session_state.interactive_sidebet_simulator.config.sidebet_payout_mode == "total":
                    # Create a table for push breakdown by value
                    if sidebet_stats.get("by_value"):
                        pushes_by_value = sidebet_stats["by_value"]
                        st.markdown("#### Pushes by Hand Value")
                        value_data = []
                        for value, count in pushes_by_value.items():
                            value_data.append({
                                "Value": value,
                                "Count": count
                            })
                        
                        value_df = pd.DataFrame(value_data)
                        st.dataframe(value_df)
                else:
                    # Create a table for push breakdown by card count
                    if sidebet_stats.get("by_cards"):
                        pushes_by_cards = sidebet_stats["by_cards"]
                        st.markdown("#### Pushes by Card Count")
                        card_data = []
                        for cards, count in pushes_by_cards.items():
                            card_data.append({
                                "Card Count": cards,
                                "Count": count
                            })
                        
                        card_df = pd.DataFrame(card_data)
                        st.dataframe(card_df)
        
        # Hand history for sidebet
        if state["history_length"] > 0:
            with st.expander("Hand History", expanded=False):
                history = st.session_state.interactive_sidebet_simulator.get_hand_history()
                history_df = pd.DataFrame(history)
                
                history_df["player_cards"] = history_df["player_hand"].apply(lambda x: ", ".join(x))
                history_df["dealer_cards"] = history_df["dealer_hand"].apply(lambda x: ", ".join(x))
                
                history_df["outcome"] = history_df["result"].map({
                    "player_win": "Player Win", 
                    "dealer_win": "Dealer Win",
                    "push": "Push"
                })
                
                display_df = history_df[["player_value", "dealer_value", "outcome", "player_cards", "dealer_cards"]]
                display_df.index = display_df.index + 1  # 1-based indexing for hand number
                
                st.dataframe(display_df.iloc[::-1])
        
        # Auto-play for sidebet
        with st.expander("Auto-play Options", expanded=False):
            st.write("Set up auto-play to automatically simulate multiple hands in succession.")
            
            num_auto_hands = st.number_input(
                "Number of Hands to Auto-Play", 
                min_value=1,
                max_value=100,
                value=10,
                key="auto_play_hands_2"
            )
            
            delay = st.slider(
                "Delay Between Steps (seconds)",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                key="delay_slider_2"
            )
            
            auto_play = st.button("Start Auto-Play", key="sidebet_auto_play_btn")
            
            if auto_play:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(num_auto_hands):
                    # Start a new hand
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.start_new_hand()
                    status_text.text(f"Hand {i+1}/{num_auto_hands}: Dealing cards...")
                    time.sleep(delay)
                    
                    # Deal cards
                    st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.deal_cards()
                    
                    # If not in player_turn phase, the hand might already be complete (blackjack)
                    if st.session_state.sidebet_current_state["phase"] == "player_turn":
                        status_text.text(f"Hand {i+1}/{num_auto_hands}: Player's turn...")
                        time.sleep(delay)
                        
                        # Play player's hand
                        while st.session_state.sidebet_current_state["phase"] == "player_turn":
                            st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.player_hit()
                            time.sleep(delay/2)
                    
                    # If needed, play dealer's hand
                    if st.session_state.sidebet_current_state["phase"] == "dealer_turn":
                        status_text.text(f"Hand {i+1}/{num_auto_hands}: Dealer's turn...")
                        time.sleep(delay)
                        
                        while st.session_state.sidebet_current_state["phase"] == "dealer_turn":
                            st.session_state.sidebet_current_state = st.session_state.interactive_sidebet_simulator.dealer_step()
                            time.sleep(delay/2)
                    
                    # Show result
                    status_text.text(f"Hand {i+1}/{num_auto_hands}: Complete!")
                    time.sleep(delay)
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / num_auto_hands)
                
                status_text.text(f"Auto-play complete! {num_auto_hands} hands played.")
                st.rerun()
    else:
        st.info("Initialize the simulator to begin playing hands interactively.")


with tab4:
    st.markdown('<div class="section-header">Data Visualization</div>', unsafe_allow_html=True)
    
    if "latest_results" in st.session_state and st.session_state.latest_results.get("detailed_df") is not None:
        detailed_df = st.session_state.latest_results["detailed_df"]
        
        st.markdown("### Select Visualization Type")
        viz_options = [
            "Hand Outcomes", 
            "Total Value Distribution", 
            "Win/Loss by Player Total", 
            "Dealer Bust Analysis", 
            "Outcome Matrix Heatmap",
            "Player vs Dealer Total Comparison",
            "Custom Analysis"
        ]
        viz_type = st.selectbox("Select Visualization", viz_options)
        
        if viz_type == "Hand Outcomes":
            fig, ax = plt.subplots(figsize=(10, 6))
            outcomes = detailed_df["result"].value_counts().reset_index()
            outcomes.columns = ["Outcome", "Count"]
            
            sns.barplot(x="Outcome", y="Count", data=outcomes, palette="viridis", ax=ax)
            ax.set_title("Distribution of Hand Outcomes")
            ax.set_ylabel("Number of Hands")
            ax.tick_params(axis='x', rotation=45)
            
            st.pyplot(fig)
            
            st.dataframe(
                outcomes.assign(Percentage=lambda x: (x["Count"] / x["Count"].sum() * 100).round(2)).assign(
                    Percentage=lambda x: x["Percentage"].astype(str) + '%'
                )
            )
            
        elif viz_type == "Total Value Distribution":
            fig, ax = plt.subplots(1, 2, figsize=(15, 6))
            
            sns.histplot(detailed_df["player_total"], kde=True, bins=20, ax=ax[0])
            ax[0].set_title("Player Hand Total Distribution")
            ax[0].set_xlabel("Player Hand Total")
            
            sns.histplot(detailed_df["dealer_total"], kde=True, bins=20, ax=ax[1])
            ax[1].set_title("Dealer Hand Total Distribution")
            ax[1].set_xlabel("Dealer Hand Total")
            
            plt.tight_layout()
            st.pyplot(fig)
            
        elif viz_type == "Win/Loss by Player Total":
            fig, ax = plt.subplots(figsize=(12, 7))
            
            pivot_data = detailed_df.pivot_table(
                index="player_total", 
                columns="result", 
                aggfunc="size", 
                fill_value=0
            )

            pivot_pct = pivot_data.div(pivot_data.sum(axis=1), axis=0) * 100
            
            pivot_pct.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")
            ax.set_title("Outcome by Player Total")
            ax.set_xlabel("Player Hand Total")
            ax.set_ylabel("Percentage")
            ax.legend(title="Outcome")
            
            plt.tight_layout()
            st.pyplot(fig)
            
        elif viz_type == "Dealer Bust Analysis":
            fig, ax = plt.subplots(figsize=(10, 6))
            
            dealer_busts = detailed_df[detailed_df["dealer_total"] > 21]
            
            if len(dealer_busts) > 0:
                # Check if dealer_upcard column exists and has meaningful values
                if "dealer_upcard" in detailed_df.columns and detailed_df["dealer_upcard"].nunique() > 1:
                    bust_by_upcard = dealer_busts.groupby("dealer_upcard").size().reset_index()
                    bust_by_upcard.columns = ["Dealer Upcard", "Bust Count"]
                    
                    total_by_upcard = detailed_df.groupby("dealer_upcard").size().reset_index()
                    total_by_upcard.columns = ["Dealer Upcard", "Total Count"]
                
                    bust_analysis = pd.merge(bust_by_upcard, total_by_upcard, on="Dealer Upcard")
                    bust_analysis["Bust Percentage"] = (bust_analysis["Bust Count"] / bust_analysis["Total Count"] * 100).round(2)
                    
                    sns.barplot(x="Dealer Upcard", y="Bust Percentage", data=bust_analysis, palette="viridis", ax=ax)
                    ax.set_title("Dealer Bust Percentage by Upcard")
                    ax.set_ylabel("Bust Percentage (%)")
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    st.dataframe(bust_analysis)
                else:
                    # If dealer_upcard is not usable, create a simpler analysis
                    st.write(f"Total dealer busts: {len(dealer_busts)} ({len(dealer_busts)/len(detailed_df)*100:.2f}%)")
                    st.info("Detailed upcard analysis not available - dealer upcard data is missing or uniform.")
            else:
                st.info("No dealer busts found in this simulation.")
        
        elif viz_type == "Outcome Matrix Heatmap":
            matrix_df = pd.crosstab(
                detailed_df["player_total"], 
                detailed_df["dealer_total"], 
                values=detailed_df["result"].apply(lambda x: 1 if x == "Win" else (0 if x == "Push" else -1)),
                aggfunc="mean"
            ).fillna(0)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(
                matrix_df, 
                annot=True, 
                cmap="RdYlGn", 
                center=0, 
                ax=ax,
                fmt=".2f"
            )
            ax.set_title("Player vs Dealer Total Outcome Matrix\n(1=Player Win, 0=Push, -1=Dealer Win)")
            ax.set_xlabel("Dealer Total")
            ax.set_ylabel("Player Total")
            
            plt.tight_layout()
            st.pyplot(fig)
            
            st.write("##### Hand Total Frequency Matrix")
            freq_matrix = pd.crosstab(
                detailed_df["player_total"], 
                detailed_df["dealer_total"]
            )
            
            fig2, ax2 = plt.subplots(figsize=(12, 8))
            sns.heatmap(
                freq_matrix, 
                annot=True, 
                cmap="YlGnBu", 
                ax=ax2
            )
            ax2.set_title("Frequency of Player vs Dealer Hand Totals")
            ax2.set_xlabel("Dealer Total")
            ax2.set_ylabel("Player Total")
            
            plt.tight_layout()
            st.pyplot(fig2)
            
        elif viz_type == "Player vs Dealer Total Comparison":
            # Create violin plot comparing player and dealer totals
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create a new dataframe for the violin plot
            violin_data = pd.DataFrame({
                "Total": detailed_df["player_total"].tolist() + detailed_df["dealer_total"].tolist(),
                "Role": ["Player"] * len(detailed_df) + ["Dealer"] * len(detailed_df)
            })
            
            # Plot
            sns.violinplot(x="Role", y="Total", data=violin_data, inner="quartile", ax=ax)
            ax.set_title("Distribution of Hand Totals: Player vs Dealer")
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Additional statistics
            st.write("##### Hand Total Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Player Total Stats**")
                st.write(f"Mean: {detailed_df['player_total'].mean():.2f}")
                st.write(f"Median: {detailed_df['player_total'].median()}")
                st.write(f"Max: {detailed_df['player_total'].max()}")
                st.write(f"Min: {detailed_df['player_total'].min()}")
                
            with col2:
                st.write("**Dealer Total Stats**")
                st.write(f"Mean: {detailed_df['dealer_total'].mean():.2f}")
                st.write(f"Median: {detailed_df['dealer_total'].median()}")
                st.write(f"Max: {detailed_df['dealer_total'].max()}")
                st.write(f"Min: {detailed_df['dealer_total'].min()}")
        
        elif viz_type == "Custom Analysis":
            st.markdown("### Custom Analysis")
            st.markdown("Create your own analysis by selecting variables to plot.")
            
            # Filtering options
            with st.expander("Data Filtering"):
                # Outcome filter
                outcome_filter = st.multiselect(
                    "Filter by outcome:", 
                    options=sorted(detailed_df["result"].unique()),
                    default=[]
                )
                
                # Player total range
                player_min = int(detailed_df["player_total"].min())
                player_max = int(detailed_df["player_total"].max())
                player_range = st.slider(
                    "Player total range:", 
                    min_value=player_min,
                    max_value=player_max,
                    value=(player_min, player_max)
                )
                
                # Dealer total range
                dealer_min = int(detailed_df["dealer_total"].min())
                dealer_max = int(detailed_df["dealer_total"].max())
                dealer_range = st.slider(
                    "Dealer total range:", 
                    min_value=dealer_min,
                    max_value=dealer_max,
                    value=(dealer_min, dealer_max)
                )
                
                # Apply filters
                filtered_df = detailed_df.copy()
                
                if outcome_filter:
                    filtered_df = filtered_df[filtered_df["result"].isin(outcome_filter)]
                
                filtered_df = filtered_df[
                    (filtered_df["player_total"] >= player_range[0]) & 
                    (filtered_df["player_total"] <= player_range[1]) &
                    (filtered_df["dealer_total"] >= dealer_range[0]) & 
                    (filtered_df["dealer_total"] <= dealer_range[1])
                ]
                
                st.write(f"Filtered data contains {len(filtered_df)} hands")
            
            col1, col2 = st.columns(2)
            with col1:
                x_var = st.selectbox("X-Axis Variable", filtered_df.columns)
            with col2:
                y_var = st.selectbox("Y-Axis Variable", [None] + list(filtered_df.columns), index=0)
            
            plot_type = st.selectbox(
                "Plot Type", 
                ["Bar Chart", "Scatter Plot", "Line Chart", "Histogram", "Box Plot", "Violin Plot", "Heatmap"]
            )
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if plot_type == "Bar Chart":
                if y_var:
                    sns.barplot(x=x_var, y=y_var, data=filtered_df, ax=ax)
                else:
                    filtered_df[x_var].value_counts().plot(kind='bar', ax=ax)
            elif plot_type == "Scatter Plot":
                if y_var:
                    sns.scatterplot(x=x_var, y=y_var, data=filtered_df, ax=ax)
                else:
                    st.error("Scatter plot requires both X and Y variables.")
            elif plot_type == "Line Chart":
                if y_var:
                    sns.lineplot(x=x_var, y=y_var, data=filtered_df, ax=ax)
                else:
                    filtered_df[x_var].value_counts().sort_index().plot(kind='line', ax=ax)
            elif plot_type == "Histogram":
                sns.histplot(filtered_df[x_var], kde=True, ax=ax)
            elif plot_type == "Box Plot":
                if y_var:
                    sns.boxplot(x=x_var, y=y_var, data=filtered_df, ax=ax)
                else:
                    sns.boxplot(y=x_var, data=filtered_df, ax=ax)
            elif plot_type == "Violin Plot":
                if y_var:
                    sns.violinplot(x=x_var, y=y_var, data=filtered_df, ax=ax)
                else:
                    sns.violinplot(y=x_var, data=filtered_df, ax=ax)
            elif plot_type == "Heatmap":
                if y_var:
                    # Create a crosstab/pivot for the heatmap
                    heatmap_data = pd.crosstab(
                        filtered_df[x_var], 
                        filtered_df[y_var]
                    )
                    sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", ax=ax)
                else:
                    st.error("Heatmap requires both X and Y variables.")
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Show filtered data
            with st.expander("View Filtered Data"):
                st.dataframe(filtered_df)
    else:
        if "latest_results" in st.session_state:
            st.info("Run a simulation with 'Generate Visualizations' enabled to see charts here.")
        else:
            st.info("Run a simulation to see visualizations here.")

with tab5:
    st.markdown('<div class="section-header">Previous Simulation Results</div>', unsafe_allow_html=True)
    
    # Get list of previous simulation files
    results = load_simulation_results()
    
    if results:
        # Create selection method tabs
        sel_tab1, sel_tab2 = st.tabs(["Select by Date", "Compare Simulations"])
        
        with sel_tab1:
            # Display dropdown to select result
            result_options = {f"{r['timestamp']}": i for i, r in enumerate(results)}
            selected_result_key = st.selectbox("Select simulation result:", 
                                            options=list(result_options.keys()),
                                            format_func=lambda x: f"Simulation {x}")
            
            selected_result = results[result_options[selected_result_key]]
            timestamp = selected_result['timestamp'];
            
            # Display summary
            if selected_result['summary_file']:
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown(f"### Summary for Simulation {timestamp}")
                
                results_dir = "results"
                summary_path = os.path.join(results_dir, selected_result['summary_file'])
                if os.path.exists(summary_path):
                    with open(summary_path, 'r') as f:
                        summary_content = f.read()
                    st.text(summary_content)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Check for corresponding config file
            config_file = selected_result['config_file']
            if config_file:
                config_path = os.path.join("config", config_file)
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    
                    st.markdown("### Simulation Configuration")
                    st.json(config)
            
            # Analysis of selected simulation
            if selected_result['detailed_file']:
                detailed_path = os.path.join("results", selected_result['detailed_file'])
                if os.path.exists(detailed_path):
                    detailed_df = pd.read_csv(detailed_path)
                    
                    st.markdown("### Visualization")
                    
                    # Choose visualization type for past simulation
                    past_viz_type = st.selectbox(
                        "Select Visualization", 
                        ["Hand Outcomes", "Total Value Distribution", "Win/Loss Analysis", "Dealer Bust Analysis"],
                        key="past_viz_selector"
                    )
                    
                    if past_viz_type == "Hand Outcomes":
                        fig, ax = plt.subplots(figsize=(10, 6))
                        outcomes = detailed_df["result"].value_counts().reset_index()
                        outcomes.columns = ["Outcome", "Count"]
                        
                        sns.barplot(x="Outcome", y="Count", data=outcomes, palette="viridis", ax=ax)
                        ax.set_title("Distribution of Hand Outcomes")
                        ax.set_ylabel("Number of Hands")
                        ax.tick_params(axis='x', rotation=45)
                        
                        st.pyplot(fig)
                    
                    elif past_viz_type == "Total Value Distribution":
                        fig, ax = plt.subplots(1, 2, figsize=(15, 6))
                        
                        # Player totals
                        sns.histplot(detailed_df["player_total"], kde=True, bins=20, ax=ax[0])
                        ax[0].set_title("Player Hand Total Distribution")
                        ax[0].set_xlabel("Player Hand Total")
                        
                        # Dealer totals
                        sns.histplot(detailed_df["dealer_total"], kde=True, bins=20, ax=ax[1])
                        ax[1].set_title("Dealer Hand Total Distribution")
                        ax[1].set_xlabel("Dealer Hand Total")
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                    
                    elif past_viz_type == "Win/Loss Analysis":
                        fig, ax = plt.subplots(figsize=(12, 7))
                        
                        # Create a pivot table of outcomes by player total
                        pivot_data = detailed_df.pivot_table(
                            index="player_total", 
                            columns="result", 
                            aggfunc="size", 
                            fill_value=0
                        )
                        
                        # Convert to percentages
                        pivot_pct = pivot_data.div(pivot_data.sum(axis=1), axis=0) * 100
                        
                        # Plot stacked bar chart
                        pivot_pct.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")
                        ax.set_title("Outcome by Player Total")
                        ax.set_xlabel("Player Hand Total")
                        ax.set_ylabel("Percentage")
                        ax.legend(title="Outcome")
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                    
                    elif past_viz_type == "Dealer Bust Analysis":
                        # Similar to above dealer bust analysis
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # Filter for dealer busts
                        dealer_busts = detailed_df[detailed_df["dealer_total"] > 21]
                        
                        if len(dealer_busts) > 0:
                            # Check if dealer_upcard column exists and has meaningful values
                            if "dealer_upcard" in detailed_df.columns and detailed_df["dealer_upcard"].nunique() > 1:
                                bust_by_upcard = dealer_busts.groupby("dealer_upcard").size().reset_index()
                                bust_by_upcard.columns = ["Dealer Upcard", "Bust Count"]
                                
                                # Calculate total hands for each upcard
                                total_by_upcard = detailed_df.groupby("dealer_upcard").size().reset_index()
                                total_by_upcard.columns = ["Dealer Upcard", "Total Count"]
                                
                                # Merge and calculate percentages
                                bust_analysis = pd.merge(bust_by_upcard, total_by_upcard, on="Dealer Upcard")
                                bust_analysis["Bust Percentage"] = (bust_analysis["Bust Count"] / bust_analysis["Total Count"] * 100).round(2)
                                
                                # Plot
                                sns.barplot(x="Dealer Upcard", y="Bust Percentage", data=bust_analysis, palette="viridis", ax=ax)
                                ax.set_title("Dealer Bust Percentage by Upcard")
                                ax.set_ylabel("Bust Percentage (%)")
                                
                                plt.tight_layout()
                                st.pyplot(fig)
                                
                                # Show the raw data
                                st.dataframe(bust_analysis)
                            else:
                                # If dealer_upcard is not usable, create a simpler analysis
                                st.write(f"Total dealer busts: {len(dealer_busts)} ({len(dealer_busts)/len(detailed_df)*100:.2f}%)")
                                st.info("Detailed upcard analysis not available - dealer upcard data is missing or uniform.")
                        else:
                            st.info("No dealer busts found in this simulation.")
            
            # Check for CSV files and allow download
            detailed_csv = selected_result['detailed_file']
            matrix_csv = selected_result['matrix_file']
            
            st.markdown("### Download Simulation Data")
            col1, col2 = st.columns(2)
            
            if detailed_csv:
                detailed_path = os.path.join("results", detailed_csv)
                if os.path.exists(detailed_path):
                    with col1:
                        with open(detailed_path, "r") as f:
                            csv_content = f.read()
                        st.download_button(
                            label="Download Detailed CSV",
                            data=csv_content,
                            file_name=detailed_csv,
                            mime="text/csv"
                        )
            
            if matrix_csv:
                matrix_path = os.path.join("results", matrix_csv)
                if os.path.exists(matrix_path):
                    with col2:
                        with open(matrix_path, "r") as f:
                            csv_content = f.read()
                        st.download_button(
                            label="Download Matrix CSV",
                            data=csv_content,
                            file_name=matrix_csv,
                            mime="text/csv"
                        )
        
        with sel_tab2:
            st.markdown("### Compare Multiple Simulations")
            
            # Allow selection of multiple simulations
            selected_simulations = st.multiselect(
                "Select simulations to compare:", 
                options=[f"Simulation {r['timestamp']}" for r in results],
                default=[]
            )
            
            if selected_simulations:
                # Get selected simulation data
                selected_data = []
                for sim_str in selected_simulations:
                    sim_timestamp = sim_str.replace("Simulation ", "")
                    sim_result = next((r for r in results if r['timestamp'] == sim_timestamp), None)
                    
                    if sim_result and sim_result['summary_file']:
                        # Get config
                        config_data = {}
                        if sim_result['config_file']:
                            config_path = os.path.join("config", sim_result['config_file'])
                            if os.path.exists(config_path):
                                with open(config_path, "r") as f:
                                    config_data = json.load(f)
                        
                        # Load detailed results for metrics
                        sim_metrics = {"timestamp": sim_timestamp, "config": config_data}
                        
                        if sim_result['detailed_file']:
                            detailed_path = os.path.join("results", sim_result['detailed_file'])
                            if os.path.exists(detailed_path):
                                df = pd.read_csv(detailed_path)
                                
                                # Calculate metrics
                                total_hands = len(df)
                                player_wins = len(df[df["result"] == "Win"])
                                dealer_wins = len(df[df["result"] == "Loss"])
                                pushes = len(df[df["result"] == "Push"])
                                player_busts = len(df[df["player_total"] > 21])
                                dealer_busts = len(df[df["dealer_total"] > 21])
                                
                                # Add metrics to data
                                sim_metrics.update({
                                    "total_hands": total_hands,
                                    "player_win_rate": (player_wins / total_hands) * 100,
                                    "dealer_win_rate": (dealer_wins / total_hands) * 100,
                                    "push_rate": (pushes / total_hands) * 100,
                                    "player_bust_rate": (player_busts / total_hands) * 100,
                                    "dealer_bust_rate": (dealer_busts / total_hands) * 100
                                })
                                
                                # Calculate house edge from the detailed data
                                win_multiplier = 1.0 - (config_data.get("commission", 5.0) / 100.0)
                                net_win = (player_wins * win_multiplier) - dealer_wins
                                house_edge = -net_win / total_hands * 100
                                
                                sim_metrics["house_edge"] = house_edge
                        
                        selected_data.append(sim_metrics)
                
                # Create comparison table
                if selected_data:
                    comparison_df = pd.DataFrame(selected_data)
                    
                    # Format the columns for display
                    display_columns = [
                        "timestamp", "house_edge", "player_win_rate", "dealer_win_rate", 
                        "push_rate", "player_bust_rate", "dealer_bust_rate"
                    ]
                    
                    # Extract key config values for comparison
                    comparison_df["num_decks"] = comparison_df["config"].apply(lambda x: x.get("num_decks", "N/A"))
                    comparison_df["dealer_hits_soft_17"] = comparison_df["config"].apply(lambda x: x.get("dealer_hit_soft_17", "N/A"))
                    comparison_df["commission"] = comparison_df["config"].apply(lambda x: x.get("commission_pct", "N/A"))
                    
                    display_columns = ["timestamp", "num_decks", "dealer_hits_soft_17", "commission", 
                                      "house_edge", "player_win_rate", "dealer_win_rate"]
                    
                    # Display comparison table
                    st.write("#### Simulation Comparison")
                    
                    # Format the comparison dataframe
                    formatted_df = comparison_df[display_columns].copy()
                    for col in ["house_edge", "player_win_rate", "dealer_win_rate"]:
                        if col in formatted_df.columns:
                            formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)
                    
                    st.dataframe(formatted_df)
                    
                    # Create comparison chart
                    st.write("#### Metric Comparison")
                    
                    metric_to_compare = st.selectbox(
                        "Select metric to compare:", 
                        options=["house_edge", "player_win_rate", "dealer_win_rate", 
                                "push_rate", "player_bust_rate", "dealer_bust_rate"]
                    )
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Create bar chart with simulation labels
                    comparison_df_chart = comparison_df.copy()
                    comparison_df_chart["simulation"] = comparison_df_chart["timestamp"].apply(
                        lambda x: f"Sim {x[-6:]}"  # Just show last 6 digits for readability
                    )
                    
                    sns.barplot(
                        x="simulation", 
                        y=metric_to_compare, 
                        data=comparison_df_chart,
                        ax=ax
                    )
                    
                    # Add labels
                    for i, v in enumerate(comparison_df_chart[metric_to_compare]):
                        ax.text(
                            i, 
                            v + 0.1, 
                            f"{v:.2f}%", 
                            ha='center', 
                            fontweight='bold'
                        )
                    
                    # Format chart
                    ax.set_title(f"Comparison of {metric_to_compare.replace('_', ' ').title()}")
                    ax.set_ylabel("Percentage (%)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    st.pyplot(fig)
    else:
        st.info("No previous simulation results found. Run simulations with 'Save Results' enabled to store them.")

# Footer
st.markdown("---")
st.markdown("Blackjack Simulator © 2025 | Created with Streamlit")