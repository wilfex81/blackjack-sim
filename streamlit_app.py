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

# Add the project root to the path so we can use absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.config import SimulationConfig
from src.simulation.simulator import BlackjackSimulator
from src.reporting.report_generator import ReportGenerator

# Custom ReportGenerator for the Streamlit app
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
            
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Calculate percentages
        total_hands = self.results['total_bets']
        player_win_pct = 100 * self.results['player_wins'] / total_hands if total_hands > 0 else 0
        dealer_win_pct = 100 * self.results['dealer_wins'] / total_hands if total_hands > 0 else 0
        push_pct = 100 * self.results['pushes'] / total_hands if total_hands > 0 else 0
        
        # Format summary text
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
            f"",
            f"House edge: {self.results['house_edge']:.4f}%"
        ]
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write("\n".join(summary))
            
        print(f"Summary report saved to {filepath}")
        return filepath
        
    def generate_matrix_csv(self, filename):
        """Generate a CSV file with the outcome matrix data"""
        if not self.results:
            raise ValueError("No simulation results available to report")
            
        # Create results directory if it doesn't exist
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
    
    def generate_detailed_csv(self, filename):
        """Generate a detailed CSV report with all outcomes"""
        if not self.results:
            raise ValueError("No simulation results available to report")
            
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            
        filepath = os.path.join(self.results_dir, filename)
        
        # Get results details
        outcome_details = self.results['outcome_details']
        
        # Prepare data for CSV
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
    
    def get_detailed_dataframe(self):
        """Create a pandas DataFrame from the detailed outcome data for visualization"""
        if not self.results:
            raise ValueError("No simulation results available to report")
            
        # Get results details
        outcome_details = self.results['outcome_details']
        
        # Prepare data for DataFrame
        detailed_data = []
        
        # Add all player vs dealer outcomes
        for (player_total, dealer_total, result), count in outcome_details.items():
            win_loss = "Win" if result == "player_win" else ("Loss" if result == "dealer_win" else "Push")
            
            # Create multiple rows for each outcome (one per hand)
            for _ in range(count):
                detailed_data.append({
                    'player_total': player_total,
                    'dealer_total': dealer_total,
                    'result': win_loss,
                    'dealer_upcard': 0  # Placeholder
                })
        
        # Create the DataFrame
        import pandas as pd
        return pd.DataFrame(detailed_data)

