import imd
import sys

# Configuration options
BANDWIDTH_OPTIONS = {
    'analog': 17,           # Traditional analog FPV
    'hdzero-narrow': 17,    # HDZero narrow mode
    'hdzero': 27,          # HDZero standard mode
    'dji': 20,             # DJI Digital FPV (approximate)
}

# Parse command line arguments
if len(sys.argv) > 1:
    bandwidth_mode = sys.argv[1].lower()
    if bandwidth_mode in BANDWIDTH_OPTIONS:
        channel_width = BANDWIDTH_OPTIONS[bandwidth_mode]
        print(f"Using {bandwidth_mode} mode with {channel_width} MHz bandwidth")
    else:
        print(f"Unknown bandwidth mode: {bandwidth_mode}")
        print(f"Available options: {', '.join(BANDWIDTH_OPTIONS.keys())}")
        sys.exit(1)
else:
    # Default to analog/HDZero narrow mode
    bandwidth_mode = 'analog'
    channel_width = 17
    print(f"Using default analog mode with {channel_width} MHz bandwidth")
    print(f"Usage: python app.py [mode]")
    print(f"Available modes: {', '.join(BANDWIDTH_OPTIONS.keys())}")

# FPV Band Frequencies (in MHz) with channel numbers
# 全チャンネル定義（アナログ用）
fpv_bands_analog = {
    'R': [(5658, 1), (5695, 2), (5732, 3), (5769, 4), (5806, 5), (5843, 6), (5880, 7), (5917, 8)],  # Raceband
    'F': [(5740, 1), (5760, 2), (5780, 3), (5800, 4), (5820, 5), (5840, 6), (5860, 7), (5880, 8)],  # Fatshark
    'A': [(5865, 1), (5845, 2), (5825, 3), (5805, 4), (5785, 5), (5765, 6), (5745, 7), (5725, 8)],  # Boscam A
    'B': [(5733, 1), (5752, 2), (5771, 3), (5790, 4), (5809, 5), (5828, 6), (5847, 7), (5866, 8)],  # Boscam B
    'E': [(5705, 1), (5685, 2), (5665, 3), (5645, 4), (5885, 5), (5905, 6), (5925, 7), (5945, 8)],  # Band E
}

# HDZero用チャンネル定義（R全部、Fの1,4、Eの1のみ）
fpv_bands_hdzero = {
    'R': [(5658, 1), (5695, 2), (5732, 3), (5769, 4), (5806, 5), (5843, 6), (5880, 7), (5917, 8)],  # Raceband全部
    'F': [(5740, 1), (5800, 4)],  # Fatsharkの1と4のみ
    'E': [(5705, 1)],  # Band Eの1のみ
}

# 実行モードに応じてFPVバンドテーブルを選択
if bandwidth_mode in ['hdzero', 'hdzero-narrow']:
    fpv_bands = fpv_bands_hdzero
    print(f"Using HDZero channel configuration: R(1-8), F(1,4), E(1)")
else:
    fpv_bands = fpv_bands_analog
    print(f"Using analog channel configuration: All bands and channels")

# Define the range we want to use
min_freq = 5640
max_freq = 5830

# Get all unique frequencies sorted and filtered by range
# Filter to ensure the entire channel bandwidth fits within the range
all_frequencies = sorted(set(freq for band in fpv_bands.values() for freq, ch in band))
filtered_frequencies = [freq for freq in all_frequencies 
                       if (freq - channel_width/2) >= min_freq and (freq + channel_width/2) <= max_freq]

print(f"Total FPV frequencies: {len(all_frequencies)}")
print(f"Frequencies that fit entirely in range {min_freq}-{max_freq} MHz: {len(filtered_frequencies)}")
print(f"Available frequencies: {filtered_frequencies}")
print(f"Channel edges: {min_freq + channel_width/2:.1f} to {max_freq - channel_width/2:.1f} MHz")

# Parameters for segment selection
segments_needed = 4

# Use filtered FPV frequencies as center points
all_segments = filtered_frequencies


# Function to check if two frequencies are too close
def do_segments_overlap(seg1, seg2):
    min_separation = channel_width + 1  # Minimum separation = channel width + 1 MHz gap
    return abs(seg1 - seg2) < min_separation


# Recursive function to find valid combinations of segments
def find_combinations(segments, needed, current_combination=[]):
    if needed == 0:
        return [current_combination]

    if not segments:
        return []

    combinations = []
    for i in range(len(segments)):
        # Check if the current segment overlaps with any segment in the current combination
        if any(do_segments_overlap(segments[i], seg) for seg in current_combination):
            continue
        # Recursive call to find further combinations with the remaining segments
        combinations.extend(find_combinations(segments[i + 1 :], needed - 1, current_combination + [segments[i]]))
    return combinations


