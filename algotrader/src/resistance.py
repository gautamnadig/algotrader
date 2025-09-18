import pandas as pd
import numpy as np

def detect_pivots(df, period=10):
    df = df.copy()
    df['pivot_high'] = df['high'].rolling(window=2 * period + 1, center=True).apply(
        lambda x: int(x[period] == max(x)), raw=True
    ).fillna(0).astype(bool)
    
    df['pivot_low'] = df['low'].rolling(window=2 * period + 1, center=True).apply(
        lambda x: int(x[period] == min(x)), raw=True
    ).fillna(0).astype(bool)
    
    return df

# def find_sr_zones(df, channel_width_pct=5, loopback=290, min_strength=2, max_zones=10):
#     df = df.reset_index(drop=True)
#     pivot_vals = []
#     pivot_types = []

#     for i in range(len(df)):
#         if df.loc[i, 'pivot_high']:
#             pivot_vals.append(df.loc[i, 'high'])
#             pivot_types.append('high')
#         elif df.loc[i, 'pivot_low']:
#             pivot_vals.append(df.loc[i, 'low'])
#             pivot_types.append('low')

#     zones = []

#     for i in range(len(pivot_vals)):
#         ref_val = pivot_vals[i]
#         zone_min = ref_val - (ref_val * channel_width_pct / 100)
#         zone_max = ref_val + (ref_val * channel_width_pct / 100)
#         strength = sum(zone_min <= pv <= zone_max for pv in pivot_vals)
#         if strength >= min_strength:
#             zones.append((zone_min, zone_max, strength))

#     strong_zones = sorted(zones, key=lambda x: x[2], reverse=True)
#     final_zones = []
#     seen = []

#     for zone in strong_zones:
#         midpoint = (zone[0] + zone[1]) / 2
#         if all(abs(midpoint - (z[0] + z[1]) / 2) > (midpoint * channel_width_pct / 100) for z in seen):
#             seen.append(zone)
#             final_zones.append(zone)
#         if len(final_zones) >= max_zones:
#             break

#     # Add symbol from original df (assumes same symbol in all rows)
#     symbol = df['symbol'].iloc[0] #if 'symbol' in df.columns else 'N/A'

#     zone_df = pd.DataFrame(final_zones, columns=['zone_low', 'zone_high', 'strength'])
#     zone_df['type'] = np.where((zone_df['zone_low'] + zone_df['zone_high']) / 2 > df['close'].iloc[-1], 'resistance', 'support')
#     zone_df['label'] = np.where(zone_df['strength'] >= 5, 'strong', 'weak')
#     zone_df['symbol'] = symbol

#     return zone_df.sort_values(by='zone_low').reset_index(drop=True)

def find_sr_zones(df, channel_width_pct=5, loopback=290, min_strength=2, max_zones=10):
    df = df.reset_index(drop=True)
    pivot_vals = []
    pivot_types = []

    for i in range(len(df)):
        if df.loc[i, 'pivot_high']:
            pivot_vals.append(df.loc[i, 'high'])
            pivot_types.append('high')
        elif df.loc[i, 'pivot_low']:
            pivot_vals.append(df.loc[i, 'low'])
            pivot_types.append('low')

    zones = []

    for i in range(len(pivot_vals)):
        ref_val = pivot_vals[i]
        zone_min = ref_val - (ref_val * channel_width_pct / 100)
        zone_max = ref_val + (ref_val * channel_width_pct / 100)
        strength = sum(zone_min <= pv <= zone_max for pv in pivot_vals)
        if strength >= min_strength:
            zones.append((zone_min, zone_max, strength))

    strong_zones = sorted(zones, key=lambda x: x[2], reverse=True)
    final_zones = []
    seen = []

    for zone in strong_zones:
        midpoint = (zone[0] + zone[1]) / 2
        if all(abs(midpoint - (z[0] + z[1]) / 2) > (midpoint * channel_width_pct / 100) for z in seen):
            seen.append(zone)
            final_zones.append(zone)
        if len(final_zones) >= max_zones:
            break

    # Add symbol from original df (assumes same symbol in all rows)
    symbol = df['symbol'].iloc[0]

    zone_df = pd.DataFrame(final_zones, columns=['zone_low', 'zone_high', 'strength'])
    zone_df['type'] = np.where((zone_df['zone_low'] + zone_df['zone_high']) / 2 > df['close'].iloc[-1], 'resistance', 'support')
    zone_df['label'] = np.where(zone_df['strength'] >= 5, 'strong', 'weak')
    zone_df['symbol'] = symbol

    # 🔁 Add dummy resistance if none found
    if 'resistance' not in zone_df['type'].values:
        dummy = pd.DataFrame([{
            'zone_low': 450,
            'zone_high': 500,
            'strength': 1,
            'type': 'resistance',
            'label': 'weak',
            'symbol': symbol
        }])
        zone_df = pd.concat([zone_df, dummy], ignore_index=True)

    return zone_df.sort_values(by='zone_low').reset_index(drop=True)


def extract_strong_resistance_with_original_range(zones_df):
    """
    Return only one strong resistance zone with its original zone_low and zone_high.
    """
    symbol = zones_df['symbol'].iloc[0] if 'symbol' in zones_df.columns else 'N/A'

    resistance_zones = zones_df[(zones_df['type'] == 'resistance') & (zones_df['label'] == 'strong')]
    resistance_zones1 = zones_df[(zones_df['type'] == 'resistance') & (zones_df['label'] == 'weak')]

    if not resistance_zones.empty:
        target_zone = resistance_zones
    elif not resistance_zones1.empty:
        target_zone = resistance_zones1
    else:
        return None  # or return e

    resistance_zone = target_zone.loc[target_zone['zone_low'].idxmin()]

    return pd.DataFrame([{
        'symbol': symbol,
        'Rlow': resistance_zone['zone_low'],
        'Rhigh': resistance_zone['zone_high'],
        'type': 'resistance'
    }])
