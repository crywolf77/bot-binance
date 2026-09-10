import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import estrategia

class ConfigUpdate(BaseModel):
    simbolo: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tenta iniciar a função assíncrona principal da estratégia
    loop_func = getattr(estrategia, 'iniciar_loop', getattr(estrategia, 'loop_principal', None))
    
    if loop_func:
        if asyncio.iscoroutinefunction(loop_func):
            task = asyncio.create_task(loop_func())
        else:
            task = asyncio.create_task(asyncio.to_thread(loop_func))
    else:
        # Fallback para caso a lógica rode via thread/função direta
        task = asyncio.create_task(asyncio.to_thread(getattr(estrategia, 'executar_estrategia', lambda: None)))
        
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def get_status():
    if hasattr(estrategia, 'obter_status'):
        return estrategia.obter_status()
    return {"status_sistema": "EXECUTANDO", "simbolo": getattr(estrategia, 'SIMBOLO', 'BTCUSDT')}

@app.post("/toggle")
def toggle_bot():
    if hasattr(estrategia, 'alternar_estado'):
        novo_estado = estrategia.alternar_estado()
        return {"status": "sucesso", "ativo": novo_estado}
    return {"status": "erro", "mensagem": "Função alternar_estado não encontrada em estrategia.py"}

@app.post("/config")
def update_config(config: ConfigUpdate):
    if hasattr(estrategia, 'atualizar_simbolo'):
        sucesso = estrategia.atualizar_simbolo(config.simbolo)
        return {"status": "sucesso" if sucesso else "erro", "simbolo": config.simbolo}
    return {"status": "erro", "mensagem": "Função atualizar_simbolo não encontrada em estrategia.py"}
