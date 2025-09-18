import pandas as pd
import datetime as dt
import json
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
import duckdb as db
import pandas_ta as ta
# from placeOrder import check_order_status,place_bo_order,get_order_state
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np
# from highlight_row import highlight_supertrend
from ta.momentum import RSIIndicator
import ta
import time
from resistance import detect_pivots,find_sr_zones,extract_strong_resistance_with_original_range
from momentum_rally import detect_momentum_rally



def angle(series, atr):
    rad2deg = 180 / np.pi
    slope = rad2deg * np.arctan((series - series.shift(1)) / atr)
    return slope

def maAngle(df):
    df = df
    # Calculate ohlc4
    df['ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    # df['ATR1'] = compute_atr(df)

    # EMA20 and its slope
    df['ema20'] = df['ohlc4'].ewm(span=20, adjust=False).mean()
    df['ema20_slope'] = angle(df['ema20'], df['ATR'])


    
    # Boolean column: is slope >= 4 degrees?
    df['ma20 SL4'] = df['ema20_slope'] >= 4
    
    return df



def compute_rsi(df, price_col='close', period=14, smoothing_period=7):
    df = df.copy()
    
    # Compute RSI using Wilder’s method (ta lib matches TradingView)
    rsi_calc = RSIIndicator(close=df[price_col], window=period)
    df['RSI'] = rsi_calc.rsi()
    
    # Add arrow column showing RSI rising
    arrow = '\u2191'
    df[f'RSI {arrow}'] = df['RSI'] > df['RSI'].shift(1)
    df['RSI_Smooth'] = df['RSI'].rolling(window=smoothing_period).mean()
    df[f'RSI{arrow} SML'] = df['RSI'] > df['RSI_Smooth']
    
    return df

def compute_atr(df, period=14):
    df = df.copy()
    atr_indicator = ta.volatility.AverageTrueRange(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=period,
        fillna=False
    )
    df['ATR'] = atr_indicator.average_true_range()
    return df

def compute_cvd(df, close_col='close', volume_col='volume'):
    df = df.copy()
    
    # Calculate price change
    close_diff = df[close_col].diff()

    # Estimate delta (buy vs sell volume)
    df['delta'] = np.where(
        close_diff > 0, df[volume_col], 
        np.where(close_diff < 0, -df[volume_col], 0)
    )
    
    # Cumulative Volume Delta
    df['CVD'] = df['delta'].cumsum()
    
    # CVD Up Arrow: is CVD increasing?
    arrow = '\u2191'  # ↑
    df[f'CVD {arrow}'] = df['CVD'] > df['CVD'].shift(1)
    
    return df

def detect_ema9_bounce(df):
    df = df.copy()

    # Step 1: Calculate EMA9
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()

    # Step 2: Shifted values for comparison
    df['prev_close'] = df['close'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    df['prev_ema9'] = df['EMA9'].shift(1)

    # Step 3: Bounce Condition
    df['EMA9_support_bounce_base'] = (
        (df['prev_low'] <= df['prev_ema9']) &           # previous low dipped to or below EMA9
        (df['prev_close'] > df['prev_ema9']) &          # previous close above EMA9
        (df['close'] > df['open']) &                    # current candle is green
        (df['close'] > df['EMA9'])                      # current close above EMA9
    )

    # Step 4: Fresh Bounce — no bounce in previous candle
    df['EMA9 SuP'] = df['EMA9_support_bounce_base'] & \
                     (~df['EMA9_support_bounce_base'].shift(1).fillna(True).astype(bool))

    return df


def candle_logic5(candle_data,symb):
        
    df_candle = pd.DataFrame(candle_data["candles"],columns=["timestamp", "open", "high", "low", "close", "volume"])
    df_candle["symbol"] = symb
    df_candle["timestamp"] = (
        pd.to_datetime(df_candle["timestamp"], unit="s", utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.strftime("%m-%d %H:%M:%S")
    )
    df_candle['ltp'] = df_candle.iloc[-1]["close"]
    ## calculate momentum
    # momentum_candle = fryers_hist_momentum(symb,auth_code)
    # momentum_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    # df_momentum = pd.DataFrame(momentum_candle["candles"],columns=momentum_columns)
    # momentum_flag = detect_momentum_rally(df_momentum)
    # crossover_flag = check_ma20_crossover_with_supertrend(df_momentum)

    ## candle calculation
    df_candle = df_candle.sort_values(by="timestamp").reset_index(drop=True)
    df_candle.ta.supertrend(length=11, multiplier=2.0, append=True)

    df_candle["symbol"] = symb
    df_candle = df_candle[['symbol','timestamp','open','close','SUPERT_11_2.0','high','low','volume','ltp']].rename(columns={'SUPERT_11_2.0':'supertrend'})
    df_candle = df_candle.drop_duplicates(subset='timestamp', keep='first')

    df_candle.loc[:, 'MA20'] = df_candle['close'].rolling(window=20).mean()
    df_candle.loc[:,'Above_MA20'] = df_candle['close'] > df_candle['MA20']
    df_candle.loc[:, 'prev_Above_MA20'] = df_candle['Above_MA20'].shift(1)
    df_candle.loc[:,'20 CXover'] = (df_candle['Above_MA20'] == True) & (df_candle['prev_Above_MA20'] == False)
    df_candle.loc[:,'Above ST11'] = df_candle['close'] > df_candle['supertrend']
    
    
    # #ATR calculations
    df_candle = compute_atr(df_candle)
    arrow = '\u2191'
    df_candle[f'ATR {arrow}'] = df_candle['ATR'] > df_candle['ATR'].shift(1)
    # MA 20 Bounce calculation
    # arrow = '\u2191'
    df_candle['prev_close'] = df_candle['close'].shift(1)
    df_candle['prev_low'] = df_candle['low'].shift(1)
    df_candle['prev_ma20'] = df_candle['MA20'].shift(1)
    df_candle['MA20_support_bounce_base'] = ((df_candle['prev_low'] <= df_candle['prev_ma20']) & (df_candle['prev_close'] > df_candle['prev_ma20']) &  (df_candle['close'] > df_candle['open']) & (df_candle['close'] > df_candle['MA20']))
    df_candle['MA20 SuP'] = df_candle['MA20_support_bounce_base'] & (~df_candle['MA20_support_bounce_base'].shift(1).fillna(True).astype(bool))

    # df_candle = maAngle(df_candle)
    df_candle = compute_rsi(df_candle)
    df_candle = compute_cvd(df_candle)
    df_candle = detect_ema9_bounce(df_candle)

    df_resis = detect_pivots(df_candle)
    df_resis = find_sr_zones(df_resis)
    df_resis = extract_strong_resistance_with_original_range(df_resis)
    
    dbdf1 = db.query("select a.*,b.Rlow ,b.Rhigh from df_candle a join df_resis b on a.symbol = b.symbol")
    df = dbdf1.df()

    df[f'LTP {arrow}'] = df['ltp'] > df['high'].shift(1)
    df[f'EMA{arrow} MA'] = df['EMA9'] > df['MA20']
    # df = df.set_index('timestamp')
    df = df[['timestamp','high','close','low','ltp','supertrend','20 CXover','MA20 SuP','EMA9 SuP',f'EMA{arrow} MA',f'LTP {arrow}','Above ST11',f'ATR {arrow}',f'CVD {arrow}',f'RSI {arrow}',f'RSI{arrow} SML','ATR','RSI','Rlow','Rhigh']]. \
                rename(columns={'ltp':'LTP','timestamp':'Time','supertrend':'ST 11','20 CXover':'20 CXvr','ATR':'ATR','Above ST11':f'ST11{arrow}','Rlow':'R LW','Rhigh':'R HG'})
    df = df.reset_index(drop=True)
    df.index.name = None
    df = df.sort_values(by='Time', ascending=False)
    df = df.head(35)
    return df

### 15 min candle logic
def candle_logic15(candle_data,symb):
        
    df_candle = pd.DataFrame(candle_data["candles"],columns=["timestamp", "open", "high", "low", "close", "volume"])
    df_candle["symbol"] = symb
    df_candle["timestamp"] = (
        pd.to_datetime(df_candle["timestamp"], unit="s", utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.strftime("%m-%d %H:%M:%S")
    )
    df_candle['ltp'] = df_candle.iloc[-1]["close"]
    # calculate momentum
    df_candle = detect_momentum_rally(df_candle)
    

    ## candle calculation
    df_candle = df_candle.sort_values(by="timestamp").reset_index(drop=True)
    df_candle.ta.supertrend(length=11, multiplier=2.0, append=True)

    df_candle["symbol"] = symb
    df_candle = df_candle[['symbol','timestamp','open','close','SUPERT_11_2.0','high','low','volume','ltp','momentum_rally']].rename(columns={'SUPERT_11_2.0':'supertrend'})
    df_candle = df_candle.drop_duplicates(subset='timestamp', keep='first')

    df_candle.loc[:, 'MA20'] = df_candle['close'].rolling(window=20).mean()
    df_candle.loc[:,'Above_MA20'] = df_candle['close'] > df_candle['MA20']
    df_candle.loc[:, 'prev_Above_MA20'] = df_candle['Above_MA20'].shift(1)
    df_candle.loc[:,'20 CXover'] = (df_candle['Above_MA20'] == True) & (df_candle['prev_Above_MA20'] == False)
    df_candle.loc[:,'Above ST11'] = df_candle['close'] > df_candle['supertrend']
    
    
    # #ATR calculations
    df_candle = compute_atr(df_candle)
    arrow = '\u2191'
    df_candle[f'ATR {arrow}'] = df_candle['ATR'] > df_candle['ATR'].shift(1)
    # MA 20 Bounce calculation
    # arrow = '\u2191'
    df_candle['prev_close'] = df_candle['close'].shift(1)
    df_candle['prev_low'] = df_candle['low'].shift(1)
    df_candle['prev_ma20'] = df_candle['MA20'].shift(1)
    df_candle['MA20_support_bounce_base'] = ((df_candle['prev_low'] <= df_candle['prev_ma20']) & (df_candle['prev_close'] > df_candle['prev_ma20']) &  (df_candle['close'] > df_candle['open']) & (df_candle['close'] > df_candle['MA20']))
    df_candle['MA20 SuP'] = df_candle['MA20_support_bounce_base'] & (~df_candle['MA20_support_bounce_base'].shift(1).fillna(True).astype(bool))

    # df_candle = maAngle(df_candle)
    df_candle = compute_rsi(df_candle)
    df_candle = compute_cvd(df_candle)
    df_candle = detect_ema9_bounce(df_candle)

    df_resis = detect_pivots(df_candle)
    df_resis = find_sr_zones(df_resis)
    df_resis = extract_strong_resistance_with_original_range(df_resis)
    
    dbdf1 = db.query("select a.*,b.Rlow ,b.Rhigh from df_candle a join df_resis b on a.symbol = b.symbol")
    df = dbdf1.df()

    df[f'LTP {arrow}'] = df['ltp'] > df['high'].shift(1)
    df[f'EMA{arrow} MA'] = df['EMA9'] > df['MA20']
    # df = df.set_index('timestamp')
    df = df[['timestamp','high','close','low','ltp','supertrend','20 CXover','MA20 SuP','EMA9 SuP',f'EMA{arrow} MA',f'LTP {arrow}','Above ST11',f'ATR {arrow}',f'CVD {arrow}',f'RSI {arrow}',f'RSI{arrow} SML','ATR','RSI','Rlow','Rhigh','momentum_rally']]. \
                rename(columns={'ltp':'LTP','timestamp':'Time','supertrend':'ST 11','20 CXover':'20 CXvr','ATR':'ATR','Above ST11':f'ST11{arrow}','Rlow':'R LW','Rhigh':'R HG'})
    df = df.reset_index(drop=True)
    df.index.name = None
    df = df.sort_values(by='Time', ascending=False)
    df = df.head(35)
    return df


def check_entry_conditions_5min(df):
    arrow = '\u2191'
    latest = df.iloc[0]   
    previous = df.iloc[1]

    ### entry conditions
    entry_trigger = (previous['20 CXvr'] or previous['MA20 SuP'] or latest['20 CXvr'] or latest['MA20 SuP'] or previous['EMA9 SuP']) and latest[f'ST11{arrow}'] and latest[f'LTP {arrow}'] and latest[f'CVD {arrow}']
    # resis = (((latest['Rlow'] - latest['LTP']) > 5) or (latest['LTP'] > latest['Rhigh'] + 5)) and not (latest['LTP'] >= latest['Rlow'] and latest['LTP'] <= latest['Rhigh'])
    # resis = (latest['LTP'] >= (latest['R LW'] - 5) and latest['LTP'] <= (latest['R HG'] + 2) and not latest[f'LTP {arrow}'])
    first_block = latest['ATR'] >= 8 and latest[f'ATR {arrow}'] and latest[f'RSI {arrow}'] and previous[f'RSI{arrow} SML'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and previous[f'EMA{arrow} MA']
    second_block = latest['RSI'] >= 63 and latest[f'RSI {arrow}'] and latest[f'ATR {arrow}'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and  previous[f'RSI{arrow} SML']
    third_block = latest[f'ST11{arrow}'] and latest['RSI'] >= 70 and previous['RSI'] >= 68 and latest[f'RSI {arrow}'] and latest[f'ATR {arrow}'] and latest['ATR'] >= 12 and latest[f'LTP {arrow}'] \
                    and latest[f'CVD {arrow}'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and previous[f'EMA{arrow} MA']
    
    condition1 = (entry_trigger and first_block)
    condition2 = (entry_trigger and second_block)
    condition3 = (third_block)
    

    triggered_conditions = None
    if condition1:
        triggered_conditions = "5min:Condition1"
    if condition2:
        triggered_conditions = "5min:Condition2"
    # if condition3:
    #     triggered_conditions = "5min:Condition3"


    return (condition1 or condition2),triggered_conditions


def check_entry_conditions_15min(df):
    arrow = '\u2191'
    latest = df.iloc[0]   
    previous = df.iloc[1]
    sprevious = df.iloc[2]
    tprevious = df.iloc[3]

    ### entry conditions
    entry_trigger = (previous['20 CXvr'] or previous['MA20 SuP'] or latest['20 CXvr'] or latest['MA20 SuP'] or previous['EMA9 SuP'] or sprevious['EMA9 SuP'] or tprevious['EMA9 SuP']) and latest[f'ST11{arrow}'] and latest[f'LTP {arrow}'] and latest[f'CVD {arrow}']
    # resis = (((latest['Rlow'] - latest['LTP']) > 5) or (latest['LTP'] > latest['Rhigh'] + 5)) and not (latest['LTP'] >= latest['Rlow'] and latest['LTP'] <= latest['Rhigh'])
    resis = (latest['LTP'] >= (latest['R LW'] - 5) and latest['LTP'] <= (latest['R HG'] + 2))
    first_block = latest['ATR'] >= 10 and latest[f'ATR {arrow}'] and latest[f'RSI {arrow}'] and previous[f'RSI{arrow} SML'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and previous[f'EMA{arrow} MA']
    second_block = latest['RSI'] >= 63 and latest[f'RSI {arrow}'] and latest[f'ATR {arrow}'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and  previous[f'RSI{arrow} SML']
    third_block = latest[f'ST11{arrow}'] and latest['RSI'] >= 70 and previous['RSI'] >= 68 and latest[f'RSI {arrow}'] and latest[f'ATR {arrow}'] and latest['ATR'] >= 12 and latest[f'LTP {arrow}'] \
                    and latest[f'CVD {arrow}'] and latest[f'RSI{arrow} SML'] and latest[f'EMA{arrow} MA'] and previous[f'EMA{arrow} MA']
    fourth_block = latest['momentum_rally'] and latest[f'ST11{arrow}'] and latest[f'RSI{arrow} SML'] and latest[f'LTP {arrow}'] and latest[f'CVD {arrow}'] and latest['RSI'] >= 70 and previous['RSI'] >= 68
    
    condition1 = (entry_trigger and first_block and not resis)
    condition2 = (entry_trigger and second_block and not resis)
    condition3 = (third_block and not resis)
    condition4 = (fourth_block and not resis)


    triggered_conditions = None
    if condition1:
        triggered_conditions = "15min:Condition1"
    if condition2:
        triggered_conditions=  "15min:Condition2"
    if condition3:
        triggered_conditions = "15min:Condition3"
    if condition4:
        triggered_conditions = "15min:Condition4"


    return (condition1 or condition2 or condition3 or condition4),triggered_conditions
