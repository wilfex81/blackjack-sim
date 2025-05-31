# Blackjack Simulator

A Python-based blackjack simulator designed to determine house edge through extensive simulations of custom blackjack variants.

## Overview

This blackjack simulator allows for precise calculation of house edge by simulating millions of hands with customizable rules. It's designed to:

- Accurately simulate blackjack play as it would occur in real-life
- Support custom rule variants (including a dealer-betting variant)
- Simulate push sidebets that pay when player and dealer tie
- Generate comprehensive reports of outcomes and statistics
- Calculate both raw and true house edge with high precision
- Account for commission effects on overall profitability

## Edge Calculation Methodology

The simulator calculates two distinct types of edge:

1. **Raw Edge**: The pure mathematical advantage in the game, calculated as (player win rate - dealer win rate). With both sides having nearly equal win rates (approximately 41%), this typically shows a very small value around ±0.04%, reflecting the near-even nature of the base game. A positive raw edge means the player has a mathematical advantage before commission.

2. **True House Edge**: The actual house advantage after accounting for commission and all payouts, calculated as:
   dealer_win_rate - (player_win_rate × (1 - commission_pct))

   Components affecting the edge:
   - Dealer wins (approximately 41%) - collected in full
   - Player wins (approximately 41%) - paid with commission deducted
   - Push rate (approximately 17-18%) - no effect on edge
   - Commission percentage on wins (default 5%)
   - Special hand payouts (e.g., blackjack bonuses if applicable)

For example, with a 5% commission on player wins, while the raw edge may be near zero (±0.04%), the true house edge is approximately 2.02%. This occurs because while both sides win about equally often, the house collects 100% of dealer wins but only pays 95% on player wins. For a typical win rate of 41%, this 5% commission creates a house advantage of about 2% (41% × 5% = 2.05%). A positive true house edge indicates an advantage for the house.

## Key Features

- **Accurate Simulation**: Simulates blackjack play exactly as it would occur in a casino
- **Custom Rules**: Supports a variant where players bet on the dealer's hand with configurable commission
- **Sidebet Simulation**: Special sidebet that pays when player and dealer push (tie)
- **Edge Calculations**: 
  - Raw Edge: Pure mathematical win/loss rate difference before commission
  - True House Edge: Actual edge after commission and payouts are applied
- **Configurable Parameters**: 
  - Number of decks (1-8)
  - Shuffling method (traditional or continuous)
  - Hitting rules for both player and dealer
  - Commission percentage
  - Blackjack payout ratios
  - Sidebet payout options for different push types
  - And more...
- **Interactive Mode**: Step-by-step hand simulation with real-time statistics
- **Comprehensive Reports**: Generates detailed CSV reports for outcome analysis
- **Statistical Analysis**: Tracks win rates, bust rates, blackjack rates, and edge calculations
- **Visualizations**: Multiple chart types for analyzing game outcomes

## Requirements

- Python 3.6+
- No external dependencies required

## Installation

After receiving the zip file:

```bash
# Extract the zip file
unzip blackjack-sim.zip

# Navigate to the project directory
cd blackjack-sim

# Create and activate a virtual environment (recommended)
python -m venv venv

# On Linux/Mac
source venv/bin/activate

# On Windows
# venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

## Usage

Run the interactive Streamlit web interface (recommended):

```bash
streamlit run streamlit_app.py
```

Alternatively, run a simulation directly from the command line:

```bash
# Run main simulation
python src/main.py

