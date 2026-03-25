from flask import Flask, render_template, jsonify
import requests
import numpy as np
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "YOUR_ALPHA_VANTAGE_KEY"
# Major FX, Gold (XAUUSD), and SP500 (SPX)
WATCHLIST = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "SPX"]

def get_multiplier(symbol):
    if any(s in symbol for s in ["JPY", "XAU", "SPX"]):
        return 100  # 2 decimal places for pips/points
    return 10000    # 4 decimal places for standard FX

def fetch_data(symbol):
    is_stock = symbol in ["SPX"]
    func = "TIME_SERIES_INTRADAY" if is_stock else "FX_INTRADAY"
    url = f"https://www.alphavantage.co/query?function={func}&symbol={symbol}&from_symbol={symbol[:3]}&to_symbol={symbol[3:]}&interval=15min&apikey={API_KEY}"
    
    try:
        r = requests.get(url).json()
        key = "Time Series (15min)" if is_stock else "Time Series FX (15min)"
        ts = r.get(key, {})
        if not ts: return None
        
        times = sorted(ts.keys())
        current_price = float(ts[times[-1]]["4. close"])
        daily_open = float(ts[times[0]]["1. open"]) # Start of available 15m data
        
        # Calculate Pips
        mult = get_multiplier(symbol)
        pips = round((current_price - daily_open) * mult, 1)
        
        # RTO Probability Logic
        abs_pips = abs(pips)
        prob = 90 if abs_pips < 10 else 70 if abs_pips < 35 else 30
        
        return {
            "symbol": symbol,
            "current": current_price,
            "open": daily_open,
            "pips": pips,
            "prob": prob,
            "history": [float(ts[t]["4. close"]) for t in times[-10:]] # Last 10 periods
        }
    except:
        return None

@app.route('/api/full-data')
def get_full_data():
    results = []
    for s in WATCHLIST:
        data = fetch_data(s)
        if data: results.append(data)
    
    # Calculate Correlation Matrix
    matrix = {}
    for i, s1 in enumerate(results):
        matrix[s1['symbol']] = {}
        for j, s2 in enumerate(results):
            if s1['symbol'] == s2['symbol']:
                matrix[s1['symbol']][s2['symbol']] = 1.0
            else:
                # Basic correlation coefficient
                corr = np.corrcoef(s1['history'], s2['history'])[0, 1]
                matrix[s1['symbol']][s2['symbol']] = round(corr, 2)
                
    return jsonify({"assets": results, "correlation": matrix})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
