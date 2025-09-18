import pandas as pd
import ta
import pandas_ta as ta


def detect_momentum_rally(df):
    """
    Returns True if the latest 3 candles show bullish momentum:
    - All 3 candles either didn't retest EMA9/MA20 or touched them and bounced
    - At least 2 of the 3 candles are bullish (close > open)
    """
    df = df.copy()
    # st1 = ta.trend.supertrend(df['high'], df['low'], df['close'], length=11, multiplier=2.0)
    # st2 = ta.trend.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=1.0)
    # df['st_11_2'] = st1['SUPERT_11_2.0']
    # df['st_10_1'] = st2['SUPERT_10_1.0']
    # df['above_supertrend'] = (df['close'] > df['st_11_2']) & (df['close'] > df['st_10_1'])

    # Calculate EMA9 and MA20 if not present
    if 'ema9' not in df.columns:
        df['ema9'] = df['close'].ewm(span=9).mean()
    if 'ma20' not in df.columns:
        df['ma20'] = df['close'].rolling(window=20).mean()

    # Bullish candle
    df['bullish'] = df['close'] > df['open']

    # No retest condition
    df['no_retest'] = (df['low'] > df['ema9']) & (df['low'] > df['ma20'])

    # Retest & bounce condition (touch or dip below but still close bullish)
    df['touched_ema_or_ma'] = (df['low'] <= df['ema9']) | (df['low'] <= df['ma20'])
    df['valid_bounce'] = df['bullish'] & df['touched_ema_or_ma']

    # Final valid candles = either no_retest OR retest_and_bounce
    df['valid_rally'] = df['no_retest'] | df['valid_bounce']

    # Shifted 3-candle window
    df['v_0'] = df['valid_rally']
    df['v_1'] = df['valid_rally'].shift(1)
    df['v_2'] = df['valid_rally'].shift(2)

    df['b_0'] = df['bullish']
    df['b_1'] = df['bullish'].shift(1)
    df['b_2'] = df['bullish'].shift(2)

    df['bullish_count'] = df[['b_0', 'b_1', 'b_2']].sum(axis=1)

    # Final momentum condition
    df['momentum_rally'] = (
        df['v_0'] & df['v_1'] & df['v_2'] & (df['bullish_count'] >= 2) 
    )
    df = df.drop(columns=["ema9", "ma20"])
    return df



# def detect_momentum_rally(df):
#     """
#     Detects bullish momentum rally with:
#     - 3 valid candles (no EMA9/MA20 retest or bounce from them)
#     - At least 2 out of 3 candles are bullish
#     - Price above Supertrend (11,2)
#     - Volume spike on latest candle
#     - RSI > 63 and rising
#     OR
#     - MA20 crossover + price above supertrend
#     - RSI > 63 and rising
#     Returns:
#         bool: True if either momentum rally or MA20 crossover conditions are met
#     """
#     df = df.copy()

#     # 🟩 Supertrend
#     df.ta.supertrend(length=11, multiplier=2.0, append=True)
#     df['st_11_2'] = df['SUPERT_11_2.0']
#     df['above_supertrend'] = df['close'] > df['st_11_2']

#     # 🟩 EMA9 and MA20
#     if 'ema9' not in df.columns:
#         df['ema9'] = df['close'].ewm(span=9).mean()
#     if 'ma20' not in df.columns:
#         df['ma20'] = df['close'].rolling(window=20).mean()

#     # 🟩 RSI
#     df['rsi'] = df.ta.rsi(length=14)
#     df['rsi_rising'] = df['rsi'] > df['rsi'].shift(1)
#     df['rsi_valid'] = (df['rsi'] > 63) & df['rsi_rising']

#     # 🟩 Bullish candle check
#     df['bullish'] = df['close'] > df['open']

#     # 🟩 Retest logic
#     df['no_retest'] = (df['low'] > df['ema9']) & (df['low'] > df['ma20'])
#     df['touched_ema_or_ma'] = (df['low'] <= df['ema9']) | (df['low'] <= df['ma20'])
#     df['valid_bounce'] = df['bullish'] & df['touched_ema_or_ma']
#     df['valid_rally'] = df['no_retest'] | df['valid_bounce']

#     # 🟩 3-Candle structure
#     df['v_0'] = df['valid_rally']
#     df['v_1'] = df['valid_rally'].shift(1)
#     df['v_2'] = df['valid_rally'].shift(2)
#     df['b_0'] = df['bullish']
#     df['b_1'] = df['bullish'].shift(1)
#     df['b_2'] = df['bullish'].shift(2)
#     df['bullish_count'] = df[['b_0', 'b_1', 'b_2']].sum(axis=1)

#     # 🟩 Volume spike
#     df['avg_volume'] = df['volume'].rolling(window=10).mean()
#     df['volume_spike'] = df['volume'] > df['avg_volume']

#     # ✅ Momentum Rally Logic
#     df['momentum_rally'] = (
#         df['v_0'] & df['v_1'] & df['v_2'] &
#         (df['bullish_count'] >= 2) &
#         df['above_supertrend'] &
#         df['volume_spike']
#     )

#     # ✅ MA20 Crossover Logic
#     df['ma20_crossover'] = (
#         (df['close'] > df['ma20']) &
#         (df['close'].shift(1) <= df['ma20'].shift(1))
#     )

#     # ✅ Final signal = either momentum rally OR MA20 crossover
#     df['final_signal'] = (df['momentum_rally'] | df['ma20_crossover']) & df['rsi_valid']

#     return df.iloc[-1]['final_signal']





# def detect_range_breakout(df):
#     """
#     Detects bullish breakout from consolidation zone with volume spike and supertrend confirmation.
#     Uses ta.supertrend() for Supertrend(11,2) and (10,1).
#     Returns True if the latest row satisfies all conditions.
#     """
#     df = df.copy()

#     if len(df) < 30:
#         return False  # Not enough data for rolling calculations

#     # 🟩 Calculate Supertrend using ta
#     st1 = ta.trend.supertrend(df['high'], df['low'], df['close'], length=11, multiplier=2.0)
#     st2 = ta.trend.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=1.0)

#     df['st_11_2'] = st1['SUPERT_11_2.0']
#     df['st_10_1'] = st2['SUPERT_10_1.0']

#     # 🔹 Consolidation: prior 3-candle range
#     df['prior_high'] = df['high'].rolling(3).max().shift(1)
#     df['prior_low'] = df['low'].rolling(3).min().shift(1)
#     df['range_size'] = df['prior_high'] - df['prior_low']

#     # Tight range condition
#     df['is_tight_range'] = df['range_size'] < df['range_size'].rolling(10).mean()

#     # Breakout condition
#     df['range_breakout'] = df['high'] > df['prior_high']

#     # 🔸 Volume spike
#     df['avg_vol'] = df['volume'].rolling(10).mean()
#     df['volume_spike'] = df['volume'] > df['avg_vol']

#     # 🟢 Close above both supertrend lines
#     df['above_supertrend'] = (df['close'] > df['st_11_2']) & (df['close'] > df['st_10_1'])

#     # ✅ Final signal
#     df['breakout_signal'] = (
#         df['is_tight_range'] & df['range_breakout'] & df['volume_spike'] & df['above_supertrend']
#     )

#     return df['breakout_signal'].iloc[-1] == True



