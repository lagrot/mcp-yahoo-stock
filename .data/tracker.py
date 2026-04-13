import sqlite3
import json
import os
import yfinance as yf
from datetime import datetime

# Konfiguration
DB_PATH = '.data/ledger.db'
TICKERS = {
    "MONTLEV": "MONTLEV.ST",
    "JGPI": "JGPI.DE",      # Xetra (EUR)
    "INVE B": "INVE-B.ST",
    "FGEQ": "FGQI.L",       # London (USD)
    "4GLD": "4GLD.DE",      # Xetra (EUR)
    "XACTHDIV": "XACTHDIV.ST",
    "ABB B": "ABB.ST"
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabell för portfölj-snapshot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings_history (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            accountId TEXT,
            ticker TEXT,
            quantity REAL,
            marketValueAccount REAL
        )
    ''')
    # Ny tabell för pris-historik (15 min fördröjd)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ticker TEXT,
            price REAL,
            change_pct REAL
        )
    ''')
    conn.commit()
    conn.close()

def fetch_prices():
    """Hämtar fördröjda priser via yfinance och sparar i databasen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    results = {}
    print(f"--- Priskontroll {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    for display_name, yf_ticker in TICKERS.items():
        try:
            t = yf.Ticker(yf_ticker)
            # info['regularMarketPrice'] kan vara långsam, fast_info är snabbare för baskurs
            price = t.fast_info['last_price']
            prev_close = t.fast_info['previous_close']
            change_pct = ((price / prev_close) - 1) * 100 if prev_close else 0
            
            cursor.execute('''
                INSERT INTO price_history (ticker, price, change_pct)
                VALUES (?, ?, ?)
            ''', (display_name, price, change_pct))
            
            results[display_name] = {"price": price, "change": change_pct}
            print(f"{display_name:10}: {price:>8.2f} SEK ({change_pct:>+6.2f}%)")
            
        except Exception as e:
            print(f"Fel vid hämtning av {display_name}: {e}")
            
    conn.commit()
    conn.close()
    return results

def log_holdings(holdings_json):
    """Loggar nuvarande innehav från Montrose till databasen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        data = json.loads(holdings_json)
        # Om data är en lista (från get_holdings) eller ett enskilt objekt
        accounts = data if isinstance(data, list) else [data]
        
        for account in accounts:
            acc_id = account.get('accountId')
            for pos in account.get('positions', []):
                ticker = pos.get('ticker')
                qty = pos.get('quantity')
                val = pos.get('marketValue', {}).get('accountCurrency', 0)
                
                if ticker:
                    cursor.execute('''
                        INSERT INTO holdings_history (accountId, ticker, quantity, marketValueAccount)
                        VALUES (?, ?, ?, ?)
                    ''', (acc_id, ticker, qty, val))
        
        conn.commit()
        print("Innehav loggat i databasen.")
    except Exception as e:
        print(f"Loggningsfel: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    fetch_prices()
