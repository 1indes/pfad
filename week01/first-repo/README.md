# Schotter — Generative Art

This project recreates Georg Nees’ *Schotter* (1968) using Python.  
It generates a grid of squares that gradually fall apart as they descend.

## How to Run
1. Make sure you have Python 3 installed.
2. Run the script:
python3 sketch.py
3. The program will output a new `sketch.svg` file with the artwork.

## Parameters
- **SEED**: Controls randomness. Change this number to get a different variation.
- **CHAOS**: Controls how much the squares rotate/displace. Higher values = more disorder.
- **COLS**: Number of columns in the grid.
- **ROWS**: Number of rows in the grid.
