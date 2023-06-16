import threading
import ccxt
import logging
import csv
import time
import os


# Configuración del registro
logging.basicConfig(filename='log.csv', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieve the value of the environment variables
api_key = os.environ.get('KRAKEN_API_KEY')
api_secret = os.environ.get('KRAKEN_API_SECRET')

# Configuración de la conexión a la API de Kraken
exchange = ccxt.kraken({'apiKey': api_key, 'secret': api_secret})


# Configuración del par de trading y la estrategia RSI
symbol = 'BTC/USDT'
rsi_length = 14
overbought_level = 70
oversold_level = 30
capital = 20  # Capital inicial en USDT
capital_fraction = 4
timeframe = '15m'

# Abrir el archivo de registro en modo append y crear un objeto csv.writer
log_file = open('log.csv', 'a', newline='')
csv_writer = csv.writer(log_file)

# Obtener los datos del par de trading
def fetch_data(symbol, timeframe=timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return ohlcv

# Cálculo del RSI
def calculate_rsi(data, length):
    close_prices = [x[4] for x in data]
    deltas = [close_prices[i] - close_prices[i-1] for i in range(1, len(close_prices))]
    positive_deltas = [delta if delta > 0 else 0 for delta in deltas]
    negative_deltas = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(positive_deltas[:length]) / length
    avg_loss = sum(negative_deltas[:length]) / length
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_current_rsi(symbol):
    data = fetch_data(symbol, limit=rsi_length+1)
    rsi = calculate_rsi(data, rsi_length)
    return rsi

# Función para realizar una operación de compra
def buy(symbol, price, amount):
    exchange.create_market_buy_order(symbol, amount)
    logging.info(f"Compra: {amount} {symbol} a {price} USDT")
    csv_writer.writerow(["Compra", symbol, price, amount])

# Función para realizar una operación de venta
def sell(symbol, price, amount):
    exchange.create_market_sell_order(symbol, amount)
    logging.info(f"Venta: {amount} {symbol} a {price} USDT")
    csv_writer.writerow(["Venta", symbol, price, amount])

# Ejecución de la estrategia
def run_strategy():
    try:
        current_rsi = get_current_rsi(symbol)
        last_price = exchange.fetch_ticker(symbol)['close']
        amount_to_trade = (capital / capital_fraction) / last_price
        if current_rsi < oversold_level:
            buy(symbol, last_price, amount_to_trade)
        elif current_rsi > overbought_level:
            sell(symbol, last_price, amount_to_trade)
    except Exception as e:
        logging.error(f"Ocurrió un error: {str(e)}")

# Función para obtener y registrar el precio de BTC/USDT cada 30 segundos
def log_btc_price():
    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['close']
            logging.info(f"Precio de {symbol}: {price} USDT")
            time.sleep(30)
        except Exception as e:
            logging.error(f"Ocurrió un error al obtener el precio de {symbol}: {str(e)}")

# Ejecutar la estrategia y el registro del precio en hilos separados
strategy_thread = threading.Thread(target=run_strategy)
price_logging_thread = threading.Thread(target=log_btc_price)

strategy_thread.start()
price_logging_thread.start()
