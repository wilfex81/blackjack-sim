#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import json
import time
from datetime import datetime

# Add the project root to the path so we can use absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.config import SimulationConfig
from src.simulation.simulator import BlackjackSimulator
from src.reporting.report_generator import ReportGenerator

# Set page configuration
st.set_page_config(
    page_title="Blackjack Simulator",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_configs():
    """Load all saved configurations from the config directory"""
    configs = []
    try:
        config_dir = os.path.join(os.path.dirname(__file__), "config")
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
        results_dir = os.path.join(os.path.dirname(__file__), "results")
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
                        'config_file': config_file if os.path.exists(os.path.join(results_dir, config_file)) else None,
                    }
                    results.append(result_entry)
    except Exception as e:
        st.error(f"Error loading simulation results: {e}")
    
    # Sort results by timestamp (newest first)
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    return results

def run_new_simulation():
    """Run a new simulation based on user configuration"""
    st.header("Configure New Simulation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_hands = st.number_input("Number of hands to simulate", 
                                   min_value=100, 
                                   max_value=1000000, 
                                   value=10000,
                                   step=1000)
        
        num_decks = st.number_input("Number of decks", 
                                   min_value=1, 
                                   max_value=8, 
                                   value=6)
        
        player_hit_soft_17 = st.checkbox("Player hits on soft 17", value=False)
        dealer_hit_soft_17 = st.checkbox("Dealer hits on soft 17", value=False)
        
        shuffle_method = st.radio("Shuffle method", 
                                ["Standard", "Continuous"], 
                                horizontal=True)
        
        if shuffle_method == "Standard":
            reshuffle_cutoff = st.number_input("Minimum cards before reshuffling", 
                                             min_value=0, 
                                             max_value=104, 
                                             value=52)
        else:
            reshuffle_cutoff = 0
    
    with col2:
        commission = st.slider("Commission percentage", 
                             min_value=0.0, 
                             max_value=10.0, 
                             value=5.0, 
                             step=0.1)
        
        blackjack_payout = st.slider("Blackjack payout ratio", 
                                   min_value=1.0, 
                                   max_value=3.0, 
                                   value=1.0, 
                                   step=0.5)
        
        num_players = st.number_input("Number of players", 
                                    min_value=1, 
                                    max_value=7, 
                                    value=1)
        
        advanced_options = st.expander("Advanced Options")
        with advanced_options:
            hit_rules = st.text_area("Custom Hit Rules", 
                                   value="",
                                   help="Format: 'hard:16,10:hit;soft:17:hit' means hit on hard 16 when dealer shows 10, and hit on soft 17")
    
    # Create simulation button
    run_button = st.button("Run Simulation", type="primary")
    
    if run_button:
        with st.spinner("Running simulation..."):
            try:
                # Parse hit rules
                hit_rules_dict = {}
                if hit_rules:
                    for rule in hit_rules.split(';'):
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
                
                # Create configuration
                config = SimulationConfig(
                    num_hands=num_hands,
                    num_decks=num_decks,
                    player_hit_soft_17=player_hit_soft_17,
                    dealer_hit_soft_17=dealer_hit_soft_17,
                    reshuffle_cutoff=reshuffle_cutoff,
                    commission_pct=commission,
                    blackjack_payout=blackjack_payout,
                    num_players=num_players,
                    player_hit_rules=hit_rules_dict
                )
                
                # Run simulation
                start_time = time.time()
                simulator = BlackjackSimulator(config)
                results = simulator.run_simulation()
                elapsed_time = time.time() - start_time
                
                # Generate reports
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                summary_file = f"blackjack_sim_summary_{timestamp}.txt"
                matrix_file = f"blackjack_sim_matrix_{timestamp}.csv"
                detailed_file = f"blackjack_sim_detailed_{timestamp}.csv"
                config_file = f"simulation_config_{timestamp}.json"
                
                report_gen = ReportGenerator(simulator)
                report_gen.generate_summary_report(summary_file)
                report_gen.generate_outcome_matrix_csv(matrix_file)
                report_gen.generate_detailed_report(detailed_file)
                report_gen.save_config(config_file)
                
                st.success(f"Simulation completed in {elapsed_time:.2f} seconds!")
                st.session_state["last_simulation"] = {
                    "timestamp": timestamp,
                    "results": results,
                    "config": config,
                    "summary_file": summary_file
                }
                
                # Show results summary
                st.subheader("Results Summary")
                total_hands = results['total_bets']
                player_win_pct = 100 * results['player_wins'] / total_hands if total_hands > 0 else 0
                dealer_win_pct = 100 * results['dealer_wins'] / total_hands if total_hands > 0 else 0
                push_pct = 100 * results['pushes'] / total_hands if total_hands > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("House Edge", f"{results['house_edge']:.2f}%")
                col2.metric("Simulation Time", f"{results['simulation_time']:.2f}s")
                col3.metric("Total Hands", f"{total_hands}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Player Wins", f"{results['player_wins']} ({player_win_pct:.2f}%)")
                col2.metric("Dealer Wins", f"{results['dealer_wins']} ({dealer_win_pct:.2f}%)")
                col3.metric("Pushes", f"{results['pushes']} ({push_pct:.2f}%)")
                
                col1, col2 = st.columns(2)
                col1.metric("Player Busts", f"{results['player_busts']} ({100 * results['player_busts'] / total_hands:.2f}%)")
                col2.metric("Dealer Busts", f"{results['dealer_busts']} ({100 * results['dealer_busts'] / total_hands:.2f}%)")
                
                # Visualization 
                st.subheader("Outcome Visualization")
                
                # Load detailed results for visualization
                results_dir = os.path.join(os.path.dirname(__file__), "results")
                detailed_path = os.path.join(results_dir, detailed_file)
                matrix_path = os.path.join(results_dir, matrix_file)
                
                if os.path.exists(detailed_path):
                    df_detailed = pd.read_csv(detailed_path)
                    
                    # Plot outcome distribution
                    st.write("##### Outcome Distribution")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    outcome_counts = df_detailed['result'].value_counts()
                    outcome_counts.plot(kind='bar', ax=ax)
                    ax.set_ylabel('Number of Hands')
                    ax.set_title('Hand Outcome Distribution')
                    st.pyplot(fig)
                
                if os.path.exists(matrix_path):
                    df_matrix = pd.read_csv(matrix_path)
                    df_matrix = df_matrix.pivot("player_total", "dealer_total", "count")
                    
                    # Plot heatmap of player vs dealer total
                    st.write("##### Hand Total Distribution")
                    fig, ax = plt.subplots(figsize=(12, 8))
                    sns.heatmap(df_matrix, annot=False, cmap="YlGnBu", ax=ax)
                    ax.set_title('Player Total vs Dealer Total Frequency')
                    st.pyplot(fig)
            
            except Exception as e:
                st.error(f"Error running simulation: {str(e)}")