# Run sidebet simulation
python run_sidebet_cli.py
```

### Command Line Options (Main Simulation)

The simulator supports various command-line arguments:

```
--num-hands INT           Number of hands to simulate (default: 10000)
--num-decks INT           Number of decks in the shoe (default: 6)
--player-hit-soft-17      Player hits on soft 17
--dealer-hit-soft-17      Dealer hits on soft 17
--continuous-shuffle      Use continuous shuffle instead of traditional shoe
--reshuffle-cutoff INT    Minimum cards before reshuffling (default: 52)
--commission FLOAT        Commission percentage taken from wins (default: 5.0)
--blackjack-payout FLOAT  Payout ratio for blackjack (default: 1.0)
--num-players INT         Number of players at the table (default: 1)
--hit-rules STRING        Custom hit rules
```

### Custom Hit Rules Format

Custom hit rules can be specified using a string format:

```
hard:16,10:hit;soft:17:hit
```

This example means:
- Hit on hard 16 when dealer shows 10
- Hit on soft 17 regardless of dealer's card

### Examples

Run 1 million hands with standard rules:

```bash
python src/main.py --num-hands 1000000
```

Run with continuous shuffle:

```bash
python src/main.py --continuous-shuffle
```

Run with custom hit rules:

```bash
python src/main.py --hit-rules "hard:16,10|9|8:hit;soft:17:hit"
```

### Sidebet Command Line Options

The sidebet simulator provides a separate command-line interface with additional options:

```bash
python run_sidebet_cli.py [options]
```

Key options include:

```
--num-hands INT           Number of hands to simulate (default: 10000)
--num-decks INT           Number of decks in the shoe (default: 6)
--player-hits-soft-17     Player hits on soft 17
--dealer-hits-soft-17     Dealer hits on soft 17
--hit-against-blackjack   Allow hitting against dealer blackjack
--continuous-shuffle      Use continuous shuffle instead of traditional shoe
--reshuffle-threshold INT Minimum cards before reshuffling (default: 52)

# Sidebet specific options
--payout-mode {total,cards}  Pay based on hand total or card count (default: total)

# Hand total payout options (when using --payout-mode total)
--payout-17 FLOAT         Payout for 17 vs 17 push (default: 1.0)
--payout-18 FLOAT         Payout for 18 vs 18 push (default: 1.0)
--payout-19 FLOAT         Payout for 19 vs 19 push (default: 1.0)
--payout-20 FLOAT         Payout for 20 vs 20 push (default: 1.0)
--payout-21 FLOAT         Payout for 21 vs 21 push (default: 1.0)
--payout-bust-bust FLOAT  Payout for bust vs bust push (default: 1.0)
--payout-bj-bj FLOAT      Payout for blackjack vs blackjack push (default: 1.0)

# Card count payout options (when using --payout-mode cards)
--payout-4-cards FLOAT    Payout for push with 4 total cards (default: 1.0)
--payout-5-cards FLOAT    Payout for push with 5 total cards (default: 1.0)
--payout-6-cards FLOAT    Payout for push with 6 total cards (default: 1.0)
... and so on up to --payout-12plus-cards

