import requests
import pandas as pd

def get_coin_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        coins = response.json()
        return {coin['name']: coin['id'] for coin in coins}
    return {}

def get_coin_market_data(coin_id, days=60, interval="daily"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": interval
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df['Open'] = df['price']
        df['High'] = df['price']
        df['Low'] = df['price']
        df['Close'] = df['price']
        df['Volume'] = 0
        return df[["Open", "High", "Low", "Close", "Volume"]]
    return pd.DataFrame()
