from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "YOUR_ALPHA_VANTAGE_KEY"
# Added Gold (XAUUSD) and SP500 (SPX)
WATCHLIST = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "SPX"]

def get_asset_data(symbol):
    # Alpha Vantage uses 'from_symbol' and 'to_symbol' for FX/Gold
    # For SP500, we use the TIME_SERIES_INTRADAY function
    is_stock = symbol in ["SPX"]
    func = "TIME_SERIES_INTRADAY" if is_stock else "FX_INTRADAY"
    
    url = f"https://www.alphavantage.co/query?function={func}&symbol={symbol}&from_symbol={symbol[:3]}&to_symbol={symbol[3:]}&interval=15min&apikey={API_KEY}"
    
    try:
        r = requests.get(url).json()
        # Handle different JSON keys for FX vs Stocks
        key = "Time Series (15min)" if is_stock else "Time Series FX (15min)"
        ts = r.get(key, {})
        
        if not ts: return None

        times = sorted(ts.keys())
        latest_price = float(ts[times[-1]]["4. close"])
        
        # Find Daily Open (approximation for 00:00)
        # In a production app, you'd scan for the exact 00:00 timestamp
        daily_open = float(ts[times[0]]["1. open"]) 
        
        # Calculate Pips (10000 for FX, 100 for Gold/Indices)
        multiplier = 100 if symbol in ["XAUUSD", "SPX", "USDJPY"] else 10000
        dist = round((latest_price - daily_open) * multiplier, 1)
        
        # Logic: Probability of Return to Open
        prob = 90 if abs(dist) < 10 else 65 if abs(dist) < 40 else 25

        return {
            "symbol": symbol,
            "current": latest_price,
            "open": daily_open,
            "pips": dist,
            "prob": prob
        }
    except:
        return None

@app.route('/api/multi-stats')
def multi_stats():
    results = []
    for symbol in WATCHLIST:
        data = get_asset_data(symbol)
        if data: results.append(data)
    return jsonify(results)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
