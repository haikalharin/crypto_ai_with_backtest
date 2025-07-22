import pandas as pd
import ta

def calculate_indicators(data):
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    # === Technical Indicators ===
    rsi = ta.momentum.RSIIndicator(close=close).rsi()
    macd_obj = ta.trend.MACD(close=close)
    macd = macd_obj.macd()
    signal_line = macd_obj.macd_signal()

    # Moving Averages
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()

    # Fibonacci Retracement Levels (high & low from last 60 days)
    high_price = close[-60:].max()
    low_price = close[-60:].min()
    diff = high_price - low_price
    fib_levels = {
        '0.0': high_price,
        '0.236': high_price - 0.236 * diff,
        '0.382': high_price - 0.382 * diff,
        '0.5': high_price - 0.5 * diff,
        '0.618': high_price - 0.618 * diff,
        '0.786': high_price - 0.786 * diff,
        '1.0': low_price,
    }

    # === Latest Values ===
    latest_price = close.iloc[-1]
    latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else None
    latest_macd = macd.dropna().iloc[-1] if not macd.dropna().empty else None
    latest_signal = signal_line.dropna().iloc[-1] if not signal_line.dropna().empty else None

    # === MACD Status ===
    macd_signal_status = "Neutral"
    if latest_macd is not None and latest_signal is not None:
        if latest_macd > latest_signal:
            macd_signal_status = "Bullish"
        elif latest_macd < latest_signal:
            macd_signal_status = "Bearish"

    # === Determine Signal ===
    signal = "HOLD"
    sma_50_latest = sma_50.dropna().iloc[-1] if not sma_50.dropna().empty else None
    sma_200_latest = sma_200.dropna().iloc[-1] if not sma_200.dropna().empty else None

    if (
        latest_rsi is not None
        and sma_50_latest is not None
        and sma_200_latest is not None
    ):
        if (
            latest_rsi < 30
            and macd_signal_status == "Bullish"
            and latest_price <= fib_levels['0.786']
            and sma_50_latest > sma_200_latest  # Golden Cross
        ):
            signal = "BUY"
        elif (
            latest_rsi > 70
            and macd_signal_status == "Bearish"
            and latest_price >= fib_levels['0.236']
            and sma_50_latest < sma_200_latest  # Death Cross
        ):
            signal = "SELL"

    return rsi, macd, signal_line, macd_signal_status, signal, sma_50, sma_200, fib_levels
