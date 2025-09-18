from fyers_apiv3 import fyersModel
import json



def get_current_order_details(fyers):
    try:
        orders = fyers.orderbook({})
        positions = fyers.positions()

        latest_active_order = None
        latest_closed_order = None

        if "orderBook" in orders:
            # Sort orders by time (most recent first)
            sorted_orders = sorted(
                orders["orderBook"],
                key=lambda x: x.get("orderDateTime", ""),
                reverse=True
            )

            for order in sorted_orders:
                status_code = order.get("status")
                symbol = order.get("symbol", "UNKNOWN")
                qty = order.get("qty", 0)
                order_id = order.get("id")

                # ✅ Get P&L from positions if available
                pnl = 0
                for pos in positions.get("netPositions", []):
                    if symbol in pos.get("symbol", ""):
                        pnl = pos.get("pl", 0)
                        break

                # ✅ Check for active order (first match, most recent)
                if status_code in [2, 3, 4, 6]:
                    latest_active_order = {
                        "order_id": order_id,
                        "symbol": symbol,
                        "qty": qty,
                        "status": status_code,
                        "pnl": round(pnl, 2)
                    }
                    break  # only the most recent active one

                # # ✅ Fallback: track most recent closed/filled order
                # elif not latest_closed_order and status_code in [1, 2, 5]:  # Cancelled, Completed, Filled
                #     latest_closed_order = {
                #         "order_id": order_id,
                #         "symbol": symbol,
                #         "qty": qty,
                #         "status": status_code,
                #         "pnl": round(pnl, 2)
                #     }

        # ✅ Final result selection
        if latest_active_order:
            result = [latest_active_order]
        # elif latest_closed_order:
        #     result = [latest_closed_order]
        else:
            result = [{"message": "No orders found"}]

        total_pnl = 0
        for pos in positions.get("netPositions", []):
            total_pnl += pos.get("pl", 0)

        result.append({"total_pnl_today": round(total_pnl, 2)})
        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps([{"error": str(e)}], indent=2)
