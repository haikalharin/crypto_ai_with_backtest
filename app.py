import streamlit as st
import pandas as pd
from pycoingecko import CoinGeckoAPI
from utils.technical_analysis import calculate_indicators
from utils.sentiment_analysis import get_sentiment_score
from utils.predictor import predict_prices
from utils.telegram_alert import send_telegram_alert
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

cg = CoinGeckoAPI()

st.set_page_config(page_title="Crypto AI Dashboard", layout="centered")
st.title("🪙 Crypto AI Dashboard")

# === FILTER COIN POPULAR / SEMUA ===
st.subheader("🔎 Analisis Coin Individual")
filter_option = st.radio("Filter Coin", ["Popular", "All"], horizontal=True)
import streamlit as st

# ===============================
# Sidebar - Pengaturan Prediksi
# ===============================
st.sidebar.header("Pengaturan Prediksi")

# Slider periode
period = st.sidebar.slider("Periode Prediksi", min_value=1, max_value=365, value=5)

# Pilih satuan waktu
unit = st.sidebar.selectbox("Satuan Waktu", ["Jam", "Hari", "Bulan", "Tahun"])

# Tombol jalankan prediksi
run_prediction = st.sidebar.button("🔮 Jalankan Prediksi")

# Konversi periode ke forecast_steps dan time_step (disimpan dulu)
forecast_steps = None
time_step = None
if unit == "Jam":
    forecast_steps = period
    time_step = "1h"
elif unit == "Hari":
    forecast_steps = period
    time_step = "1d"
elif unit == "Bulan":
    forecast_steps = period * 30
    time_step = "1d"
elif unit == "Tahun":
    forecast_steps = period * 365
    time_step = "1d"

# Tampilkan total langkah prediksi
st.sidebar.markdown(f"**Total Langkah Prediksi:** {forecast_steps} langkah")



with st.spinner("📱 Mengambil daftar coin dari CoinGecko..."):
    if filter_option == "Popular":
        gecko_list = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=1000, page=1)
    else:
        gecko_list = cg.get_coins_list()

if filter_option == "Popular":
    symbol_to_id = {coin['symbol'].upper(): coin['id'] for coin in gecko_list}
    popular_symbols = [coin['symbol'].upper() for coin in gecko_list[:100]]
    symbols = sorted(set(popular_symbols) & set(symbol_to_id.keys()))
else:
    symbol_to_id = {coin['symbol'].upper(): coin['id'] for coin in gecko_list}
    symbols = sorted(symbol_to_id.keys())

# === ANALISIS INDIVIDUAL COIN ===
selected_symbol = st.selectbox("Pilih Coin (Symbol)", symbols)
selected_id = symbol_to_id[selected_symbol]

