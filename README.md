# Blackjack Simulator

A Python-based blackjack simulator designed to determine house edge through extensive simulations of custom blackjack variants.

## Overview

This blackjack simulator allows for precise calculation of house edge by simulating millions of hands with customizable rules. It's designed to:

- Accurately simulate blackjack play as it would occur in real-life
- Support custom rule variants (including a dealer-betting variant)
- Generate comprehensive reports of outcomes and statistics
- Calculate house edge with high precision

## Key Features

- **Accurate Simulation**: Simulates blackjack play exactly as it would occur in a casino
- **Custom Rules**: Supports a variant where players bet on the dealer's hand with 5% commission
- **Configurable Parameters**: Adjustable deck count, shuffling method, hitting rules, and more
- **Comprehensive Reports**: Generates detailed CSV reports for outcome analysis
- **Statistical Analysis**: Tracks outcome frequencies and calculates house edge

## Requirements

- Python 3.6+
- No external dependencies required

## Installation

Clone the repository:

```bash
git clone (github url/blackjack-sim)
cd blackjack-sim
```

## Usage

Run a simulation with default parameters:

```bash
python src/main.py
```

### Command Line Options

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

## Output Reports

After each simulation, the following reports are generated in the `results` directory:

1. **Summary Report**: Text file with overall statistics and house edge
2. **Outcome Matrix**: CSV file showing hand total frequencies
3. **Detailed Report**: CSV file with detailed win/loss outcomes for each hand combination

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
│   │   └── simulator.py # Core simulator
│   ├── reporting/       # Reporting tools
│   │   └── report_generator.py
│   └── main.py          # Main entry point
```

## Customizable Variant Rules

The simulator is set up for a custom variant where:

1. The player bets on the dealer's hand winning against their own hand
2. The player hits using the same rules as the dealer by default
3. If player and dealer both bust, the hand pushes
4. If player and dealer both get blackjack, the hand pushes
5. A 5% commission is taken from player wins (configurable)

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
