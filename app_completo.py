import asyncio
import time
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Importa a função de estratégia que já criamos e testamos
from estrategia import analisar_sinal_e_executar

# Inicializa a API FastAPI
app = FastAPI(title="Binance Trading Bot & Control API", version="2.0.0")

# -------------------------------------------------------------
# ESTADO GLOBAL (Compartilhado entre a API e o Robô)
# -------------------------------------------------------------
estado_robo = {
    "ativo": True,
    "simbolo": "BTCUSDT",
    "quantidade": 0.001,
    "intervalo_minutos": 15,
    "ultima_analise": "Aguardando início...",
    "ultima_ordem": "Nenhuma ordem executada ainda",
    "status_sistema": "Iniciando..."
}

class ConfiguracaoRequest(BaseModel):
    ativo: bool
    simbolo: str
    quantidade: float = 0.001

# -------------------------------------------------------------
# LOOP ASSÍNCRONO DO ROBÔ (Executa 24/7 em segundo plano)
# -------------------------------------------------------------
async def loop_principal_robo():
    print("🤖 Loop do Robô iniciado com sucesso em segundo plano!")
    
    while True:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_robo["ultima_analise"] = agora

        # 1. Checa se o usuário pausou o robô pelo aplicativo
        if not estado_robo["ativo"]:
            estado_robo["status_sistema"] = "PAUSADO PELO USUÁRIO 🔴"
            print(f"[{agora}] ⏸️ Robô em pausa. Aguardando ativação pelo aplicativo...")
        else:
            estado_robo["status_sistema"] = "EXECUTANDO 🟢"
            print(f"[{agora}] 🔍 Executando análise para {estado_robo['simbolo']}...")
            
            try:
                # Executa a estratégia de análise de mercado
                analisar_sinal_e_executar(
                    simbolo=estado_robo["simbolo"],
                    quantidade=estado_robo["quantidade"]
                )
            except Exception as e:
                print(f"⚠️ Erro ao analisar mercado: {e}")

        # Aguarda o intervalo configurado (ex: 15 minutos = 900 segundos)
        intervalo_segundos = estado_robo["intervalo_minutos"] * 60
        await asyncio.sleep(intervalo_segundos)

# Evento do FastAPI que roda assim que o servidor liga
@app.on_event("startup")
async def ao_iniciar():
    # Dispara o loop do robô em background sem travar as requisições da API
    asyncio.create_task(loop_principal_robo())

# -------------------------------------------------------------
# ENDPOINTS DA API (Usados pelo Aplicativo Mobile)
# -------------------------------------------------------------

@app.get("/status")
def obter_status():
    """O aplicativo consulta este endpoint a cada X segundos para atualizar o painel."""
    return estado_robo

@app.post("/controle")
def alterar_controle(config: ConfiguracaoRequest):
    """O aplicativo chama este endpoint quando você clica nos botões do celular."""
    estado_robo["ativo"] = config.ativo
    estado_robo["simbolo"] = config.simbolo.upper()
    estado_robo["quantidade"] = config.quantidade

    acao = "ATIVADO 🟢" if config.ativo else "PAUSADO 🔴"
    print(f"\n📱 COMANDO RECEBIDO DO APP: Robô {acao} | Par: {estado_robo['simbolo']}\n")
    
    return {
        "mensagem": f"Comando executado! O robô agora está {acao}",
        "novo_estado": estado_robo
    }

# -------------------------------------------------------------
# EXECUÇÃO DO SERVIDOR
# -------------------------------------------------------------
if __name__ == "__main__":
    # Roda o servidor acessível na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)