def view_existing_results():
    """View and analyze existing simulation results"""
    st.header("View Existing Simulation Results")
    
    # Load existing results
    results = load_simulation_results()
    
    if not results:
        st.info("No simulation results found. Run a new simulation to generate results.")
        return
    
    # Display dropdown to select result
    result_options = {f"{r['timestamp']}": i for i, r in enumerate(results)}
    selected_result_key = st.selectbox("Select simulation result:", 
                                     options=list(result_options.keys()),
                                     format_func=lambda x: f"Simulation {x}")
    
    selected_result = results[result_options[selected_result_key]]
    
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    
    # Display summary
    if selected_result['summary_file']:
        st.subheader("Summary")
        summary_path = os.path.join(results_dir, selected_result['summary_file'])
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary_content = f.read()
            st.text(summary_content)
    
    # Display configuration
    if selected_result['config_file']:
        config_path = os.path.join(results_dir, selected_result['config_file'])
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            st.subheader("Configuration")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Hands:** {config.get('num_hands', 'N/A')}")
                st.write(f"**Decks:** {config.get('num_decks', 'N/A')}")
                st.write(f"**Player hits soft 17:** {config.get('player_hit_soft_17', 'N/A')}")
                st.write(f"**Dealer hits soft 17:** {config.get('dealer_hit_soft_17', 'N/A')}")
                
            with col2:
                shuffle_type = "Continuous shuffle" if config.get('reshuffle_cutoff', 0) == 0 else f"Reshuffle at {config.get('reshuffle_cutoff', 'N/A')} cards"
                st.write(f"**Shuffle method:** {shuffle_type}")
                st.write(f"**Commission:** {config.get('commission_pct', 'N/A')}%")
                st.write(f"**Blackjack payout:** {config.get('blackjack_payout', 'N/A')}:1")
                st.write(f"**Players:** {config.get('num_players', 'N/A')}")
    
    # Visualizations
    st.subheader("Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Outcome Matrix", "Detailed Results", "Analysis"])
    
    with tab1:
        if selected_result['matrix_file']:
            matrix_path = os.path.join(results_dir, selected_result['matrix_file'])
            if os.path.exists(matrix_path):
                df_matrix = pd.read_csv(matrix_path)
                if not df_matrix.empty:
                    # Create pivot table for the heatmap
                    pivot_matrix = df_matrix.pivot("player_total", "dealer_total", "count")
                    
                    st.write("##### Player vs. Dealer Hand Totals")
                    fig, ax = plt.subplots(figsize=(12, 8))
                    sns.heatmap(pivot_matrix, annot=False, cmap="YlGnBu", ax=ax)
                    ax.set_title('Frequency of Hand Total Combinations')
                    st.pyplot(fig)
                    
                    # Show raw data in an expandable section
                    with st.expander("View Raw Matrix Data"):
                        st.dataframe(df_matrix)
    
    with tab2:
        if selected_result['detailed_file']:
            detailed_path = os.path.join(results_dir, selected_result['detailed_file'])
            if os.path.exists(detailed_path):
                df_detailed = pd.read_csv(detailed_path)
                if not df_detailed.empty:
                    # Create charts
                    st.write("##### Outcome Distribution")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    outcome_counts = df_detailed['result'].value_counts()
                    outcome_counts.plot(kind='bar', ax=ax)
                    ax.set_ylabel('Number of Hands')
                    ax.set_title('Hand Outcome Distribution')
                    st.pyplot(fig)
                    
                    st.write("##### Player Hand Distribution")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    player_totals = df_detailed['player_total'].value_counts().sort_index()
                    player_totals.plot(kind='bar', ax=ax)
                    ax.set_xlabel('Player Hand Total')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Player Hand Total Distribution')
                    st.pyplot(fig)
                    
                    # Filter controls
                    st.write("##### Filter Detailed Results")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        result_filter = st.multiselect(
                            "Filter by outcome:", 
                            options=sorted(df_detailed['result'].unique()),
                            default=[]
                        )
                    
                    with col2:
                        player_min = int(df_detailed['player_total'].min())
                        player_max = int(df_detailed['player_total'].max())
                        player_range = st.slider(
                            "Player total range:", 
                            min_value=player_min,
                            max_value=player_max,
                            value=(player_min, player_max)
                        )
                    
                    with col3:
                        dealer_min = int(df_detailed['dealer_total'].min())
                        dealer_max = int(df_detailed['dealer_total'].max())
                        dealer_range = st.slider(
                            "Dealer total range:", 
                            min_value=dealer_min,
                            max_value=dealer_max,
                            value=(dealer_min, dealer_max)
                        )
                    
                    # Apply filters
                    filtered_df = df_detailed.copy()
                    
                    if result_filter:
                        filtered_df = filtered_df[filtered_df['result'].isin(result_filter)]
                    
                    filtered_df = filtered_df[
                        (filtered_df['player_total'] >= player_range[0]) & 
                        (filtered_df['player_total'] <= player_range[1]) &
                        (filtered_df['dealer_total'] >= dealer_range[0]) & 
                        (filtered_df['dealer_total'] <= dealer_range[1])
                    ]
                    
                    # Show filtered data
                    st.write(f"Showing {len(filtered_df)} hands matching filters")
                    st.dataframe(filtered_df)
    
    with tab3:
        st.write("##### Key Statistics")
        
        # Try to calculate key stats from the detailed file
        if selected_result['detailed_file']:
            detailed_path = os.path.join(results_dir, selected_result['detailed_file'])
            if os.path.exists(detailed_path):
                try:
                    df_detailed = pd.read_csv(detailed_path)
                    if not df_detailed.empty:
                        total_hands = len(df_detailed)
                        player_wins = len(df_detailed[df_detailed['result'] == 'player_win'])
                        dealer_wins = len(df_detailed[df_detailed['result'] == 'dealer_win'])
                        pushes = len(df_detailed[df_detailed['result'] == 'push'])
                        player_busts = len(df_detailed[df_detailed['player_total'] > 21])
                        dealer_busts = len(df_detailed[df_detailed['dealer_total'] > 21])
                        
                        # Custom variant house edge calculation
                        # Wins contribute (1-commission) to player
                        # Losses contribute -1 to player
                        # Calculate from config file to get commission rate
                        commission = 5.0  # Default
                        if selected_result['config_file']:
                            config_path = os.path.join(results_dir, selected_result['config_file'])
                            if os.path.exists(config_path):
                                with open(config_path, 'r') as f:
                                    config = json.load(f)
                                    commission = config.get('commission_pct', 5.0)
                        
                        win_multiplier = 1.0 - (commission / 100.0)
                        net_win = (player_wins * win_multiplier) - dealer_wins
                        house_edge = -net_win / total_hands * 100
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("House Edge", f"{house_edge:.2f}%")
                        col2.metric("Total Hands", f"{total_hands}")
                        col3.metric("Dealer Bust Rate", f"{dealer_busts/total_hands*100:.2f}%")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Player Win Rate", f"{player_wins/total_hands*100:.2f}%")  
                        col2.metric("Dealer Win Rate", f"{dealer_wins/total_hands*100:.2f}%")
                        col3.metric("Push Rate", f"{pushes/total_hands*100:.2f}%")
                        
                        # Add custom analysis based on the simulation report
                        st.write("##### Analysis")
                        st.write("""
                        This analysis is based on the simulation data for the custom blackjack variant where
                        players bet on the dealer's hand winning against a standard strategy player hand.
                        
                        The house edge shown above represents the casino's expected profit per unit wagered.
                        A positive house edge means the casino has an advantage in the long run.
                        """)
                        
                        # Compare with standard blackjack
                        st.write("##### Comparison to Standard Blackjack")
                        st.write("""
                        In standard blackjack with common rules, the house edge is typically between 0.5% and 1%, 
                        assuming optimal basic strategy play. This custom variant with the commission-based model 
                        shows a different edge profile, which can be adjusted by changing the commission rate.
                        
                        The dealer hitting on soft 17 in this custom variant actually decreases the house edge, 
                        which is the opposite of standard blackjack where it increases the house edge.
                        """)
                except Exception as e:
                    st.error(f"Error analyzing results: {e}")

def main():
    """Main function for the Streamlit app"""
    st.title("🃏 Blackjack Simulator")
    
    # About section in the sidebar
    with st.sidebar:
        st.write("## About")
        st.write("""
        This application simulates a custom blackjack variant to analyze house edge and winning probabilities
        under different rule configurations.
        
        You can run new simulations with custom parameters or analyze previous simulation results.
        """)
        
        st.write("## Features")
        st.write("""
        - Run simulations with customizable parameters
        - View detailed outcome statistics
        - Visualize player vs dealer hand distributions
        - Compare different rule variations
        """)
        
        st.write("---")
        st.write("Developed with Streamlit")
    
    # Main navigation
    tab1, tab2 = st.tabs(["Run Simulation", "View Results"])
    
    with tab1:
        run_new_simulation()
    
    with tab2:
        view_existing_results()

if __name__ == "__main__":
    main()