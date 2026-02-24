"""
Este arquivo define os contratos de entrada/saída da API.
A ideia é centralizar modelos Pydantic para garantir validação
consistente e facilitar manutenção das rotas.
"""

from pydantic import BaseModel, Field


class SimpleInput(BaseModel):
    message: str = Field(..., description="Texto de entrada simples.")


class MessageInput(BaseModel):
    message: str = Field(..., description="Mensagem do usuário para o chatbot.")
    telefone: str | None = Field(
        default=None,
        description="Telefone do usuário para operações no ProRAF (somente números).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "cadastre um lote de 25 kg de tomate",
                "telefone": "55996852212",
            }
        }
    }


class TelefoneInput(BaseModel):
    telefone: str = Field(
        ...,
        description="Telefone para validação no ProRAF. Aceita também formato numero@s.whatsapp.net.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "telefone": "55996852212@s.whatsapp.net",
            }
        }
    }