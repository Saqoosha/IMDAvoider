MIN_DISPLAY_FREQUENCY = 5100
MAX_DISPLAY_FREQUENCY = 6099
RATING_MAX_VALUE = 100
RATING_DIFF_LIMIT = 35

# Weighting factors for different IMD orders (based on typical signal strengths)
def db_to_linear(db):
    """Convert dB value to linear scale"""
    return 10 ** (db / 10)

# Weight values in dB relative to 2nd order IMD
WEIGHT_2ND_ORDER_DB = 0       # Reference level (0 dB)
WEIGHT_3RD_ORDER_2FREQ_DB = -20  # -20dB relative to 2nd order
WEIGHT_3RD_ORDER_3FREQ_DB = -30  # -30dB relative to 2nd order

# Convert to linear weights
WEIGHT_2ND_ORDER = db_to_linear(WEIGHT_2ND_ORDER_DB)      # 1.0
WEIGHT_3RD_ORDER_2FREQ = db_to_linear(WEIGHT_3RD_ORDER_2FREQ_DB)  # 0.01
WEIGHT_3RD_ORDER_3FREQ = db_to_linear(WEIGHT_3RD_ORDER_3FREQ_DB)  # 0.001

# Different thresholds for different IMD types
THRESHOLD_2ND_ORDER = 35  # Original threshold
THRESHOLD_3RD_ORDER = 25  # Stricter threshold for 3rd order


def isValidFrequency(frequency: int):
    return MIN_DISPLAY_FREQUENCY <= frequency <= MAX_DISPLAY_FREQUENCY


def findNearestFrequency(frequency: int, frequencies: list):
    nearest = frequencies[0]
    for f in frequencies:
        if abs(f - frequency) < abs(nearest - frequency):
            nearest = f
    return nearest


def calculate_2nd_order_imd(f1: int, f2: int):
    """Calculate 2nd order IMD products: 2*f1 - f2"""
    return [2 * f1 - f2]


def calculate_3rd_order_imd_2freq(f1: int, f2: int):
    """Calculate 3rd order IMD products for 2 frequencies
    Returns: list of IMD products that fall within valid frequency range
    """
    imd_products = []
    
    # Type 1: 2*f1 - f2 (already covered in 2nd order, but keeping for clarity)
    # Type 2: 2*f2 - f1
    imd2 = 2 * f2 - f1
    if isValidFrequency(imd2):
        imd_products.append(imd2)
    
    # Type 3 & 4: f1 + 2*f2 and 2*f1 + f2 (usually out of band, but check anyway)
    imd3 = f1 + 2 * f2
    if isValidFrequency(imd3):
        imd_products.append(imd3)
    
    imd4 = 2 * f1 + f2
    if isValidFrequency(imd4):
        imd_products.append(imd4)
    
    return imd_products


def calculate_3rd_order_imd_3freq(f1: int, f2: int, f3: int):
    """Calculate 3rd order IMD products for 3 frequencies
    Returns: list of IMD products that fall within valid frequency range
    
    All 10 patterns from IMDAvoider3:
    1. f1 - f2 + f3
    2. f1 + f2 - f3  
    3. 2*f1 - f2 - f3
    4. f1 + f2 + f3
    5. -f1 + f2 + f3
    6. 2*f1 + f2 - f3
    7. 2*f1 - f2 + f3
    8. f1 - 2*f2 + f3
    9. f1 + 2*f2 - f3
    10. -f1 + 2*f2 + f3
    """
    imd_products = []
    
    # Pattern 1: f1 - f2 + f3
    imd = f1 - f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 2: f1 + f2 - f3
    imd = f1 + f2 - f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 3: 2*f1 - f2 - f3
    imd = 2 * f1 - f2 - f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 4: f1 + f2 + f3
    imd = f1 + f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 5: -f1 + f2 + f3
    imd = -f1 + f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 6: 2*f1 + f2 - f3
    imd = 2 * f1 + f2 - f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 7: 2*f1 - f2 + f3
    imd = 2 * f1 - f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 8: f1 - 2*f2 + f3
    imd = f1 - 2 * f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 9: f1 + 2*f2 - f3
    imd = f1 + 2 * f2 - f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    # Pattern 10: -f1 + 2*f2 + f3
    imd = -f1 + 2 * f2 + f3
    if isValidFrequency(imd):
        imd_products.append(imd)
    
    return imd_products


