import time
import pandas as pd
from binance.client import Client

API_KEY = 'SUA_API_KEY_AQUI'
API_SECRET = 'SUA_SECRET_KEY_AQUI'

client = Client(API_KEY, API_SECRET, testnet=True)
# Redireciona as chamadas para os servidores de Testnet aceitos
client.API_URL = 'https://testnet.binance.vision/api'

# Corrigir sincronização de horário
res = client.get_server_time()
client.TIMESTAMP_OFFSET = res['serverTime'] - int(time.time() * 1000)

def obter_dados_mercado(simbolo="BTCUSDT", intervalo=Client.KLINE_INTERVAL_1HOUR, limite=100):
    klines = client.get_klines(symbol=simbolo, interval=intervalo, limit=limite)
    
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume', 
                                      'close_time', 'qav', 'num_trades', 'taker_base_vol', 
                                      'taker_quote_vol', 'ignore'])
    df['close'] = df['close'].astype(float)
    
    # Calculando as Médias Móveis (SMA 9 e SMA 21)
    df['sma_9'] = df['close'].rolling(window=9).mean()
    df['sma_21'] = df['close'].rolling(window=21).mean()

    # Calculando o RSI de 14 períodos
    delta = df['close'].diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = ganho / perda
    df['rsi'] = 100 - (100 / (1 + rs))

    return df

def analisar_sinal_e_executar(simbolo="BTCUSDT", quantidade=0.001):
    print(f"\n[Analise] Verificando dados para {simbolo}...")
    df = obter_dados_mercado(simbolo, limite=100)
    
    ultimo_preco = df['close'].iloc[-1]
    sma_9_atual = df['sma_9'].iloc[-1]
    sma_21_atual = df['sma_21'].iloc[-1]
    rsi_atual = df['rsi'].iloc[-1]

    print(f"📊 Preço: US$ {ultimo_preco:,.2f} | SMA9: US$ {sma_9_atual:,.2f} | SMA21: US$ {sma_21_atual:,.2f} | RSI: {rsi_atual:.1f}")

    tendencia_alta = sma_9_atual > sma_21_atual
    rsi_favoravel = 40 <= rsi_atual <= 60

    if tendencia_alta and rsi_favoravel:
        print("🚀 SINAL DE COMPRA CONFIRMADO!")
        try:
            ordem_compra = client.order_market_buy(symbol=simbolo, quantity=quantidade, recvWindow=60000)
            preco_entrada = float(ordem_compra['fills'][0]['price']) if 'fills' in ordem_compra and ordem_compra['fills'] else ultimo_preco
            print(f"✅ Compra executada com sucesso ao preço de US$ {preco_entrada:,.2f}")

            preco_alvo = round(preco_entrada * 1.015, 2)
            preco_stop = round(preco_entrada * 0.990, 2)
            stop_limit = round(preco_stop * 0.998, 2)

            print(f"🎯 Registrando Ordem OCO -> Take Profit: US$ {preco_alvo} | Stop Loss: US$ {preco_stop}")

            client.create_oco_order(
                symbol=simbolo,
                side=Client.SIDE_SELL,
                quantity=quantidade,
                price=str(preco_alvo),
                stopPrice=str(preco_stop),
                stopLimitPrice=str(stop_limit),
                stopLimitTimeInForce=Client.TIME_IN_FORCE_GTC,
                recvWindow=60000
            )
            print("🛡️ Ordem de proteção OCO configurada na corretora com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao executar ordens: {e}")
    else:
        print("⏳ Sem sinal de entrada seguro no momento. O mercado será reanalisado no próximo ciclo.")

if __name__ == "__main__":
    analisar_sinal_e_executar("BTCUSDT", quantidade=0.001)