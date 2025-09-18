from fyers_apiv3 import fyersModel
from datetime import date
client_id = "15YI17TORX-100"
# today = date.today().strftime("%Y-%m-%d")
from datetime import datetime, timedelta
from take_order_screenshot import take_screenshot
today = datetime.now().weekday()


# Global state
order_state = {
    "active": False,
    "count": 0,
    "last_order_id": None,
    "last_trade_time": datetime.combine(datetime.today(), datetime.strptime("09:00", "%H:%M").time()),
    "condition":[]
}

def place_bo_order(fyers, symbol, qty, stop_loss, target, triggered_condition):
    """
    Places a Bracket Order (BO) if no other active order and count < 2.
    """
    start_time = datetime.strptime("09:25", "%H:%M").time()
    end_time = datetime.strptime("15:00", "%H:%M").time()
    now = datetime.now().time()
    if not (start_time <= now < end_time):
        # print("No more trades after 3:00 PM.")
        return {"status": "closed", "message": " No trades allowed before 9.25 am or after 3:00 PM."}
    
    
    # Don't place trade if 15 minutes haven't passed since last trade    
    now = datetime.now()
    if now < order_state["last_trade_time"] + timedelta(minutes=30):
        wait_minutes = (order_state["last_trade_time"] + timedelta(minutes=30) - now).seconds // 60
        return {
            "status": "cooldown",
            "message": f"Please wait {wait_minutes} more minute(s) before placing the next trade."
        }
    
    if order_state["active"]:
        # print("Order already active. Skipping.")
        return {"status": "active", "message": "Order already running."}
    
    max_orders = 2 if today == 3 else 2
    if order_state["count"] >= max_orders:
        return {"status": "limit", "message": f"Max {max_orders} orders reached for today."}

    payload = {
        "symbol": symbol,
        "qty": qty,
        "type": 2,               
        "side": 1,               
        "productType": "BO",
        "stopLoss": stop_loss,
        "takeProfit": target,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False
    }

    try:
        
        response = fyers.place_order(payload)
        order_state["active"] = True
        order_state["count"] += 1
        order_state["last_order_id"] = response.get("id")
        order_state["last_trade_time"] = now
        order_state["condition"].append(triggered_condition)

        return response
    except Exception as e:
        print("Order Error:", e)
        return {"status": "error", "message": str(e)}

def check_order_status(fyers):
    if not order_state["last_order_id"]:
        return {"status": "idle", "message": "No order placed yet."}
    
    orders = fyers.orderbook({})
    if "orderBook" in orders:
        
        sorted_orders = sorted(
                    orders["orderBook"],
                    key=lambda x: x.get("orderDateTime", ""),
                    reverse=True
                )
        for order in sorted_orders:
            if  order.get("status") ==2:
                order_state["active"] = False
                break  

        return {"status": "not_found", "message": "Order not found in orderbook"}
        # return order


def get_order_state():
    """Returns the current order state."""
    return order_state
