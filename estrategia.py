import asyncio
import os
from datetime import datetime
from binance.client import Client

# Variáveis Globais de Estado
BOT_ATIVO = True
SIMBOLO = "BTCUSDT"
ULTIMA_ANALISE = "Aguardando..."
ULTIMA_ORDEM = "Nenhuma ordem executada ainda"
SALDO_USDT = "0.00"

# Inicialização do Cliente Binance
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

client = None
if API_KEY and API_SECRET:
    try:
        client = Client(API_KEY, API_SECRET)
    except Exception as e:
        print(f"Erro ao inicializar cliente Binance: {e}")

def obter_saldo():
    global SALDO_USDT
    if client:
        try:
            balance = client.get_asset_balance(asset='USDT')
            if balance and 'free' in balance:
                SALDO_USDT = f"${float(balance['free']):,.2f}"
        except Exception as e:
            print(f"Erro ao buscar saldo: {e}")
            SALDO_USDT = "Erro API"
    else:
        SALDO_USDT = "Chaves não configuradas"
    return SALDO_USDT

def alternar_estado():
    global BOT_ATIVO
    BOT_ATIVO = not BOT_ATIVO
    return BOT_ATIVO

def atualizar_simbolo(novo_simbolo: str):
    global SIMBOLO
    SIMBOLO = novo_simbolo
    return True

def obter_status():
    saldo = obter_saldo()
    return {
        "ativo": BOT_ATIVO,
        "simbolo": SIMBOLO,
        "status_sistema": "EXECUTANDO" if BOT_ATIVO else "PAUSADO",
        "ultima_analise": ULTIMA_ANALISE,
        "ultima_ordem": ULTIMA_ORDEM,
        "saldo_usdt": saldo
    }

async def iniciar_loop():
    global ULTIMA_ANALISE
    while True:
        if BOT_ATIVO:
            ULTIMA_ANALISE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ULTIMA_ANALISE}] Analisando par {SIMBOLO}...")
            # Lógica de análise de indicadores e envio de ordens aqui...
        else:
            ULTIMA_ANALISE = "Pausado"
            
        await asyncio.sleep(10)
