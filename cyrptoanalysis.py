import requests
import sqlite3
from datetime import datetime, timezone

# Constants
API_BASE_URL = "https://api.coingecko.com/api/v3"
DB_FILE = "crypto_combined_data.db"

# Tokens to track
TOKENS = ["sui"]

# Database initialization
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create OHLC table with separate date and time columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS OHLC (
            token TEXT,
            date DATE,
            time TEXT,  -- Use TEXT for time column
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            PRIMARY KEY (token, date, time)
        )
    """)
    conn.commit()
    conn.close()

# Fetch OHLC data
def fetch_ohlc_data(token, days="7"):  # Default to 7 days
    url = f"{API_BASE_URL}/coins/{token}/ohlc"
    params = {
        "vs_currency": "usd",
        "days": days
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Failed to fetch OHLC data for {token}: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error while fetching OHLC data for {token}: {e}")
        return None

# Save OHLC data into the database
def save_ohlc_data(token, ohlc_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for entry in ohlc_data:
        # Use timezone-aware datetime objects
        timestamp = datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc)
        date = timestamp.date()
        time = timestamp.strftime("%H:%M:%S")  # Convert time to string (e.g., "14:30:00")
        open_price = entry[1]
        high_price = entry[2]
        low_price = entry[3]
        close_price = entry[4]

        cursor.execute("""
            INSERT OR IGNORE INTO OHLC (token, date, time, open, high, low, close)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (token, date, time, open_price, high_price, low_price, close_price))
    conn.commit()
    conn.close()

# Main script
def main():
    init_db()
    print("Fetching and processing OHLC data...")

    for token in TOKENS:
        print(f"Processing {token}...")

        # Fetch OHLC data for 7 days
        ohlc_data = fetch_ohlc_data(token, days="7")
        if ohlc_data:
            try:
                save_ohlc_data(token, ohlc_data)
                print(f"[SUCCESS] OHLC data saved for {token}.")
            except KeyError as e:
                print(f"[ERROR] Missing key in OHLC response for {token}: {e}")
        else:
            print(f"[ERROR] Skipping OHLC data for {token}.")
    
    print("Data fetching and saving complete.")

if __name__ == "__main__":
    main()
