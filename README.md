# Crypto AI Prediction Dashboard

## Fitur
- Prediksi harga coin 7 hari ke depan menggunakan LSTM
- Analisis teknikal (RSI, MACD)
- Analisis sentimen (Twitter & CoinGecko)
- Dashboard UI dengan Streamlit
- Alert otomatis ke Telegram

## Cara Pakai
1. Install dependency: `pip install -r requirements.txt`
2. Jalankan: `streamlit run app.py`
3. Isi `TELEGRAM_TOKEN` dan `CHAT_ID` di `utils/telegram_alert.py`

## Catatan
Prediksi bersifat estimasi. Selalu lakukan analisa pribadi.