# Output options
--output-dir DIR          Directory to save results (default: results)
--config-dir DIR          Directory to save configuration (default: config)
--no-save                 Do not save results to files
--config-file FILE        Load configuration from file
```

### Sidebet Simulation Examples

Run a basic sidebet simulation:

```bash
python run_sidebet_cli.py
```

Run with card count payout mode:

```bash
python run_sidebet_cli.py --payout-mode cards
```

Run with custom payouts:

```bash
python run_sidebet_cli.py --payout-bj-bj 5 --payout-21 3 --payout-20 2
```

Load a configuration from file:

```bash
python run_sidebet_cli.py --config-file config/sidebet_config_20250531_110003.json
```

## Output Reports

After each simulation, the following reports are generated in the `results` directory:

1. **Summary Report**: Text file with overall statistics and house edge
2. **Outcome Matrix**: CSV file showing hand total frequencies
3. **Detailed Report**: CSV file with detailed win/loss outcomes for each hand combination

### Sidebet Reports

The sidebet simulation generates additional reports:

1. **Sidebet Summary**: Text file with push statistics, blackjack rates, and house edge
2. **Detailed Push Matrix**: CSV file correlating hand totals and card counts for all pushes

## Project Structure

```
blackjack-sim/
├── config/              # Configuration files
├── results/             # Simulation result files
├── src/                 # Source code
│   ├── game/            # Game mechanics
│   │   ├── card.py      # Card representation
│   │   ├── deck.py      # Deck and shoe management
│   │   └── hand.py      # Hand evaluation
│   ├── strategy/        # Player and dealer strategies
│   │   ├── base_strategy.py
│   │   ├── dealer_strategy.py
│   │   └── player_strategy.py
│   ├── simulation/      # Simulation engine
│   │   ├── config.py    # Simulation configuration
│   │   ├── simulator.py # Core simulator
│   │   └── sidebet_simulator.py # Sidebet simulator
│   ├── reporting/       # Reporting tools
│   │   └── report_generator.py
│   └── main.py          # Main entry point
├── run_sidebet_cli.py   # Command-line interface for sidebet simulation
└── streamlit_app.py     # Streamlit web interface
```

## Customizable Variant Rules

The simulator is set up for a custom variant where:

1. The player bets on the dealer's hand winning against their own hand
2. The player hits using the same rules as the dealer by default
3. If player and dealer both bust, the hand pushes
4. If player and dealer both get blackjack, the hand pushes
5. A 5% commission is taken from player wins (configurable)
6. Optional sidebet pays when player and dealer push

Additional features:

1. Option to allow player to hit when dealer has blackjack
2. Ability to set up exact hands for player and dealer in hand-by-hand mode
3. Tracking of blackjack statistics (player blackjacks, dealer blackjacks, blackjack pushes)

## Understanding Custom Hit Rules

Custom hit rules allow you to define exactly when the player should hit or stand based on their hand value and the dealer's upcard. Here's how they work:

### Format Explanation

The hit rules use this format: `hand_type:player_total:dealer_cards,action`

- **hand_type**: Either `hard` or `soft` (soft hands contain an Ace counted as 11)
- **player_total**: The total value of the player's hand (e.g., 12, 13, 14, etc.)
- **dealer_cards**: The dealer's upcard values, separated by `|` (e.g., `2|3|4|5|6`)
- **action**: Either `hit` or `stand` indicating what the player should do

Multiple rules are combined with semicolons (`;`).

### Example Strategy

For example, to make the player stand on 12 or higher when the dealer shows 2-6, and hit otherwise:

```
hard:12:2|3|4|5|6,stand;hard:12:7|8|9|10|11,hit;hard:13:2|3|4|5|6,stand;hard:13:7|8|9|10|11,hit;hard:14:2|3|4|5|6,stand;hard:14:7|8|9|10|11,hit;hard:15:2|3|4|5|6,stand;hard:15:7|8|9|10|11,hit;hard:16:2|3|4|5|6,stand;hard:16:7|8|9|10|11,hit
```

This tells the simulator:
- Stand on hard 12 when dealer shows 2-6, hit when dealer shows 7-A
- Stand on hard 13 when dealer shows 2-6, hit when dealer shows 7-A
- And so on...

### Default Behavior

If you don't specify a rule for a particular scenario, the simulator follows the default behavior:
- Hit on 16 or less
- Stand on 17 or more
- Possibly hit on soft 17 depending on the "Player Hits Soft 17" setting

Remember: In this variant, since you're betting on the dealer's hand winning, an optimal player strategy might be different from traditional blackjack.

## Sidebet Feature

The simulator includes a special sidebet that pays when the player and dealer push (tie). This is implemented as a separate simulation mode with its own configuration options.

### Sidebet Characteristics

- Pays when player and dealer push (tie)
- Two payout modes:
  - **Hand Total**: Different payouts based on the hand value (17v17, 18v18, etc.)
  - **Card Count**: Different payouts based on total number of cards used (4, 5, 6, etc.)
- Tracks statistics such as:
  - Push rate by hand value
  - Push rate by card count
  - Blackjack vs blackjack pushes
  - Player and dealer blackjack rates
  - Detailed correlation between hand totals and card counts

### Sidebet Interface

The sidebet can be accessed in two ways:

1. **Streamlit Web Interface**: Via the "Sidebet Simulation" tab in the web app
2. **Command Line**: Using the `run_sidebet_cli.py` script

### Sidebet Simulation Options

The sidebet simulation offers these configurable parameters:

- Game rules (decks, shuffling, hitting rules)
- Payout mode (hand total or card count)
- Custom payouts for each type of push
- Interactive hand-by-hand simulation
- Ability to set up specific starting hands