# Find all valid combinations of the required number of segments
valid_combinations = find_combinations(all_segments, segments_needed)

# Display the count of combinations and the first 5 combinations for verification
print(f"Total combinations: {len(valid_combinations)}")
# print("First 5 combinations:", valid_combinations[:5])

# calc rating for all combinations
ratings = []
for combination in valid_combinations:
    rating = imd.calcRating(combination)
    ratings.append((rating, combination))
    # print(f"Rating: {rating} - {combination}")

# sort ratings
ratings.sort(key=lambda x: x[0], reverse=True)

# Create frequency to band/channel mapping for display
freq_to_band_ch = {}
for band_name, band_data in fpv_bands.items():
    for freq, ch in band_data:
        if freq not in freq_to_band_ch:
            freq_to_band_ch[freq] = []
        freq_to_band_ch[freq].append((band_name, ch))

# display top 10 ratings with comparison to legacy
print("\nTop 10 FPV frequency combinations (Enhanced IMD Analysis):")
print("Note: Enhanced and Legacy ratings use different calculation methods and cannot be directly compared.")
for i, (rating, combination) in enumerate(ratings[:10], 1):
    band_info = []
    legacy_rating = imd.calcRating_legacy(combination)
    for freq in combination:
        band_ch_list = freq_to_band_ch.get(freq, [('?', '?')])
        band_ch_str = '/'.join([f"{b}{ch}" for b, ch in band_ch_list])
        band_info.append(f"{freq}MHz({band_ch_str})")
    print(f"{i}. Rating: {rating} (Legacy: {legacy_rating}) - {', '.join(band_info)}")

# Display as table
print("\n" + "="*80)
print("Rank | Rating | Ch1        | Ch2        | Ch3        | Ch4        ")
print("-"*80)
for i, (rating, combination) in enumerate(ratings[:10], 1):
    ch_strs = []
    for freq in combination:
        band_ch_list = freq_to_band_ch.get(freq, [('?', '?')])
        band_ch_str = '/'.join([f"{b}{ch}" for b, ch in band_ch_list])
        ch_strs.append(f"{freq}({band_ch_str})")
    print(f"{i:4d} | {rating:6d} | {ch_strs[0]:10s} | {ch_strs[1]:10s} | {ch_strs[2]:10s} | {ch_strs[3]:10s}")
print("="*80)


