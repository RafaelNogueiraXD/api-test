"""
Este arquivo é o ponto de entrada da API FastAPI.
A ideia geral é expor rotas HTTP simples e uma rota de conversa
que usa multiagentes de IA para estruturar dados de produto/lote agrícola.
"""

from typing import Any

from fastapi import FastAPI
from api_test.agents import AgriculturalMultiAgentService
from api_test.schemas import MessageInput, SimpleInput, TelefoneInput
from api_test.api_proraf import ProrafAPI
from api_test.settings import settings

app = FastAPI()
multi_agent_service = AgriculturalMultiAgentService()
proraf_client = ProrafAPI(
    base_url=settings.proraf_api_base_url,
    secret_key=settings.proraf_secret_key,
    api_key=settings.proraf_api_key,
)

    
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/verificaTelefone")
async def verifica_telefone(data: TelefoneInput) -> dict[str, Any]:
    telefone = data.telefone.strip()
    return proraf_client.verificar_telefone(telefone)


@app.post("/message")
async def create_message(data: SimpleInput):
    return {"message": f"You sent: {data.message}"}


@app.post("/mensagem")
@app.post("/chatbot")
async def mensagem(data: MessageInput) -> dict[str, Any] | int:
    print("Received message:", data.message)
    return multi_agent_service.process_message(data.message, data.telefone)

@app.post("/choose")
async def choose_option(data: SimpleInput):
    mensagem = data.message.lower()
    if mensagem == "produto":
        return {"message": "Você escolheu a opção Produto"}
    elif mensagem == "lote":
        return {"message": "Você escolheu a opção Lote"}
    elif mensagem == "transação":
        return {"message": "Você escolheu a opção Transação"}
    else:
        return {"message": "Opção inválida"}