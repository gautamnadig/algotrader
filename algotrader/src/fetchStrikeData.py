'''
Created on 29-Jun-2025

@author: User
'''
'''
Created on 13-Apr-2024

@author: User
'''
from datetime import date
# from fyers_api import fyersModel
# from fyers_api import accessToken
import os
from fyers_apiv3 import fyersModel
import datetime as dt
import json
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('future.no_silent_downcasting', True)
pd.set_option('display.max_colwidth', None)
import duckdb as db
import pandas_ta as ta
from placeOrder import check_order_status,place_bo_order,get_order_state
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np
from highlight_row import highlight_supertrend
from ta.momentum import RSIIndicator
import ta
import time
from resistance import detect_pivots,find_sr_zones,extract_strong_resistance_with_original_range
from candle_logic import candle_logic5,check_entry_conditions_15min,check_entry_conditions_5min,candle_logic15
from tabulate import tabulate

client_id = "15YI17TORX-100"
today = date.today().strftime("%Y-%m-%d")
yesterday = datetime.today() - timedelta(days=15)
yesterday = yesterday.strftime('%Y-%m-%d')


def getAuthCode():
    client_id = "15YI17TORX-100"
    secret_key = "2HJ9AD57A5"
    redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
    response_type = "code"  
    state = "sample_state"
    grant_type = "authorization_code"  

    # Create a session model with the provided credentials
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type=response_type,
        grant_type=grant_type
        
    )

    # Generate the auth code using the session model
    auth_codeURL = session.generate_authcode()
    return auth_codeURL

access_token = None
def gen_AcessTok(auth_code):
    global access_token
    if access_token is None:
        secret_key = "2HJ9AD57A5"
        redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
        response_type = "code"  
        state = "sample_state"
        grant_type = "authorization_code"  

        # Create a session model with the provided credentials
        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type=response_type,
            grant_type=grant_type
            
        )

        # Generate the auth code using the session model
        auth_codeURL = session.generate_authcode()
        print(auth_codeURL)
        auth_code=auth_code
        # Set the authorization code in the session object
        session.set_token(auth_code)

        # Generate the access token using the authorization code
        access_token = session.generate_token()["access_token"]
    return access_token



def fryers_hist(symb,auth_code,tm):
    access_token = gen_AcessTok(auth_code)
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")

    data = {"symbol":f"{symb}", "resolution": f"{tm}", "date_format": "1",
            "range_from": yesterday, "range_to": today, "cont_flag": "1"}

    candle_data = fyers.history(data)
    return candle_data


def fryers_chain(auth_code):
    access_token = gen_AcessTok(auth_code)
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")

    data = {
        "symbol":"NSE:NIFTY50-INDEX",
        "strikecount":30,
        
    }
    response = fyers.optionchain(data=data)
    return response

## for ordering block
def fryersOrder(auth_code):
    access_token = gen_AcessTok(auth_code)
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    return fyers



def print_bool_fields(df):
    """
    Print all columns from the latest row (most recent candle) in key=value format.
    """
    latest_row = df.iloc[0]  # Most recent row (assuming df is sorted descending by time)
    output = " | ".join(f"{col}={latest_row[col]}" for col in df.columns)
    return output



# the logic block
def start_bot(symb,auth_code):
    try:

        #### 5 MINS CANDLE
        
        candle_data = fryers_hist(symb,auth_code,5)
        df5 = candle_logic5(candle_data,symb)

        #### 15 MINS CANDLE
        
        candle_data = fryers_hist(symb,auth_code,15)
        df15 = candle_logic15(candle_data,symb)


        ## FINAL DATAFRAME
        df_final = df15[["Time","high","low","close","LTP"]].copy()
        # df_final["condition_matched"] = None
        # df_final["Order_Placed"] = None
        df_final = df_final[["Time","high","low","close","LTP"]].rename(columns={'Time':'TIME','high':'HIGH','low':'LOW','close':'CLOSE','LTP':'LTP'})
        df_final["HIGH"] = df_final["HIGH"].astype(float).round(2)
        df_final["LOW"] = df_final["LOW"].fillna(0).round(2)
        df_final["CLOSE"] = df_final["CLOSE"].fillna(0).round(2)
        df_final["LTP"] = df_final["LTP"].fillna(0).round(2)


        fyers = fryersOrder(auth_code)
        get_order_state()
        check_order_status(fyers)
        # check condition on both timeframes
        cond_5min,trigg5 = check_entry_conditions_5min(df5)
        cond_15min,trigg15 = check_entry_conditions_15min(df15)

        triggered_condition  = None
        
        if cond_5min or cond_15min:

            if cond_5min:
                triggered_condition = trigg5
            else:
                triggered_condition = trigg15

            stop_loss = 4
            target = 15
            qty = 75
            symbol = symb
            
            order_response = place_bo_order(fyers, symbol, qty, stop_loss, target, triggered_condition)    
            time.sleep(3)
        else:
            order_response = {
                "message": "Conditions not met for placing order."
            }
            triggered_condition = "No condition matched"
         
        order_response = order_response.get("message")
        

        styled_html = df_final.style.format(precision=2)\
                            .set_table_styles(
                                [{'selector': 'td', 'props': [('white-space', 'normal'), ('word-wrap', 'break-word')]},
                                {'selector': 'th', 'props': [('white-space', 'normal'), ('word-wrap', 'break-word')]}]
                            )\
                            .to_html(index=False, table_attributes='class="table table-bordered table-hover table-sm w-100"')


        # styled_html = 's'
        # order_response = 'm'
        # triggered_condition = 's'

        return styled_html,order_response,df5,df15,triggered_condition
        
    except Exception as e:
        return "", f"Exception: {str(e)}", pd.DataFrame(),pd.DataFrame(),"No condition matched"
    