# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a frequency segment optimization tool for drone avoidance systems (IMD - Intermodulation Distortion Avoider). The project finds optimal frequency combinations within specified ranges while avoiding interference patterns.

## Key Architecture

### Core Components

1. **imd.py** - Enhanced IMD rating calculation module
   - Calculates intermodulation distortion ratings with multiple IMD orders:
     - 2nd order IMD: 2*f1 - f2 (1 pattern)
     - 3rd order IMD (2-freq): 2*f2 - f1, f1 + 2*f2, 2*f1 + f2 (3 patterns)
     - 3rd order IMD (3-freq): All 10 patterns including f1 + f2 - f3, f1 - f2 + f3, -f1 + f2 + f3, etc.
   - Weighted scoring system based on relative signal strengths:
     - 2nd order: weight = 1.0 (reference)
     - 3rd order (2-freq): weight = 0.1 (-20dB)
     - 3rd order (3-freq): weight = 0.03 (-30dB)
   - Different thresholds: 35 MHz for 2nd order, 25 MHz for 3rd order
   - Valid frequency range: 5100-6099 MHz
   - Rating system: 0-100 (higher is better)
   - Includes legacy rating function for comparison

2. **app.py** - Main application
   - Finds non-overlapping frequency segments within defined ranges
   - Configurable bandwidth modes: analog (17 MHz), hdzero-narrow (17 MHz), hdzero (27 MHz), dji (20 MHz)
   - Current range: 5670-5830 MHz (configurable)
   - Segment width based on selected mode with 1 MHz minimum gap
   - Visualizes top-rated combinations using matplotlib
   - Shows detailed IMD analysis for best combination
   - Comparison between enhanced and legacy ratings
   - Optional IMD product visualization with color coding

### Algorithm Flow
1. Generate all possible center frequencies from FPV bands within range
2. Find all valid non-overlapping combinations of 4 segments
3. Calculate enhanced IMD ratings for each combination (2nd and 3rd order)
4. Sort by rating and display top 10 results
5. Provide detailed IMD analysis showing:
   - Significant IMD products by type
   - Worst interference cases with formulas
   - Visual representation with IMD markers

### Key Features
- **Enhanced IMD Analysis**: Considers both 2nd and 3rd order IMD products
- **Weighted Scoring**: Realistic weighting based on signal strength characteristics
- **Detailed Reporting**: Shows IMD formulas, frequencies, and interference scores
- **Dual Visualization**: Standard view and IMD-annotated view
- **Legacy Comparison**: Shows both enhanced and original ratings

### Visualization Features

1. **Standard Results View** (`drawResults(ratings[:10])`)
   - Shows top 10 frequency combinations
   - Channel bandwidth visualization
   - Band color coding (R=red, F=blue, A=green, B=orange, E=purple)
   - Rating display for each combination

2. **IMD-Enhanced View** (`drawResults(ratings[:1], show_imd=True)`)
   - Shows IMD products for best combination
   - Color-coded IMD markers:
     - Red: 2nd order IMD
     - Orange: 3rd order IMD (2-freq)
     - Yellow: 3rd order IMD (3-freq)
   - Legend explaining IMD types

3. **Detailed IMD Analysis Output**
   - analyze_imd_details() provides comprehensive breakdown
   - Shows formulas, frequencies, and scores
   - Identifies worst interference cases
   - Counts significant IMD products by type

## Development Commands

### Setup with uv
```bash
# Install dependencies
uv sync

# Run the application
uv run python app.py
```

### Alternative: Manual Setup
If not using uv, install matplotlib directly:
```bash
pip install matplotlib
python3 app.py
```

## Project-Specific Notes

- Frequency values are in MHz
- Segments are defined by their center frequency
- The rating algorithm penalizes combinations where intermodulation products fall near existing frequencies
- Lower total interference score results in higher rating (100 - normalized_score)

## Technical Implementation Details

### IMD Calculation Functions

1. **calculate_2nd_order_imd(f1, f2)**
   - Returns: [2*f1 - f2]
   - Traditional IMD calculation

2. **calculate_3rd_order_imd_2freq(f1, f2)**
   - Returns IMD products that fall within valid frequency range
   - Products: 2*f2 - f1, f1 + 2*f2, 2*f1 + f2
   - Only returns products within 5100-6099 MHz

3. **calculate_3rd_order_imd_3freq(f1, f2, f3)**
   - Returns 3-frequency interaction products
   - Implements all 10 IMDAvoider3 patterns:
     - Pattern 1-3: f1±f2±f3 combinations
     - Pattern 4-10: 2*f1±f2±f3 and f1±2*f2±f3 combinations
   - Critical for multi-transmitter scenarios
   - Mathematically 16 patterns exist, but 6 generate negative/out-of-band frequencies

4. **calculate_weighted_interference(imd_freq, frequencies, weight, threshold)**
   - Calculates interference score for a single IMD product
   - Uses quadratic penalty: (threshold - difference)²
   - Applies weight based on IMD type

### Algorithm Optimization

- **Normalization Factor**: Increased from 5*n to 15*n to account for additional IMD types
- **Early Termination**: IMD products outside valid range are skipped
- **Threshold Differentiation**: Stricter threshold for 3rd order reflects near-channel placement

### Research Background

Detailed academic research supporting the implementation is documented in:
- [English Version](docs/IMD_Research_Document.md)
- [Japanese Version](docs/IMD_Research_Document_JP.md)
- [3rd Order IMD Theory](docs/3rd_order_imd_theory.md)
- [IMDAvoider3 Comparison](docs/IMDAvoider3_Comparison.md)

Key findings:
- 3rd order products typically -20 to -30 dB below fundamentals
- Power growth: 2nd order at 2:1 ratio, 3rd order at 3:1 ratio
- Indoor environments amplify 3rd order effects due to reflections

### Future Considerations

1. **Higher Order IMD**: Could add 4th and 5th order calculations for extreme accuracy
2. **Power-Based Weighting**: Dynamic weights based on actual transmitter power levels
3. **Environmental Factors**: Adjustable parameters for indoor/outdoor scenarios
4. **Machine Learning**: Train on real-world interference reports to refine weights
5. **Real-time Monitoring**: Integration with spectrum analyzers for validation