def drawResults(results, show_imd=False):
    import matplotlib.pyplot as plt

    # Create frequency to band/channel mapping
    freq_to_band_ch = {}
    for band_name, band_data in fpv_bands.items():
        for freq, ch in band_data:
            if freq not in freq_to_band_ch:
                freq_to_band_ch[freq] = []
            freq_to_band_ch[freq].append((band_name, ch))

    # Create a new figure
    plt.figure(figsize=(14, 10))

    # Channel width is already defined globally

    # Plot all FPV frequencies as vertical lines
    band_colors = {'R': 'red', 'F': 'blue', 'A': 'green', 'B': 'orange', 'E': 'purple'}
    
    # Plot background bands
    for band_name, band_data in fpv_bands.items():
        for freq, ch in band_data:
            if min_freq <= freq <= max_freq:
                plt.axvline(x=freq, color=band_colors[band_name], alpha=0.2, linewidth=1)

    # Plot the top combinations with channel bandwidth (reversed order)
    for i, (rating, combination) in enumerate(results):
        # Reverse the index so best is at top
        plot_index = len(results) - 1 - i
        for freq in combination:
            # Get band(s) and channel(s) for this frequency
            band_ch_list = freq_to_band_ch.get(freq, [('?', '?')])
            band = band_ch_list[0][0]  # Primary band
            band_ch_str = '/'.join([f"{b}{ch}" for b, ch in band_ch_list])
            band_color = band_colors.get(band, 'gray')
            
            # Plot channel bandwidth as a rectangle
            start_freq = freq - channel_width / 2
            end_freq = freq + channel_width / 2
            
            # Draw channel bandwidth rectangle
            plt.fill([start_freq, end_freq, end_freq, start_freq], 
                    [plot_index - 0.4, plot_index - 0.4, plot_index + 0.4, plot_index + 0.4], 
                    color=band_color, alpha=0.3, edgecolor=band_color, linewidth=2)
            
            # Display frequency with band and channel
            plt.text(freq, plot_index - 0.05, f"{freq}", ha="center", va="center", 
                    fontsize=8, weight="bold", color='black')
            plt.text(freq, plot_index + 0.25, band_ch_str, ha="center", va="center", 
                    fontsize=9, weight="bold", color='white',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=band_color, alpha=0.8))
        
        # Add rating on the left side
        plt.text(min_freq - 8, plot_index, f"Rating: {rating}", ha="right", va="center", 
                fontsize=10, weight="bold")
        
        # Optionally show IMD products for this combination
        if show_imd and i == 0:  # Only show for the best combination
            imd_details = imd.analyze_imd_details(combination)
            imd_colors = {
                '2nd_order': 'red',
                '3rd_order_2freq': 'orange', 
                '3rd_order_3freq': 'yellow'
            }
            
            # Plot significant IMD products
            for imd_type, products in imd_details.items():
                for p in products:
                    if p['interference_score'] > 0 and min_freq <= p['imd_freq'] <= max_freq:
                        # Draw vertical line for IMD product
                        plt.axvline(x=p['imd_freq'], ymin=(plot_index-0.4)/len(results), 
                                   ymax=(plot_index+0.4)/len(results),
                                   color=imd_colors[imd_type], alpha=0.7, linewidth=2,
                                   linestyle='--')
                        # Add small text label
                        plt.text(p['imd_freq'], plot_index - 0.6, 'IMD', 
                                ha='center', va='top', fontsize=6,
                                color=imd_colors[imd_type], weight='bold')

    # Add grid and labels
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Combination Rank")
    plt.title(f"Top FPV Frequency Combinations - {channel_width}MHz Channel Bandwidth\n(Range: {min_freq}-{max_freq} MHz)")
    plt.grid(True, alpha=0.3)
    plt.xlim(min_freq - 10, max_freq + 10)
    plt.ylim(-1, len(results))

    # Add frequency range indicators
    plt.axvline(x=min_freq, color='black', linestyle='--', alpha=0.5)
    plt.axvline(x=max_freq, color='black', linestyle='--', alpha=0.5)
    plt.text(min_freq, len(results) - 0.5, f'{min_freq} MHz', rotation=90, va='bottom', ha='right')
    plt.text(max_freq, len(results) - 0.5, f'{max_freq} MHz', rotation=90, va='bottom', ha='left')

    # Add IMD legend if showing IMD
    if show_imd:
        from matplotlib.patches import Patch
        imd_legend_elements = [
            Patch(facecolor='red', alpha=0.7, label='2nd Order IMD'),
            Patch(facecolor='orange', alpha=0.7, label='3rd Order IMD (2-freq)'),
            Patch(facecolor='yellow', alpha=0.7, label='3rd Order IMD (3-freq)')
        ]
        plt.legend(handles=imd_legend_elements, loc='upper right')

    # Display the plot
    plt.tight_layout()
    plt.show()


# Show detailed IMD analysis for the best combination
print("\nDetailed IMD Analysis for Best Combination:")
best_combination = ratings[0][1]
imd_details = imd.analyze_imd_details(best_combination)

print(f"Frequencies: {best_combination}")
print(f"Enhanced Rating: {ratings[0][0]}, Legacy Rating: {imd.calcRating_legacy(best_combination)}")

# Count significant IMD products
significant_imd_count = {
    '2nd_order': sum(1 for p in imd_details['2nd_order'] if p['interference_score'] > 0),
    '3rd_order_2freq': sum(1 for p in imd_details['3rd_order_2freq'] if p['interference_score'] > 0),
    '3rd_order_3freq': sum(1 for p in imd_details['3rd_order_3freq'] if p['interference_score'] > 0)
}

print(f"\nSignificant IMD products:")
print(f"  2nd order: {significant_imd_count['2nd_order']}")
print(f"  3rd order (2-freq): {significant_imd_count['3rd_order_2freq']}")
print(f"  3rd order (3-freq): {significant_imd_count['3rd_order_3freq']}")

# Show worst interference cases
all_imd = []
for imd_type, products in imd_details.items():
    for p in products:
        if p['interference_score'] > 0:
            all_imd.append((p['interference_score'], imd_type, p))

all_imd.sort(key=lambda x: x[0], reverse=True)
print(f"\nWorst 5 interference cases:")
for score, imd_type, product in all_imd[:5]:
    print(f"  {product['formula']} = {product['imd_freq']} MHz")
    print(f"    Type: {imd_type.replace('_', ' ').title()}")
    print(f"    Separation: {product['separation']} MHz, Score: {score:.2f}")

# Draw standard results
drawResults(ratings[:10])

# Draw results with IMD visualization for the best combination
print("\nGenerating visualization with IMD products...")
drawResults(ratings[:1], show_imd=True)