def calculate_weighted_interference(imd_freq: int, frequencies: list, weight: float, threshold: int):
    """Calculate weighted interference score for a single IMD product"""
    nearest = findNearestFrequency(imd_freq, frequencies)
    difference = abs(imd_freq - nearest)
    
    if difference > threshold:
        return 0
    
    value = threshold - difference
    return value * value * weight


def calcRating(frequencies: list):
    """Enhanced rating calculation including 2nd and 3rd order IMD"""
    n = len(frequencies)
    total_interference = 0
    
    # 2nd order IMD (original calculation)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            
            imd_products = calculate_2nd_order_imd(frequencies[i], frequencies[j])
            for imd in imd_products:
                if isValidFrequency(imd):
                    interference = calculate_weighted_interference(
                        imd, frequencies, WEIGHT_2ND_ORDER, THRESHOLD_2ND_ORDER
                    )
                    total_interference += interference
    
    # 3rd order IMD (2 frequencies)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            
            imd_products = calculate_3rd_order_imd_2freq(frequencies[i], frequencies[j])
            for imd in imd_products:
                interference = calculate_weighted_interference(
                    imd, frequencies, WEIGHT_3RD_ORDER_2FREQ, THRESHOLD_3RD_ORDER
                )
                total_interference += interference
    
    # 3rd order IMD (3 frequencies)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                imd_products = calculate_3rd_order_imd_3freq(
                    frequencies[i], frequencies[j], frequencies[k]
                )
                for imd in imd_products:
                    interference = calculate_weighted_interference(
                        imd, frequencies, WEIGHT_3RD_ORDER_3FREQ, THRESHOLD_3RD_ORDER
                    )
                    total_interference += interference
    
    # Normalize and convert to rating
    # Increased normalization factor to account for additional IMD calculations
    # and weighted scoring system
    normalization_factor = 15 * n  # Increased from 5*n to account for more IMD types
    rating = RATING_MAX_VALUE - (total_interference / normalization_factor)
    
    return max(0, round(rating))  # Ensure rating doesn't go below 0


def calcRating_legacy(frequencies: list):
    """Original rating calculation for comparison"""
    n = len(frequencies)
    total = 0
    for row in range(n):
        for column in range(n):
            if row == column:
                continue
            thirdFrequency = frequencies[row] * 2 - frequencies[column]
            if not isValidFrequency(thirdFrequency):
                continue
            nearest = findNearestFrequency(thirdFrequency, frequencies)
            difference = abs(thirdFrequency - nearest)
            if difference > RATING_DIFF_LIMIT:
                continue
            value = RATING_DIFF_LIMIT - difference
            total += value * value
            # print(f"{row} {column} {thirdFrequency} {nearest} {difference} {value} {total}")
    return round(RATING_MAX_VALUE - total / 5 / n)


