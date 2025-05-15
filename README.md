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
git clone https://github.com/yourusername/blackjack-sim.git
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
└── tests/               # Unit tests
```

## Customizable Variant Rules

The simulator is set up for a custom variant where:

1. The player bets on the dealer's hand winning against their own hand
2. The player hits using the same rules as the dealer by default
3. If player and dealer both bust, the hand pushes
4. If player and dealer both get blackjack, the hand pushes
5. A 5% commission is taken from player wins (configurable)

## License

Free for personal and academic use.