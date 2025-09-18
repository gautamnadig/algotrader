import pandas as pd

def highlight_supertrend(row):
    st_11 = row.get('ST 11')
    # st_10 = row.get('ST 10')
    close = row.get('close')
    
    styles = [''] * len(row)
    columns = list(row.index)
    
    if pd.notna(st_11) and pd.notna(close):
        st_11_index = row.index.get_loc('ST 11')
        if st_11 < close:
            styles[st_11_index] = 'background-color: lightgreen'
        elif st_11 > close:
            styles[st_11_index] = 'background-color: lightcoral'

    # if pd.notna(st_10) and pd.notna(close):
    #     st_10_index = row.index.get_loc('ST 10')
    #     if st_10 < close:
    #         styles[st_10_index] = 'background-color: lightgreen'
    #     elif st_10 > close:
    #         styles[st_10_index] = 'background-color: lightcoral'

    
# Make '20 CXvr' and 'MA20 Sup' bold if True
    if '20 CXvr' in columns:
        idx = columns.index('20 CXvr')
        if row['20 CXvr'] == True:
            styles[idx] = 'font-weight: bold; background-color: darkgreen;'
        else:
            styles[idx] = 'background-color: lightblue;'


    if 'MA20 SuP' in columns:
        idx = columns.index('MA20 SuP')
        if row['MA20 SuP'] == True:
            # current_style = styles.get(idx, "")
            styles[idx] = 'font-weight: bold; background-color: darkgreen;'
        else:
            styles[idx] = 'background-color: lightblue;'
    
    if 'EMA9 SuP' in columns:
        idx = columns.index('EMA9 SuP')
        if row['EMA9 SuP'] == True:
            # current_style = styles.get(idx, "")
            styles[idx] = 'font-weight: bold; background-color: darkgreen;'
        else:
            styles[idx] = 'background-color: lightblue;'



    arrow = '\u2191'
    st11col = f'ST11{arrow}'
    if st11col in columns:
        idx = columns.index(st11col)
        if row[st11col] == True:
            styles[idx] = 'font-weight: bold;'

    # arrow = '\u2191'
    # st10col = f'ST10{arrow}'
    # if st10col in columns:
    #     idx = columns.index(st10col)
    #     if row[st10col] == True:
    #         styles[idx] = 'font-weight: bold;'


    if 'ma20 SL4' in columns:
        idx = columns.index('ma20 SL4')
        if row['ma20 SL4'] == True:
            styles[idx] = 'font-weight: bold;'

    arrow = '\u2191'
    ltp_col = f'LTP {arrow}'
    if ltp_col in columns:
        idx = columns.index(ltp_col)
        if row[ltp_col] == True:
            styles[idx] = 'font-weight: bold;'

    arrow = '\u2191'
    rsi_col = f'RSI {arrow}'
    if rsi_col in columns:
        idx = columns.index(rsi_col)
        if row[rsi_col] == True:
            styles[idx] = 'font-weight: bold;'

    arrow = '\u2191'
    atp_col = f'ATR {arrow}'
    if atp_col in columns:
        idx = columns.index(atp_col)
        if row[atp_col] == True:
            styles[idx] = 'font-weight: bold;'

    arrow = '\u2191'
    cvd_col = f'CVD {arrow}'
    if cvd_col in columns:
        idx = columns.index(cvd_col)
        if row[cvd_col] == True:
            styles[idx] = 'font-weight: bold;'
    
    arrow = '\u2191'
    rsi_col = f'RSI{arrow} SML'
    if rsi_col in columns:
        idx = columns.index(rsi_col)
        if row[rsi_col] == True:
            styles[idx] = 'font-weight: bold;'
    
    arrow = '\u2191'
    ema_ma_col = f'EMA{arrow} MA'
    if ema_ma_col in columns:
        idx = columns.index(ema_ma_col)
        if row[ema_ma_col] == True:
            styles[idx] = 'font-weight: bold;'

    return styles
