"""
Cliente HTTP para integração com os endpoints WhatsApp do backend ProRAF.
Este módulo encapsula autenticação HMAC + API Key e operações CRUD.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import requests


class ProrafAPI:
    def __init__(self, base_url: str, secret_key: str, api_key: str = "", timeout: int = 30):
        """
        Inicializa o cliente da API Proraf com autenticação HMAC-SHA256
        
        Args:
            base_url: URL base da API Proraf 
            secret_key: Chave secreta para gerar hashes HMAC (deve ser a mesma do servidor)
        """
        self.base_url = base_url.rstrip("/")
        self.secret_key = secret_key
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("headers", self._headers())
        return requests.request(method=method, url=f"{self.base_url}{endpoint}", **kwargs)

    def gerar_hash(self, telefone: str) -> str:
        """
        Gera hash HMAC-SHA256 para autenticação baseada no telefone
        
        Args:
            telefone: Número de telefone do usuário
            
        Returns:
            Hash hexadecimal para autenticação
        """
        hash_object = hmac.new(
            self.secret_key.encode('utf-8'),
            telefone.encode('utf-8'),
            hashlib.sha256
        )
        generated_hash = hash_object.hexdigest()
        print(f"[DEBUG] Hash gerado para {telefone}: {generated_hash[:20]}...")
        return generated_hash

    def listar_telefones(self):
        """Lista todos os telefones cadastrados no sistema"""
        # Hash especial para listagem de telefones
        hash_list = self.gerar_hash("PHONE_LIST")
        
        try:
            response = self._request("GET", "/whatsapp/phones", params={"hash": hash_list})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar telefones: {e}")
            return {"error": str(e), "telefones": []}
    
    def verificar_telefone(self, telefone: str):
        """
        Verifica se telefone existe e retorna dados do usuário
        
        Args:
            telefone: Número de telefone a verificar
            
        Returns:
            Dict com exists, user_id, nome, email, tipo_pessoa
        """
        hash_auth = self.gerar_hash(telefone)
        
        print(f"[DEBUG] Verificando telefone: {telefone}")
        print(f"[DEBUG] URL: {self.base_url}/whatsapp/verify-phone")
        
        try:
            response = self._request(
                "POST",
                "/whatsapp/verify-phone",
                json={
                    "telefone": telefone,
                    "hash": hash_auth
                },
                timeout=10,
            )
            print(f"[DEBUG] Status code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text[:200]}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout ao verificar telefone: {telefone}")
            return {"error": "Timeout", "exists": False}
        except requests.exceptions.ConnectionError as e:
            print(f"[ERROR] Erro de conexão ao verificar telefone: {e}")
            return {"error": str(e), "exists": False}
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Erro ao verificar telefone: {e}")
            return {"error": str(e), "exists": False}
            
    def criar_produto(self, telefone: str, nome: str, descricao=None, variedade=None):
        """
        Cria produto para usuário via WhatsApp
        
        Args:
            telefone: Número de telefone do usuário
            nome: Nome do produto
            descricao: Descrição do produto (opcional)
            variedade: Variedade/cultivar do produto (opcional)
            
        Returns:
            Dict com success, product_id, product_name, qrcode_url
        """
        hash_auth = self.gerar_hash(telefone)
        
        payload = {
            "telefone": telefone,
            "hash": hash_auth,
            "name": nome,
            "description": descricao,
            "variedade_cultivar": variedade
        }
        
        print(f"[DEBUG] Payload criar_produto: {payload}")
        print(f"[DEBUG] URL: {self.base_url}/whatsapp/create-product")
        
        try:
            response = self._request("POST", "/whatsapp/create-product", json=payload)
            
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            
            # Se o status for 4xx ou 5xx, tenta pegar JSON de erro
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"[ERROR] Resposta de erro da API: {error_data}")
                    return {
                        "error": error_data.get("detail", response.text),
                        "success": False,
                        "status_code": response.status_code
                    }
                except:
                    return {
                        "error": response.text,
                        "success": False,
                        "status_code": response.status_code
                    }
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout ao criar produto")
            return {"error": "Timeout na requisição", "success": False}
        except requests.exceptions.ConnectionError as e:
            print(f"[ERROR] Erro de conexão ao criar produto: {e}")
            return {"error": f"Erro de conexão: {str(e)}", "success": False}
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Erro ao criar produto: {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            print(f"[ERROR] Erro inesperado ao criar produto: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Erro inesperado: {str(e)}", "success": False}
    
    def listar_produtos(self, telefone: str):
        """
        Lista todos os produtos do usuário
        
        Args:
            telefone: Número de telefone do usuário
            
        Returns:
            Dict com success e lista de produtos
        """
        hash_auth = self.gerar_hash(telefone)
        
        payload = {
            "telefone": telefone,
            "hash": hash_auth
        }
        
        print(f"[DEBUG] Listando produtos para: {telefone}")
        
        try:
            response = self._request("POST", "/whatsapp/list-products", json=payload)
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"[ERROR] Erro ao listar produtos: {error_data}")
                    return {"error": error_data.get("detail", response.text), "success": False, "products": []}
                except:
                    return {"error": response.text, "success": False, "products": []}
            
            response.raise_for_status()
            data = response.json()
            print(f"[DEBUG] Produtos encontrados: {len(data.get('products', []))}")
            return data
            
        except Exception as e:
            print(f"[ERROR] Erro ao listar produtos: {e}")
            return {"error": str(e), "success": False, "products": []}
    
    def atualizar_produto(self, telefone: str, product_id: int, description=None, comertial_name=None):
        """
        Atualiza informações de um produto
        
        Args:
            telefone: Número de telefone do usuário
            product_id: ID do produto
            description: Nova descrição (opcional)
            comertial_name: Novo nome comercial (opcional)
            
        Returns:
            Dict com success e dados do produto atualizado
        """
        hash_auth = self.gerar_hash(telefone)
        
        payload = {
            "telefone": telefone,
            "hash": hash_auth,
            "product_id": product_id
        }
        
        if description:
            payload["description"] = description
        if comertial_name:
            payload["comertial_name"] = comertial_name
        
        print(f"[DEBUG] Atualizando produto {product_id}")
        
        try:
            response = self._request("PUT", "/whatsapp/update-product", json=payload)
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"[ERROR] Erro ao atualizar produto: {error_data}")
                    return {"error": error_data.get("detail", response.text), "success": False}
                except:
                    return {"error": response.text, "success": False}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar produto: {e}")
            return {"error": str(e), "success": False}
    
    def criar_lote(self, telefone: str, product_id: int, talhao: str, producao: float, 
                   unidadeMedida: str, dt_plantio=None, dt_colheita=None):
        """
        Cria um lote para um produto
        
        Args:
            telefone: Número de telefone do usuário
            product_id: ID do produto
            talhao: Nome do talhão
            producao: Quantidade produzida
            unidadeMedida: Unidade de medida (kg, unidades, toneladas, caixas)
            dt_plantio: Data de plantio YYYY-MM-DD (opcional)
            dt_colheita: Data de colheita YYYY-MM-DD (opcional)
            
        Returns:
            Dict com success, batch_id e batch_number
        """
        hash_auth = self.gerar_hash(telefone)
        
        payload = {
            "telefone": telefone,
            "hash": hash_auth,
            "product_id": product_id,
            "talhao": talhao,
            "producao": producao,
            "unidadeMedida": unidadeMedida
        }
        
        if dt_plantio:
            payload["dt_plantio"] = dt_plantio
        if dt_colheita:
            payload["dt_colheita"] = dt_colheita
        
        print(f"[DEBUG] Payload criar_lote: {payload}")
        print(f"[DEBUG] URL: {self.base_url}/whatsapp/create-batch")
        
        try:
            response = self._request("POST", "/whatsapp/create-batch", json=payload)
            
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"[ERROR] Resposta de erro da API: {error_data}")
                    return {"error": error_data.get("detail", response.text), "success": False}
                except:
                    return {"error": response.text, "success": False}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[ERROR] Erro ao criar lote: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "success": False}