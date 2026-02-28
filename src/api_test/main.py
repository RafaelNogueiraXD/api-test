"""
Este arquivo é o ponto de entrada da API FastAPI.
A ideia geral é expor rotas HTTP simples e uma rota de conversa
que usa multiagentes de IA para estruturar dados de produto/lote agrícola.
"""

from typing import Any

from fastapi import Body, FastAPI
from api_test.agents import AgriculturalMultiAgentService
from api_test.schemas import MessageInput, SimpleInput, TelefoneInput
from api_test.api_proraf import ProrafAPI
from api_test.settings import settings

api_tags = [
    {"name": "Health", "description": "Verificação básica de disponibilidade da API."},
    {"name": "WhatsApp", "description": "Integração de verificação de telefone com backend ProRAF."},
    {"name": "Chatbot", "description": "Rotas de conversa com IA para operações agrícolas."},
    {"name": "Utilitários", "description": "Rotas auxiliares de teste."},
]


app = FastAPI(
    title="API Test - Agentes Agrícolas",
    description=(
        "API para integração com ProRAF e chatbot de IA multiagente para operações "
        "de produto e lote agrícola."
    ),
    version="0.1.0",
    openapi_tags=api_tags,
)

multi_agent_service = AgriculturalMultiAgentService()
proraf_client = ProrafAPI(
    base_url=settings.proraf_api_base_url,
    secret_key=settings.proraf_secret_key,
    api_key=settings.proraf_api_key,
)

    
@app.get(
    "/",
    tags=["Health"],
    summary="Health check da API",
    description="Retorna uma mensagem simples indicando que a API está online.",
)
async def root():
    """Endpoint de verificação rápida de disponibilidade da API."""
    return {"message": "Hello World"}


@app.post(
    "/verificaTelefone",
    tags=["WhatsApp"],
    summary="Verifica se telefone existe no ProRAF",
    description=(
        "Recebe um telefone (também aceita formato WhatsApp `numero@s.whatsapp.net`) "
        "e consulta o backend ProRAF para validar se o usuário existe."
    ),
)
async def verifica_telefone(
    data: TelefoneInput = Body(
        ...,
        examples={
            "telefone_numerico": {
                "summary": "Telefone comum",
                "value": {"telefone": "55996852212"},
            },
            "telefone_whatsapp": {
                "summary": "Formato WhatsApp",
                "value": {"telefone": "55996852212@s.whatsapp.net"},
            },
        },
    )
) -> dict[str, Any]:
    """Normaliza o telefone e consulta existência no backend ProRAF."""
    # se a resposta vier 555596852212@s.whatsapp.net, extrai apenas o número
    if data.telefone.endswith("@s.whatsapp.net"):
        telefone1 = data.telefone.split("@")[0]
        telefone = telefone1.strip()
    else:
        telefone = data.telefone.strip()

    resultado = proraf_client.verificar_telefone(telefone)
    return {
        "telefone": telefone,
        "resultado": resultado,
    }


@app.post(
    "/message",
    tags=["Utilitários"],
    summary="Echo de mensagem",
    description="Endpoint simples para testes, devolve a mensagem recebida.",
)
async def create_message(
    data: SimpleInput = Body(
        ...,
        examples={
            "exemplo": {
                "summary": "Payload básico",
                "value": {"message": "Olá API"},
            }
        },
    )
):
    """Retorna a mensagem enviada no request."""
    return {"message": f"You sent: {data.message}"}


@app.post(
    "/mensagem",
    tags=["Chatbot"],
    summary="Conversa com IA (rota principal)",
    description=(
        "Recebe mensagem do usuário e opcionalmente telefone para execução de "
        "operações no ProRAF (produto/lote)."
    ),
)
@app.post("/chatbot", include_in_schema=False)
async def mensagem(
    data: MessageInput = Body(
        ...,
        examples={
            "cadastro_lote": {
                "summary": "Cadastro de lote",
                "value": {
                    "message": "cadastre um lote de 25 kg de tomate",
                    "telefone": "55996852212",
                },
            },
            "consulta_produtos": {
                "summary": "Consulta de produtos",
                "value": {
                    "message": "listar meus produtos",
                    "telefone": "55996852212",
                },
            },
        },
    )
) -> dict[str, Any] | int:
    """Executa o fluxo IA -> planejamento -> CRUD -> resposta natural."""
    print("Received message:", data.message)
    if data.telefone.endswith("@s.whatsapp.net"):
        telefone1 = data.telefone.split("@")[0]
        telefone = telefone1.strip()
    else:
        telefone = data.telefone.strip() 
    return multi_agent_service.process_message(data.message, telefone)