with st.spinner(f"🔍 Memuat data untuk {selected_symbol}..."):
    try:
        market_data = cg.get_coin_market_chart_by_id(id=selected_id, vs_currency='usd', days=60)
        prices = market_data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df['Close'] = df['price']
        df['Open'] = df['Close'].shift(1)
        df['High'] = df['Close'].rolling(window=2).max()
        df['Low'] = df['Close'].rolling(window=2).min()
        data = df[['Open', 'High', 'Low', 'Close']].dropna()

        if data.empty:
            st.error(f"⚠️ Data untuk {selected_symbol} tidak tersedia.")
        else:
            current_price = float(data['Close'].iloc[-1])

            rsi, macd, signal_line, macd_status, signal, sma_50, sma_200, fib_levels = calculate_indicators(data)
            predicted = predict_prices(df, sequence_length=20, forecast_steps=forecast_steps)
            tw_sent, cg_sent = get_sentiment_score(selected_symbol)

            st.metric("📊 Harga Saat Ini", f"${current_price:,.20f}")
            st.line_chart(predicted)

            # Tambahkan tanggal prediksi
            last_timestamp = data.index[-1]
            future_dates = pd.date_range(start=last_timestamp + pd.Timedelta(days=1), periods=forecast_steps)

            # Buat DataFrame hasil prediksi
            predicted_df = pd.DataFrame({'timestamp': future_dates, 'Predicted': predicted})
            predicted_df.set_index('timestamp', inplace=True)

            # Gabungkan harga aktual & prediksi
            combined_df = pd.concat([data[['Close']], predicted_df], axis=0)

            # Jika ingin tampilkan juga SMA
            combined_df['SMA_50'] = sma_50
            combined_df['SMA_200'] = sma_200

            # Tampilkan chart gabungan
            st.subheader("📈 Grafik Harga & Prediksi")
            st.line_chart(combined_df[['Close', 'Predicted', 'SMA_50', 'SMA_200']])

            st.subheader("🔧 Indikator Teknikal")

            # RSI
            rsi_value = rsi.iloc[-1]
            rsi_status = (
                "📉 Oversold (potensi rebound)" if rsi_value < 30 else
                "📈 Overbought (potensi koreksi)" if rsi_value > 70 else
                "⚖️ Netral"
            )
            st.write(f"**📊 RSI:** {rsi_value:.2f} – {rsi_status}")

            # MACD dan Signal Line
            macd_value = macd.iloc[-1]
            signal_line_value = signal_line.iloc[-1]
            macd_diff = macd_value - signal_line_value
            macd_status = (
                "📉 Bearish (MACD < Signal)" if macd_diff < 0 else
                "📈 Bullish (MACD > Signal)"
            )
            st.write(f"**📉 MACD:** {macd_value:.2f}")
            st.write(f"**📈 Signal Line:** {signal_line_value:.2f}")
            st.write(f"**🔄 MACD Signal:** {macd_status}")

            # Trading Signal
            signal_icon = {
                "BUY": "🟢",
                "SELL": "🔴",
                "HOLD": "🟡"
            }.get(signal, "⚪")
            st.write(f"**📈 Trading Signal:** {signal_icon} {signal}")

            # SMA
            sma_50_value = sma_50.iloc[-1]
            sma_200_value = sma_200.iloc[-1]
            sma_status = (
                "📈 Golden Cross (potensi uptrend)" if sma_50_value > sma_200_value else
                "📉 Death Cross (potensi downtrend)"
            )
            st.write(f"**📊 SMA 50:** {sma_50_value:.2f}")
            st.write(f"**📊 SMA 200:** {sma_200_value:.2f} – {sma_status}")

            # Fibonacci Levels
            st.write("📀 **Fibonacci Levels:**")
            for level, price in fib_levels.items():
                level_icon = "🔹" if level == 0.5 else "▫️"
                st.write(f"{level_icon} {level}: ${price:.2f}")

            st.subheader("📌 Kesimpulan Analisis")

            rsi_value = rsi.iloc[-1]
            macd_value = macd.iloc[-1]
            signal_value = signal_line.iloc[-1]
            sma_50_value = sma_50.iloc[-1]
            sma_200_value = sma_200.iloc[-1]
            last_price = df['Close'].iloc[-1]

            # Interpretasi RSI
            if rsi_value < 30:
                rsi_status = "📉 *Oversold* (potensi naik)"
            elif rsi_value > 70:
                rsi_status = "📈 *Overbought* (potensi turun)"
            else:
                rsi_status = "⚖️ *Netral*"

            # Interpretasi MACD
            if macd_value > signal_value:
                macd_status = "📈 *Bullish crossover* (potensi naik)(Jangka Pendek)"
            elif macd_value < signal_value:
                macd_status = "📉 *Bearish crossover* (potensi turun)(Jangka Pendek)"
            else:
                macd_status = "⚖️ *Netral*(Jangaka Pendek)"

            # Interpretasi SMA
            if sma_50_value > sma_200_value:
                sma_status = "📈 *Golden Cross* (tren naik)(Jangka Panjang)"
            elif sma_50_value < sma_200_value:
                sma_status = "📉 *Death Cross* (tren turun)(Jangka Panjang)"
            else:
                sma_status = "⚖️ *Netral*(Jangka Panjang)"

            # Harga terhadap Fibonacci
            nearest_fib_level = min(fib_levels.items(), key=lambda x: abs(x[1] - last_price))
            fib_status = f"Harga mendekati level Fib {nearest_fib_level[0]} (${nearest_fib_level[1]:.2f})"

            # KESIMPULAN UTAMA
            summary = []
           


            # MACD
            if macd_status.startswith("📈") and "Bullish" in macd_status:
                summary.append("🚀 *Potensi Naik* berdasarkan indikator MACD.")
            elif macd_status.startswith("📉") and "Bearish" in macd_status:
                summary.append("⚠️ *Potensi Turun* berdasarkan indikator MACD.")

            # SMA
            if sma_status.startswith("📈") and "Golden" in sma_status:
                summary.append("🚀 *Potensi Naik* berdasarkan indikator SMA.")
            elif sma_status.startswith("📉") and "Death" in sma_status:
                summary.append("⚠️ *Potensi Turun* berdasarkan indikator SMA.")

            # RSI
            if rsi_value < 30:
                summary.append("🟢 RSI menunjukkan aset sedang *Oversold*, potensi rebound.")
            elif rsi_value > 70:
                summary.append("🔴 RSI menunjukkan aset sedang *Overbought*, waspadai koreksi.")

            # SMA crossover mendekati
            if abs(sma_50_value - sma_200_value) < 0.01:
                summary.append("🟡 SMA 50 dan 200 sedang mendekati persilangan, sinyal belum pasti.")


            # Tampilkan hasil
            st.write(f"**RSI Status:** {rsi_status}")
            st.write(f"**MACD Status:** {macd_status}")
            st.write(f"**SMA Status:** {sma_status}")
            st.write(f"**Fibonacci Level:** {fib_status}")
            st.markdown("---")
            st.subheader("📈 Rangkuman Sinyal:")
            for line in summary:
                st.markdown(f"- {line}")


            st.subheader("💬 Sentimen Sosial")
            st.write(f"**Twitter:** {tw_sent}")
            st.write(f"**CoinGecko:** {cg_sent}")

            st.subheader("📢 Sinyal")
            if signal == "BUY":
                st.success("📈 BELI SEKARANG 🚀")
                send_telegram_alert(f"Sinyal BELI untuk {selected_symbol} pada harga ${current_price:20f}")
            elif signal == "SELL":
                st.error("📉 SAATNYA JUAL ⚠️")
            else:
                st.warning("⏳ Tunggu dulu... Belum ada sinyal beli.")

            st.caption("🗕️ Update otomatis setiap 5 menit")

    except Exception as e:
        st.error(f"Terjadi error saat memuat data dari CoinGecko: {e}")

