import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import estrategia

# Estrutura para receber requisições de mudança de par
class ConfigUpdate(BaseModel):
    simbolo: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia a execução da estratégia em segundo plano ao ligar o servidor
    task = asyncio.create_task(estrategia.iniciar_loop())
    yield
    # Cancela a tarefa ao desligar
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Configuração de CORS: Permite que o index.html faça requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def get_status():
    """Retorna o estado atual do robô para o painel web."""
    return estrategia.obter_status()

@app.post("/toggle")
def toggle_bot():
    """Liga ou desliga o robô via interface."""
    novo_estado = estrategia.alternar_estado()
    return {"status": "sucesso", "ativo": novo_estado}

@app.post("/config")
def update_config(config: ConfigUpdate):
    """Atualiza o par de negociação ativo."""
    sucesso = estrategia.atualizar_simbolo(config.simbolo)
    return {"status": "sucesso" if sucesso else "erro", "simbolo": config.simbolo}
