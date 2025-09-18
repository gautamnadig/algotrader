from fyers_apiv3 import fyersModel
import duckdb as db
import pandas as pd
from flask import session as flask_session  # Use Flask session

import datetime
from datetime import timedelta,datetime
from datetime import date

yesterday_momentum = datetime.today() - timedelta(days=15)
yesterday_momentum = yesterday_momentum.strftime('%Y-%m-%d')
today = date.today().strftime("%Y-%m-%d")

todayweek = datetime.now().weekday()
today_day = datetime.today()
tomorrow = today_day + timedelta(days=1)
is_last_day = tomorrow.day == 1

client_id = "15YI17TORX-100"
access_token = None

def gen_AcessTok(auth_code):
    global access_token
    if access_token is None:
        secret_key = "2HJ9AD57A5"
        redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type="code",
            grant_type="authorization_code"
        )
        session.set_token(auth_code)
        access_token = session.generate_token()["access_token"]
    return access_token


def fryers_chain(auth_code):
    access_token = gen_AcessTok(auth_code)
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    data = {
        "symbol": "NSE:NIFTY50-INDEX",
        "strikecount": 30,
    }
    response = fyers.optionchain(data=data)
    return response


def selectStrike(df):
    db.sql("CREATE OR REPLACE TABLE df_ltp AS SELECT * FROM df")  # DuckDB in-memory
    dfd_ce = db.query("SELECT min(symbol) AS ce_sm FROM df_ltp WHERE ltp >= 120 AND ltp <= 170 AND option_type = 'CE'").df()
    dfd_pe = db.query("SELECT max(symbol) AS pe_sm FROM df_ltp WHERE ltp >= 120 AND ltp <= 170 AND option_type = 'PE'").df()

    ce = dfd_ce.iloc[0, 0] if not dfd_ce.empty else None
    pe = dfd_pe.iloc[0, 0] if not dfd_pe.empty else None
    # ce = "NSE:NIFTY2571025450CE"
    # pe = "NSE:NIFTY2571025550PE"
    return [ce, pe]

def fryers_hist(symb,fyers):
    # access_token = gen_AcessTok(fyers)
    # fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")

    data = {"symbol": f"{symb}", "resolution": "5", "date_format": "1",
            "range_from": yesterday_momentum, "range_to": today, "cont_flag": "1"}

    candle_data = fyers.history(data)
    
    columns_candle = ["timestamp", "open", "high", "low", "close", "volume"]
    df_candle = pd.DataFrame(candle_data["candles"],columns=columns_candle)
    df_candle['symbol'] = symb
   
    df_candle["timestamp"] = (
        pd.to_datetime(df_candle["timestamp"], unit="s", utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )    
    df_candle = df_candle.sort_values(by='timestamp', ascending=False)
    return df_candle

def fetchStrike(fyers):
    nifty_symb1 = "NSE:NIFTY50-INDEX"
    nifty = fryers_hist(nifty_symb1,fyers)
    # print(nifty.head(1))
    latest = nifty.iloc[0]
    strike  = latest['close']
    strike = round(strike/100)*100
    return strike


symbol_cache = {}

def loadSymbol(auth_code, use_flask_session=True):
    # ✅ Use flask session only when inside a web request
    # if use_flask_session:
    #     from flask import session as flask_session
    #     if 'ce_symbol' in flask_session and 'pe_symbol' in flask_session:
    #         return flask_session['ce_symbol'], flask_session['pe_symbol']

    # ✅ CLI or fallback global cache... use thsi for one session of app.py run(the strike data will persist here for one session)
    if 'ce' in symbol_cache and 'pe' in symbol_cache:
        return symbol_cache['ce'], symbol_cache['pe']

    resp = fryers_chain(auth_code)
    df_op = pd.DataFrame(resp["data"]["optionsChain"])
    columns = ["symbol", "option_type", "strike_price", "ltp", "bid", "ask", "volume"]
    df_op = df_op[columns]
    access_token = gen_AcessTok(auth_code)
    fyers = fyersModel.FyersModel(client_id="15YI17TORX-100",token=access_token, log_path="")
    strike = fetchStrike(fyers)

    if todayweek !=3 and not is_last_day:     
        ce, pe = selectStrike(df_op)
    
    elif todayweek == 3 and is_last_day:
        Ex_UnderlyingSymbol= "NSE:NIFTY"
        yy = datetime.now().strftime("%y")
        expiry_month = {1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7",7: "8", 8: "9", 9: "O", 10: "N", 11: "D", 12: "1"}[datetime.now().month]
        dd = (datetime.now() + timedelta(days=7)).strftime("%d")
        strikep = str(strike)
        opt_type_ce = "CE"
        opt_type_pe = "PE"
        ce = ''.join((Ex_UnderlyingSymbol,yy,expiry_month,dd,strikep, opt_type_ce))
        pe = ''.join((Ex_UnderlyingSymbol,yy,expiry_month,dd,strikep, opt_type_pe))
        # print(ce,pe)
        # print("block2")
    
    elif todayweek == 3 and not is_last_day:
        Ex_UnderlyingSymbol= "NSE:NIFTY"
        yy = datetime.now().strftime("%y")
        expiry_month = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",7: "8", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"}[datetime.now().month]
        dd = (datetime.now() + timedelta(days=7)).strftime("%d")
        strikep1 = str(strike)
        opt_type_ce = "CE"
        opt_type_pe = "PE"
        ce = ''.join((Ex_UnderlyingSymbol,yy,expiry_month,dd,strikep1, opt_type_ce))
        pe = ''.join((Ex_UnderlyingSymbol,yy,expiry_month,dd,strikep1, opt_type_pe))
        # print(ce,pe)
        # print("block3")
 
    else:
        ce, pe = selectStrike(df_op)
        


    # Store in global cache
    symbol_cache['ce'] = ce
    symbol_cache['pe'] = pe

    # Also store in flask session if inside Flask context
    # if use_flask_session:
    #     flask_session['ce_symbol'] = ce
    #     flask_session['pe_symbol'] = pe
    # print(ce,pe)
    return ce, pe