# === ANALISIS MASSAL 1000 COIN ===
st.markdown("---")
st.subheader("📊 Analisis Otomatis Coin")

st.markdown("Tentukan jumlah coin yang ingin dianalisis (maksimum 1000):")
total = st.number_input("Jumlah coin", min_value=1, max_value=1000, value=50, step=10)

if st.button("🚀 Jalankan Analisis Coin"):
    with st.spinner("🔄 Menganalisis semua coin..."):
        buy_list = []
        sell_list = []

        log_area = st.empty()
        progress = st.progress(0)

        if filter_option == "Popular":
            symbols_to_analyze = [(symbol, symbol_to_id[symbol]) for symbol in popular_symbols if symbol in symbol_to_id][:total]
        else:
            symbols_to_analyze = list(symbol_to_id.items())[:total]

        placeholder_buy = st.empty()
        placeholder_sell = st.empty()

        placeholder_buy.markdown("### ✅ Coin Untuk Dibeli\n- (Sedang diproses...)")
        placeholder_sell.markdown("### ❌ Coin Untuk Dijual\n- (Sedang diproses...)")

        def analyze(symbol, coin_id):
            try:
                time.sleep(0.2)
                market_data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency='usd', days=5)
                prices = market_data['prices']
                df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df['Close'] = df['price']
                df['Open'] = df['Close'].shift(1)
                df['High'] = df['Close'].rolling(window=2).max()
                df['Low'] = df['Close'].rolling(window=2).min()
                data = df[['Open', 'High', 'Low', 'Close']].dropna()

                if data.empty or len(data) < 15:
                    return symbol, None

                _, _, _, _, signal, *_ = calculate_indicators(data)
                return symbol, signal
            except:
                return symbol, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(analyze, symbol, coin_id): (symbol, coin_id) for symbol, coin_id in symbols_to_analyze}
            for i, future in enumerate(as_completed(futures)):
                symbol, signal = future.result()
                if signal == "BUY":
                    buy_list.append(symbol)
                    placeholder_buy.markdown("### ✅ Coin Untuk Dibeli\n- " + "\n- ".join(buy_list))
                elif signal == "SELL":
                    sell_list.append(symbol)
                    placeholder_sell.markdown("### ❌ Coin Untuk Dijual\n- " + "\n- ".join(sell_list))
                log_area.text(f"[{i+1}/{total}] {symbol} selesai - Sinyal: {signal if signal else '❌'}")
                progress.progress((i + 1) / total)

        progress.empty()
        if not buy_list:
            placeholder_buy.markdown("### ✅ Coin Untuk Dibeli\n- Tidak ada coin")
        if not sell_list:
            placeholder_sell.markdown("### ❌ Coin Untuk Dijual\n- Tidak ada coin")

        st.success("✅ Analisis selesai!")
