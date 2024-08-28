from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import datetime
from dotenv import load_dotenv
from jugaad_trader import Zerodha
import pyotp
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
load_dotenv()
# Initialize the Zerodha object and login
def login():
    kite = Zerodha()
    # creds_str = os.getenv('user_id')
    # print(creds_str,"creds")
    # print(creds, "creds")
    kite.user_id = os.getenv('user_id')
    kite.password = os.getenv('password')
    json_res = kite.login_step1()
    twofa = pyotp.TOTP(os.getenv('totp_key')).now()
    kite.twofa = twofa
    json_res_1 = kite.login_step2(json_res)
    kite.enc_token = kite.r.cookies['enctoken']
    print(kite.enc_token)
    return kite
# Get instrument tokens for symbols in tradebook_df
def get_instrument_tokens(tradebook_df, kite):
    instruments = pd.DataFrame(kite.instruments())
    symbol_list = list(set(tradebook_df['symbol'].tolist()))
    instrument_list = {}
    for symbol in symbol_list:
        instrument_list[symbol] = instruments[instruments['tradingsymbol'] == symbol].instrument_token.values[0]
    return instrument_list

# Fetch options data for each symbol
def fetch_options_data(instrument_list,kite):
    option_data_df = pd.DataFrame()
    to_date = from_date = datetime.datetime.now().date() - datetime.timedelta(days=5)
    print(to_date, from_date)
    for symbol, instrument_token in instrument_list.items():
        df = pd.DataFrame(kite.historical_data(instrument_token, from_date, to_date, 'minute', continuous=False, oi=False))
        df['symbol'] = symbol
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['date'] = pd.to_datetime(df['date'])
        option_data_df = pd.concat([option_data_df, df], ignore_index=True)
    print(f"options data is {option_data_df}")  
    return option_data_df

# Calculate MTM
def plot_day_mtm(trade_book_df: pd.DataFrame, options_data_df: pd.DataFrame, kite):
    start_datetime = "2024-08-23 9:15:00"
    end_datetime = "2024-08-23 15:30:00"
    datetime_index = pd.date_range(start=start_datetime, end=end_datetime, freq='min')
    mtm_df = pd.DataFrame(index=datetime_index)
    mtm_df = mtm_df.reset_index()
    mtm_df = mtm_df.rename(columns={'index': 'Time'})
    mtm_df["MTM"] = 0
    minutes_count = mtm_df.shape[0]
    for trade in trade_book_df.itertuples():
        trade_price = trade[5]
        trade_time = trade[1]
        order_type = 1 if trade[2] == "BUY" else -1
        qty = int(trade[4])
        pos = order_type * qty
        symbol_options_data = options_data_df[options_data_df["symbol"] == trade[3]]
        num_empty_rows = minutes_count - symbol_options_data.shape[0]
        empty_df = pd.DataFrame(index=range(num_empty_rows), columns=symbol_options_data.columns)
        symbol_options_data = pd.concat([symbol_options_data, empty_df])
        symbol_options_data.reset_index(drop=True, inplace=True)
        mtm_df["close"] = symbol_options_data["close"]
        mtm_df.loc[mtm_df["Time"] > trade_time, "MTM"] = mtm_df["MTM"] + (mtm_df["close"] - trade_price) * pos

    mtm_df = mtm_df.dropna()
    mtm_df.drop(["close"], axis=1, inplace=True)
    mtm_df.set_index('Time', inplace=True)
    return mtm_df, min(mtm_df), max(mtm_df)

@app.route('/calculate_mtm', methods=['POST'])
def calculate_mtm():
    try:
        kite = login()
        # Receive JSON data and convert to DataFrame
        # data = request.get_json()

        file = request.files['file']

        # Read the file into a DataFrame
        trade_book_df = pd.read_csv(file)

        # Get instrument tokens for trade symbols
        instrument_list = get_instrument_tokens(trade_book_df,kite)
        # Fetch options data
        options_data_df = fetch_options_data(instrument_list,kite)

        # Process the data to calculate MTM
        mtm_df, min_mtm, max_mtm = plot_day_mtm(trade_book_df, options_data_df,kite)

        # Convert the MTM DataFrame to JSON and return as response
        mtm_json = mtm_df.to_json(orient='split', date_format='iso')
        # mtm_json['min_mtm'] = min_mtm
        # mtm_json['max_mtm'] = max_mtm

        print(mtm_json)
        return jsonify(mtm_json)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