# Set page configuration
st.set_page_config(
    page_title="Blackjack Simulator",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
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

# Title and introduction
st.markdown('<div class="main-header">Blackjack Simulator</div>', unsafe_allow_html=True)
st.markdown("""
This application allows you to configure and run blackjack simulations to analyze house edge 
and game dynamics under various rule configurations. You can adjust parameters, 
run simulations, and visualize the results.
""")

# Load existing configs and results for use in the app
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
            # Look for summary text files
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
    
    # Sort results by timestamp (newest first)
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    return results

# Main navigation - using tabs
tab1, tab2, tab3 = st.tabs(["Run Simulation", "Data Visualization", "Previous Results"])

# Run Simulation Tab
with tab1:
    st.markdown('<div class="section-header">Configure and Run Simulation</div>', unsafe_allow_html=True)
    
    # Configuration form with all advanced options
    with st.form("simulation_config_advanced"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Game Rules")
            
            num_hands = st.number_input(
                "Number of Hands to Simulate", 
                min_value=100, 
                max_value=1000000, 
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
                options=["1:1", "3:2", "2:1"],
                index=0
            )
            
            st.markdown("### Simulation Options")
            
            save_results = st.checkbox("Save Simulation Results", value=True)
            generate_visuals = st.checkbox("Generate Visualizations", value=True)
        
        # Advanced Strategy Options
        advanced_expander = st.expander("Advanced Strategy Options")
        with advanced_expander:
            custom_hit_rules = st.text_area(
                "Custom Hit Rules", 
                value="",
                help="Format: 'hard:16,10:hit;soft:17:hit' means hit on hard 16 when dealer shows 10, and hit on soft 17"
            )
        
        submit_button = st.form_submit_button("Run Simulation")

    # Function to run the simulation with all advanced options
    def run_simulation_advanced(config):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Parse custom hit rules if provided
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
        
        # Create configuration object with all advanced parameters
        sim_config = SimulationConfig(
            num_decks=config["num_decks"],
            num_hands=config["num_hands"],
            player_hit_soft_17=config["player_hits_soft_17"],
            dealer_hit_soft_17=config["dealer_hits_soft_17"],  
            reshuffle_cutoff=config.get("reshuffle_threshold", 52) if config["shuffle_method"] != "Continuous shuffle" else 0,
            commission_pct=config["commission"],
            blackjack_payout=float(config["blackjack_payout"].split(":")[0]),
            num_players=config.get("num_players", 1),
            player_hit_rules=hit_rules_dict if hit_rules_dict else None
        )
        
        # Save config
        if config["save_results"]:
            os.makedirs("config", exist_ok=True)
            config_file = f"config/simulation_config_{timestamp}.json"
            with open(config_file, "w") as f:
                json.dump(sim_config.to_dict(), f, indent=4)
        
        # Create and run simulator
        simulator = BlackjackSimulator(sim_config)
        start_time = time.time()
        results = simulator.run_simulation()
        end_time = time.time()
        simulation_time = end_time - start_time
        
        # Generate reports
        report_generator = StreamlitReportGenerator(results, sim_config)
        
        if config["save_results"]:
            os.makedirs("results", exist_ok=True)
            report_generator.generate_detailed_csv(f"blackjack_sim_detailed_{timestamp}.csv")
            report_generator.generate_matrix_csv(f"blackjack_sim_matrix_{timestamp}.csv")
            report_generator.generate_summary(f"blackjack_sim_summary_{timestamp}.txt")
        
        # Calculate metrics from results
        total_hands = results['total_bets']
        player_win_rate = results['player_wins'] / total_hands if total_hands > 0 else 0
        dealer_win_rate = results['dealer_wins'] / total_hands if total_hands > 0 else 0
        push_rate = results['pushes'] / total_hands if total_hands > 0 else 0
        player_bust_rate = results['player_busts'] / total_hands if total_hands > 0 else 0
        dealer_bust_rate = results['dealer_busts'] / total_hands if total_hands > 0 else 0
        house_edge = results['house_edge']
        
        # Return summary data
        summary_data = {
            "timestamp": timestamp,
            "config": sim_config.to_dict(),
            "results": results,
            "simulation_time": simulation_time,
            "house_edge": house_edge,
            "player_win_rate": player_win_rate,
            "dealer_win_rate": dealer_win_rate,
            "push_rate": push_rate,
            "player_bust_rate": player_bust_rate,
            "dealer_bust_rate": dealer_bust_rate
        }
        
        # If generating visuals, create DataFrames for plotting
        if config["generate_visuals"]:
            detailed_results_df = report_generator.get_detailed_dataframe()
            summary_data["detailed_df"] = detailed_results_df
        
        return summary_data

    # Handle simulation when form is submitted
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
                "num_players": num_players,
                "save_results": save_results,
                "generate_visuals": generate_visuals,
                "custom_hit_rules": custom_hit_rules
            }
            
            simulation_results = run_simulation_advanced(config)
            st.session_state.latest_results = simulation_results
            
        st.success(f"Simulation completed! {num_hands} hands simulated in {simulation_results['simulation_time']:.2f} seconds.")

        # Display immediate results after simulation
        results = simulation_results
        
        st.markdown('<div class="section-header">Simulation Results</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("House Edge", f"{results['house_edge']*100:.2f}%")
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
            
        if save_results:
            st.info(f"""
            Results have been saved to the following files:
            - Configuration: `config/simulation_config_{results['timestamp']}.json`
            - Detailed CSV: `results/blackjack_sim_detailed_{results['timestamp']}.csv`
            - Matrix CSV: `results/blackjack_sim_matrix_{results['timestamp']}.csv`
            - Summary: `results/blackjack_sim_summary_{results['timestamp']}.txt`
            """)

# Data Visualization tab - Enhanced with more advanced visualization options
with tab2:
    st.markdown('<div class="section-header">Data Visualization</div>', unsafe_allow_html=True)
    
    if "latest_results" in st.session_state and st.session_state.latest_results.get("detailed_df") is not None:
        detailed_df = st.session_state.latest_results["detailed_df"]
        
        # Advanced visualization options
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
            
            # Show outcome percentages
            st.dataframe(
                outcomes.assign(Percentage=lambda x: (x["Count"] / x["Count"].sum() * 100).round(2)).assign(
                    Percentage=lambda x: x["Percentage"].astype(str) + '%'
                )
            )
            
        elif viz_type == "Total Value Distribution":
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
            
        elif viz_type == "Win/Loss by Player Total":
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
            
        elif viz_type == "Dealer Bust Analysis":
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Filter for dealer busts
            dealer_busts = detailed_df[detailed_df["dealer_total"] > 21]
            
            if len(dealer_busts) > 0:
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
                st.info("No dealer busts found in this simulation.")
        
        elif viz_type == "Outcome Matrix Heatmap":
            # Create matrix for heatmap
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
            
            # Show frequency matrix
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

# Previous Results tab - Enhanced with more options
with tab3:
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
            timestamp = selected_result['timestamp']
            
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
                            columns="outcome", 
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