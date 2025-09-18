from flask import Flask, render_template, request, redirect,url_for,jsonify, session as flask_session
from flask_socketio import SocketIO

from authenticate.getAuthorization_topt import check_valid_fyerID
from fetchStrikeData import start_bot,fryersOrder,print_bool_fields
import pandas as pd
from fetchStrikeData import getAuthCode
from placeOrder import get_order_state
from flask import request
import threading
from datetime import datetime
import time
import sys
import os
from orderStatusCurrent import get_current_order_details
import json
from symbolLoad import loadSymbol
from datetime import datetime
import time
import threading
import webbrowser
from symbolLoad import symbol_cache
import json
from flask import Response
## logging::
import sys
import logging
from logging.handlers import TimedRotatingFileHandler


# Logger setup (place this just after imports)
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

handler = TimedRotatingFileHandler(
    "C:\\Users\\Gautam\\myproject\\myalgo\\algotrader\\bot_output.log", when="midnight", interval=1, backupCount=50
)
handler.suffix = "%Y-%m-%d"
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


####################################

app = Flask(__name__)
app.secret_key = 'supersecretkey'
session = {}
token = None 

def validate_user():
    profile_data = check_valid_fyerID()
    if profile_data.get("s") == "ok":
        session['fy_id'] = profile_data["data"]["fy_id"]
        session['username'] = profile_data["data"]["name"]
        session['access_token'] = profile_data["data"]["access_token"]
        session['appId'] = profile_data["data"]["appId"]
        print(session['appId'])
        return True
    return False

@app.context_processor
def inject_user():
    return dict(username=session.get("username"))

