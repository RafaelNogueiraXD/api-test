"""
Este arquivo implementa a orquestração entre IA e API ProRAF.
Fluxo principal:
1) A IA interpreta a intenção e monta o body da requisição CRUD
2) O sistema executa a operação no backend ProRAF
3) A IA transforma o resultado técnico em resposta amigável ao usuário
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from api_test.api_proraf import ProrafAPI
from api_test.prompts import (
    CRUD_PLANNER_PROMPT,
    CRUD_RESULT_MESSAGE_PROMPT,
    USER_MESSAGE_TEMPLATE,
)
from api_test.settings import settings


class AgriculturalMultiAgentService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model
        self.proraf = ProrafAPI(
            base_url=settings.proraf_api_base_url,
            secret_key=settings.proraf_secret_key,
            api_key=settings.proraf_api_key,
        )

    def _invoke_json(self, system_prompt: str, user_message: str) -> dict[str, Any] | int:
        if self.client is None:
            return 0

        user_payload = USER_MESSAGE_TEMPLATE.format(user_message=user_message)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload},
                ],
            )
        except Exception:
            return 0

        content = (response.choices[0].message.content or "").strip()
        return self._parse_agent_output(content)

    def _invoke_text(self, system_prompt: str, user_message: str) -> str:
        if self.client is None:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
        except Exception:
            return ""

        return (response.choices[0].message.content or "").strip()

    @staticmethod
    def _parse_agent_output(content: str) -> dict[str, Any] | int:
        if content == "0":
            return 0

        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return 0
        except json.JSONDecodeError:
            return 0

    def _execute_crud(self, api_method: str, request_body: dict[str, Any]) -> dict[str, Any]:
        try:
            if api_method == "verificar_telefone":
                telefone = str(request_body.get("telefone", "")).strip()
                if not telefone:
                    return {"success": False, "error": "Telefone é obrigatório para verificar telefone."}
                return self.proraf.verificar_telefone(telefone)

            if api_method == "criar_produto":
                telefone = str(request_body.get("telefone", "")).strip()
                name = str(request_body.get("name", "")).strip()
                if not telefone or not name:
                    return {"success": False, "error": "Telefone e name são obrigatórios para criar produto."}
                return self.proraf.criar_produto(
                    telefone=telefone,
                    nome=name,
                    descricao=request_body.get("description"),
                    variedade=request_body.get("variedade_cultivar"),
                )

            if api_method == "listar_produtos":
                telefone = str(request_body.get("telefone", "")).strip()
                if not telefone:
                    return {"success": False, "error": "Telefone é obrigatório para listar produtos."}
                return self.proraf.listar_produtos(telefone)

            if api_method == "atualizar_produto":
                telefone = str(request_body.get("telefone", "")).strip()
                product_id = request_body.get("product_id")
                if not telefone or product_id is None:
                    return {"success": False, "error": "Telefone e product_id são obrigatórios para atualizar produto."}
                return self.proraf.atualizar_produto(
                    telefone=telefone,
                    product_id=int(product_id),
                    description=request_body.get("description"),
                    comertial_name=request_body.get("comertial_name"),
                )

            if api_method == "criar_lote":
                telefone = str(request_body.get("telefone", "")).strip()
                product_id = request_body.get("product_id")
                talhao = str(request_body.get("talhao") or "Talhão A").strip()
                producao = request_body.get("producao")
                unidade = str(request_body.get("unidadeMedida", "")).strip()

                if product_id is None:
                    product_id = self._resolve_product_id_by_name(telefone, request_body)

                if not telefone or product_id is None or producao is None or not unidade:
                    return {
                        "success": False,
                        "error": "Telefone, produto (product_id ou name), producao e unidadeMedida são obrigatórios para criar lote.",
                    }
                return self.proraf.criar_lote(
                    telefone=telefone,
                    product_id=int(product_id),
                    talhao=talhao,
                    producao=float(producao),
                    unidadeMedida=unidade,
                    dt_plantio=request_body.get("dt_plantio"),
                    dt_colheita=request_body.get("dt_colheita"),
                )

            if api_method == "listar_telefones":
                return {"success": True, "phones": self.proraf.listar_telefones()}

            return {"success": False, "error": f"api_method inválido: {api_method}"}
        except Exception as exc:
            return {"success": False, "error": f"Erro ao executar operação: {exc}"}

    def _resolve_product_id_by_name(self, telefone: str, request_body: dict[str, Any]) -> int | None:
        if not telefone:
            return None

        raw_name = request_body.get("name") or request_body.get("product_name")
        name = str(raw_name or "").strip()
        if not name:
            return None

        products_response = self.proraf.listar_produtos(telefone)
        products = products_response.get("products", []) if isinstance(products_response, dict) else []

        target = name.casefold()
        for item in products:
            product_name = str(item.get("name", "")).strip().casefold()
            if product_name == target:
                product_id = item.get("id")
                return int(product_id) if product_id is not None else None

        created = self.proraf.criar_produto(
            telefone=telefone,
            nome=name,
            descricao=request_body.get("description"),
            variedade=request_body.get("variedade_cultivar"),
        )

        if isinstance(created, dict):
            created_id = created.get("product_id")
            if created_id is not None:
                return int(created_id)

        products_response = self.proraf.listar_produtos(telefone)
        products = products_response.get("products", []) if isinstance(products_response, dict) else []
        for item in products:
            product_name = str(item.get("name", "")).strip().casefold()
            if product_name == target:
                product_id = item.get("id")
                return int(product_id) if product_id is not None else None

        return None

    def process_message(self, user_message: str, telefone: str | None = None) -> dict[str, Any] | int:
        if self.client is None:
            return {
                "error": "OPENAI_API_KEY não configurada. Defina no arquivo .env para usar /mensagem."
            }

        if not settings.proraf_secret_key:
            return {
                "error": "SECRET_KEY do ProRAF não configurada no .env. Defina PRORAF_SECRET_KEY ou SECRET_KEY.",
            }

        planner_input = {
            "mensagem_usuario": user_message,
            "telefone_contexto": telefone,
        }
        planner_output = self._invoke_json(
            CRUD_PLANNER_PROMPT,
            json.dumps(planner_input, ensure_ascii=False),
        )
        if not isinstance(planner_output, dict):
            return 0

        operation = planner_output.get("operation", "none")
        api_method = planner_output.get("api_method")
        request_body = planner_output.get("request_body", {})
        if not isinstance(request_body, dict):
            request_body = {}

        if telefone and not request_body.get("telefone"):
            request_body["telefone"] = telefone

        if operation == "none" or not api_method or api_method == "null":
            human = self._invoke_text(
                CRUD_RESULT_MESSAGE_PROMPT,
                json.dumps(
                    {
                        "mensagem_usuario": user_message,
                        "resultado_api": {"info": "Sem operação CRUD identificada"},
                    },
                    ensure_ascii=False,
                ),
            )
            return {
                "operation": "none",
                "planner": planner_output,
                "assistant_message": human
                or "Não identifiquei uma ação de cadastro/consulta. Pode me dizer o que deseja fazer?",
            }

        api_result = self._execute_crud(str(api_method), request_body)

        human_message_payload = {
            "mensagem_usuario": user_message,
            "operation": operation,
            "request_body": request_body,
            "resultado_api": api_result,
        }
        human_message = self._invoke_text(
            CRUD_RESULT_MESSAGE_PROMPT,
            json.dumps(human_message_payload, ensure_ascii=False),
        )

        return {
            "operation": operation,
            "planner": planner_output,
            "api_result": api_result,
            "assistant_message": human_message or "Concluí a operação e já tenho o resultado da API.",
        }
