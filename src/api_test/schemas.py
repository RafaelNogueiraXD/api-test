"""
Este arquivo define os contratos de entrada/saída da API.
A ideia é centralizar modelos Pydantic para garantir validação
consistente e facilitar manutenção das rotas.
"""

from pydantic import BaseModel
class SimpleInput(BaseModel):
    message: str
class MessageInput(BaseModel):
    message: str
    telefone: str | None = None


class TelefoneInput(BaseModel):
    telefone: str