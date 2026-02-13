# PinkyPawn

> A hobby project for fun. Do not expect a serious or competitive chess engine.

A simple chess engine designed to play on Lichess as a personal programming exercise and pastime.

## ⚠️ Important Disclaimer

This is a **personal hobby project** created purely for entertainment and learning purposes. There is **no intention** to reinvent the wheel or build a "real" competitive chess engine. If you're looking for a serious chess engine, please check out [Stockfish](https://stockfishchess.org/), [Leela Chess Zero](https://lczero.org/), or other established engines.

## Overview

PinkyPawn implements simple heuristic-based move evaluation using intuitive chess concepts.


## Project Structure

```
bot/
├── config.py              # Configuration settings
├── main.py                # Bot entry point
├── engines/
│   ├── base_engine.py     # Abstract engine interface
│   ├── pinkypawn_engine.py # Heuristic-based engine
│   ├── random_engine.py   # Random move selection
│   └── stockfish_engine.py # Stockfish integration
```