def analyze_imd_details(frequencies: list):
    """Analyze and return detailed IMD information for visualization"""
    results = {
        '2nd_order': [],
        '3rd_order_2freq': [],
        '3rd_order_3freq': []
    }
    
    n = len(frequencies)
    
    # 2nd order IMD
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            
            imd_products = calculate_2nd_order_imd(frequencies[i], frequencies[j])
            for imd in imd_products:
                if isValidFrequency(imd):
                    nearest = findNearestFrequency(imd, frequencies)
                    difference = abs(imd - nearest)
                    interference = calculate_weighted_interference(
                        imd, frequencies, WEIGHT_2ND_ORDER, THRESHOLD_2ND_ORDER
                    )
                    results['2nd_order'].append({
                        'imd_freq': imd,
                        'source_freqs': [frequencies[i], frequencies[j]],
                        'formula': f"2×{frequencies[i]} - {frequencies[j]}",
                        'nearest_freq': nearest,
                        'separation': difference,
                        'interference_score': interference,
                        'weight': WEIGHT_2ND_ORDER
                    })
    
    # 3rd order IMD (2 frequencies)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            
            imd_products = calculate_3rd_order_imd_2freq(frequencies[i], frequencies[j])
            for imd in imd_products:
                nearest = findNearestFrequency(imd, frequencies)
                difference = abs(imd - nearest)
                interference = calculate_weighted_interference(
                    imd, frequencies, WEIGHT_3RD_ORDER_2FREQ, THRESHOLD_3RD_ORDER
                )
                
                # Determine formula
                if imd == 2 * frequencies[j] - frequencies[i]:
                    formula = f"2×{frequencies[j]} - {frequencies[i]}"
                elif imd == frequencies[i] + 2 * frequencies[j]:
                    formula = f"{frequencies[i]} + 2×{frequencies[j]}"
                elif imd == 2 * frequencies[i] + frequencies[j]:
                    formula = f"2×{frequencies[i]} + {frequencies[j]}"
                else:
                    formula = f"3rd order IMD"
                
                results['3rd_order_2freq'].append({
                    'imd_freq': imd,
                    'source_freqs': [frequencies[i], frequencies[j]],
                    'formula': formula,
                    'nearest_freq': nearest,
                    'separation': difference,
                    'interference_score': interference,
                    'weight': WEIGHT_3RD_ORDER_2FREQ
                })
    
    # 3rd order IMD (3 frequencies)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                imd_products = calculate_3rd_order_imd_3freq(
                    frequencies[i], frequencies[j], frequencies[k]
                )
                for imd in imd_products:
                    nearest = findNearestFrequency(imd, frequencies)
                    difference = abs(imd - nearest)
                    interference = calculate_weighted_interference(
                        imd, frequencies, WEIGHT_3RD_ORDER_3FREQ, THRESHOLD_3RD_ORDER
                    )
                    
                    # Determine formula
                    if imd == frequencies[i] + frequencies[j] - frequencies[k]:
                        formula = f"{frequencies[i]} + {frequencies[j]} - {frequencies[k]}"
                    elif imd == frequencies[i] - frequencies[j] + frequencies[k]:
                        formula = f"{frequencies[i]} - {frequencies[j]} + {frequencies[k]}"
                    elif imd == -frequencies[i] + frequencies[j] + frequencies[k]:
                        formula = f"-{frequencies[i]} + {frequencies[j]} + {frequencies[k]}"
                    else:
                        formula = f"3rd order IMD (3 freq)"
                    
                    results['3rd_order_3freq'].append({
                        'imd_freq': imd,
                        'source_freqs': [frequencies[i], frequencies[j], frequencies[k]],
                        'formula': formula,
                        'nearest_freq': nearest,
                        'separation': difference,
                        'interference_score': interference,
                        'weight': WEIGHT_3RD_ORDER_3FREQ
                    })
    
    return results


if __name__ == "__main__":
    # Test frequencies
    test_freqs = [5760, 5800, 5840]
    
    # Calculate ratings
    print("Test frequencies:", test_freqs)
    print("Enhanced rating:", calcRating(test_freqs))
    print("Legacy rating:", calcRating_legacy(test_freqs))
    
    # Show detailed analysis
    print("\nDetailed IMD Analysis:")
    details = analyze_imd_details(test_freqs)
    
    for imd_type, products in details.items():
        if products:
            print(f"\n{imd_type.replace('_', ' ').title()}:")
            for p in products[:5]:  # Show first 5 of each type
                if p['interference_score'] > 0:
                    print(f"  {p['formula']} = {p['imd_freq']} MHz")
                    print(f"    Nearest: {p['nearest_freq']} MHz (Δ={p['separation']} MHz)")
                    print(f"    Interference score: {p['interference_score']:.2f}")
