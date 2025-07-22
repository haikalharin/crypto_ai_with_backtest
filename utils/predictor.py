import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def predict_prices(df, forecast_steps, sequence_length=20):
    # Ambil hanya harga penutupan
    close_prices = df['Close'].values.reshape(-1, 1)

    # Scaling data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(close_prices)

    # Persiapkan dataset untuk LSTM
    X, y = [], []
    for i in range(sequence_length, len(scaled)):
        X.append(scaled[i-sequence_length:i, 0])
        y.append(scaled[i, 0])

    if not X:
        raise ValueError("Gagal membuat dataset X untuk model prediksi.")

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # Buat model LSTM
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')

    # Training model
    model.fit(X, y, epochs=5, batch_size=16, verbose=0)

    # Prediksi ke depan sebanyak forecast_steps
    predicted = []
    last_sequence = scaled[-sequence_length:]
    for _ in range(forecast_steps):
        seq_input = np.reshape(last_sequence, (1, sequence_length, 1))
        pred = model.predict(seq_input, verbose=0)[0][0]
        predicted.append(pred)
        last_sequence = np.append(last_sequence[1:], [[pred]], axis=0)

    # Kembalikan ke skala harga asli
    predicted_prices = scaler.inverse_transform(np.array(predicted).reshape(-1, 1)).flatten()
    return predicted_prices