@app.route('/', methods=['GET', 'POST'])
def home():
    print("Home route accessed")
    if request.method == 'POST':
        if validate_user():
            return redirect(url_for('index'))
        else:
            return "Authentication Failed ❌"
    return render_template('home.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    # auth_url = getAuthCode()
    # if request.method == 'POST':
    #     session['token'] = request.form['access_token']
    #     flask_session['token'] = request.form['access_token']
    #     global token
    #     token = session['token']  
    #     session['ce_symbol'] = request.form['ce_symbol']
    #     session['pe_symbol'] = request.form['pe_symbol']
    #     # session['stop_loss'] = float(request.form['stop_loss'])
    #     # session['target'] = float(request.form['target'])
    #     threading.Thread(target=wait_until_market_opens, daemon=True).start()
    #     return render_template('result.html')  # triggers auto-refresh
    # return render_template('index.html',auth_url=auth_url)
    # username = session.get("username")
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    # username = session.get("username")
    page = request.args.get('page', 'dashboard')
    tab = request.args.get('tab', 'live' if page == 'dashboard' else None)
    
    return render_template(
        'dashboard.html',
        active_page=page,
        active_tab=tab
    )

# Orders route
@app.route('/orders')
def orders():
    if 'username' not in session:
        return redirect(url_for('home'))
    # Dummy data (replace with Fyers API data later)
    orders_data = [
        {"id": 1, "symbol": "BANKNIFTY23SEP", "qty": 25, "status": "Completed"},
        {"id": 2, "symbol": "NIFTY23SEP", "qty": 50, "status": "Pending"},
    ]
    return render_template("orders.html", 
                           username=session['username'], 
                           active_page="orders", 
                           orders=orders_data)

# Trades route
@app.route('/trades')
def trades():
    if 'username' not in session:
        return redirect(url_for('home'))
    # Dummy trade data (replace with Fyers API data later)
    trades_data = [
        {"id": 101, "symbol": "BANKNIFTY23SEP", "qty": 25, "price": 45000, "pnl": "+2500"},
        {"id": 102, "symbol": "NIFTY23SEP", "qty": 50, "price": 19700, "pnl": "-500"},
    ]
    return render_template("trades.html", 
                           username=session['username'], 
                           active_page="trades", 
                           trades=trades_data)

# Settings route
@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template("settings.html", 
                           username=session['username'], 
                           active_page="settings")

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/data')
def get_data():
    try:
        global token
        token = session.get('token')  # from flask session during login
        if not token:
            return jsonify({'error': 'Token not found in session.'})

        # ✅ Use from symbol_cache (filled by the thread after 9:15 AM)
        global ce
        global pe
        ce = session.get('ce_symbol')
        pe = session.get('pe_symbol')

        if ce == 'ce':
            if 'ce' not in symbol_cache:
                return jsonify({'error': 'CE symbol not loaded yet. Try after 9:15 AM.'})
            ce = symbol_cache['ce']
        

        # Fallback for PE only if it's literal 'pe'
        if pe == 'pe':
            if 'pe' not in symbol_cache:
                return jsonify({'error': 'PE symbol not loaded yet. Try after 9:15 AM.'})
            pe = symbol_cache['pe']
        
        print("✅ symbols used — CE:", ce, "PE:", pe)

        # Call your bot logic
        try:
            ce_table, ce_order_msg,df_ce_5,df_ce_15,condition_ce = start_bot(ce, token)
            pe_table, pe_order_msg,df_pe_5,df_pe_15,condition_pe = start_bot(pe, token)
            # log dfs
            logger.info("CE Fields - 5 min")
            logger.info(print_bool_fields(df_ce_5))
            logger.info("CE Fields - 15 min")
            logger.info(print_bool_fields(df_ce_15))
            logger.info("PE Fields - 5 min")
            logger.info(print_bool_fields(df_pe_5))
            logger.info("PE Fields - 15 min")
            logger.info(print_bool_fields(df_pe_15))

            triggered_condition = "No condition matched"
            if condition_ce and condition_ce != "No condition matched":
                triggered_condition = f"CE: {condition_ce}"
                logger.info(f"CE Triggered Condition: {triggered_condition}")
                logger.info(ce_order_msg)
            elif condition_pe and condition_pe != "No condition matched":
                triggered_condition = f"PE: {condition_pe}"
                logger.info(f"PE Triggered Condition: {triggered_condition}")
                logger.info(pe_order_msg)
            
            return jsonify({
                'ce_table': ce_table,
                'pe_table': pe_table,
                'ce_symbol': ce,
                'pe_symbol': pe,
                'ce_order_msg': ce_order_msg,
                'pe_order_msg': pe_order_msg,
                'triggered_condition': triggered_condition
            })
        except Exception as e:
            return jsonify({'error': f'start_bot failed: {str(e)}'})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/result')
def result():
    return render_template(
        'result.html',
        ce_symbol=session.get('ce_symbol', 'Call Option (CE)'),
        pe_symbol=session.get('pe_symbol', 'Put Option (PE)'),
    )


@app.route('/order-status')
def order_status():
    return jsonify(get_order_state())


def auto_shutdown():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "15:15":
            print("It's (3:15pm) end of session. Exiting Flask app.")

            os._exit(0)  # Immediately stops the process
        time.sleep(30)


@app.route('/order-status-current')
def order_status_current():
    try:
        fyers = fryersOrder(token)
        orders_json = get_current_order_details(fyers)
        orders = json.loads(orders_json)
        return render_template("order_status_current.html", orders=orders)
    
    except Exception as e:
        return f"Error: {e}", 500

# global_token must be set after login POST

# symbol_cache = {}

def wait_until_market_opens():
    global token
    while True:
        now = datetime.now().time()
        start_time = datetime.strptime("09:16", "%H:%M").time()
        end_time = datetime.strptime("23:14", "%H:%M").time()

        # Check if it's after 9:15 AND token is available
        if start_time <= now <= end_time and token:
            print("✅ It's 9:15 AM. Token is available. Loading symbols...")
            try:
                loadSymbol(token)
                print("✅ Symbols loaded successfully after 9:15 AM.")
            except Exception as e:
                print("❌ Error loading symbols:", str(e))
            break
        else:
            print("🕒 Waiting for market to open...")

        time.sleep(30)





if __name__ == '__main__':

    threading.Thread(target=auto_shutdown, daemon=True).start()
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)