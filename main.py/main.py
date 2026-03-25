from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)
API_KEY = "YOUR_KEY_HERE"

@app.route('/api/stats')
def stats():
    # Fetching real-time FX data
    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=EUR&to_symbol=USD&interval=15min&apikey={API_KEY}"
    r = requests.get(url).json()
    ts = r.get("Time Series FX (15min)", {})
    
    latest = float(ts[sorted(ts.keys())[-1]]["4. close"])
    # Finding Opens (Simplified for demo, usually you'd loop for exact 00:00, 08:00)
    d_open = float(list(ts.values())[40]["1. open"]) 
    
    dist = round((latest - d_open) * 10000, 1)
    
    # Probability Logic
    prob = 95 if abs(dist) < 10 else 75 if abs(dist) < 30 else 40

    return jsonify({
        "current": latest,
        "daily_open": d_open,
        "pips": dist,
        "prob": prob
    })

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
