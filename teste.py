#!/usr/bin/env python3
"""
Script de teste para integração WhatsApp com ProRAF API
Demonstra como gerar hashes e fazer requisições aos endpoints WhatsApp
"""

import hmac
import hashlib
import os
import requests
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Configuração - lida do arquivo .env local
API_BASE_URL = os.getenv("API_BASE_URL", "https://proraf.cloud/api").rstrip("/")

# Usada no header X-API-Key (frontend → backend)
API_KEY = os.getenv("API_KEY", "")

# Usada para gerar o HMAC dos endpoints WhatsApp.
# DEVE ser o mesmo valor de SECRET_KEY do .env do backend (NÃO é a API_KEY).
HASH_KEY = os.getenv("SECRET_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))


def _headers() -> dict[str, str]:
    """Headers padrão para autenticação no backend."""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["x-api-key"] = API_KEY
    return headers


def _request(method: str, endpoint: str, **kwargs):
    """Wrapper para requisições HTTP com URL base, headers e timeout."""
    url = f"{API_BASE_URL}{endpoint}"
    kwargs.setdefault("headers", _headers())
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    return requests.request(method=method, url=url, **kwargs)


def gerar_hash(telefone: str) -> str:
    """
    Gera hash HMAC-SHA256 para autenticação
    
    Args:
        telefone: Número de telefone do usuário
        
    Returns:
        Hash hexadecimal para autenticação
    """
    hash_object = hmac.new(
        HASH_KEY.encode('utf-8'),
        telefone.encode('utf-8'),
        hashlib.sha256
    )
    return hash_object.hexdigest()


def listar_telefones():
    """Lista todos os telefones cadastrados no sistema"""
    print("\n" + "="*60)
    print("LISTANDO TELEFONES CADASTRADOS")
    print("="*60)
    
    # Gera hash especial para listagem
    hash_list = gerar_hash("PHONE_LIST")
    
    try:
        response = _request("GET", "/whatsapp/phones", params={"hash": hash_list})
        
        if response.status_code == 200:
            telefones = response.json()
            print(f"\n✅ {len(telefones)} telefone(s) encontrado(s):")
            for tel in telefones:
                print(f"   - {tel}")
            return telefones
        else:
            print(f"\n❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return []
    except Exception as e:
        print(f"\n❌ Erro na requisição: {e}")
        return []


def verificar_telefone(telefone: str):
    """Verifica se telefone existe e retorna dados do usuário"""
    print("\n" + "="*60)
    print(f"VERIFICANDO TELEFONE: {telefone}")
    print("="*60)
    
    hash_auth = gerar_hash(telefone)
    print(f"\nHash gerado: {hash_auth[:32]}...{hash_auth[-8:]}")
    
    try:
        response = _request(
            "POST",
            "/whatsapp/verify-phone",
            json={
                "telefone": telefone,
                "hash": hash_auth
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['exists']:
                print("\n✅ TELEFONE CADASTRADO!")
                print(f"   ID do Usuário: {data['user_id']}")
                print(f"   Nome: {data['nome']}")
                print(f"   Email: {data['email']}")
                print(f"   Tipo: {'Pessoa Física' if data['tipo_pessoa'] == 'F' else 'Pessoa Jurídica'}")
            else:
                print("\n❌ Telefone não cadastrado no sistema")
            
            return data
        else:
            print(f"\n❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ Erro na requisição: {e}")
        return None


def criar_produto(telefone: str, nome: str, descricao: Optional[str] = None, variedade: Optional[str] = None):
    """Cria produto para usuário via WhatsApp"""
    print("\n" + "="*60)
    print(f"CRIANDO PRODUTO VIA WHATSAPP")
    print("="*60)
    
    hash_auth = gerar_hash(telefone)
    
    payload = {
        "telefone": telefone,
        "hash": hash_auth,
        "name": nome,
        "description": descricao,
        "variedade_cultivar": variedade
    }
    
    print(f"\nTelefone: {telefone}")
    print(f"Produto: {nome}")
    if descricao:
        print(f"Descrição: {descricao}")
    if variedade:
        print(f"Variedade: {variedade}")
    
    try:
        response = _request("POST", "/whatsapp/create-product", json=payload)
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            if data['success']:
                print("\n✅ PRODUTO CRIADO COM SUCESSO!")
                print(f"   ID: {data['product_id']}")
                print(f"   Nome: {data['product_name']}")
                print(f"   QR Code: {data['qrcode_url']}")
            else:
                print(f"\n⚠️ {data['message']}")
                print(f"   Produto já existe - ID: {data['product_id']}")
            
            return data
        else:
            print(f"\n❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ Erro na requisição: {e}")
        return None


def menu_principal():
    """Menu interativo para testes"""
    while True:
        print("\n" + "="*60)
        print("TESTE DE INTEGRAÇÃO WHATSAPP - PRORAF API")
        print("="*60)
        print("\nOpções:")
        print("1. Listar todos os telefones cadastrados")
        print("2. Verificar se telefone existe")
        print("3. Criar produto via WhatsApp")
        print("4. Gerar hash para telefone")
        print("5. Exemplo completo (verificar + criar)")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            listar_telefones()
        
        elif opcao == "2":
            telefone = input("\nDigite o telefone (ex: 55996852212): ").strip()
            verificar_telefone(telefone)
        
        elif opcao == "3":
            telefone = input("\nDigite o telefone: ").strip()
            nome = input("Digite o nome do produto: ").strip()
            descricao = input("Digite a descrição (ou Enter para pular): ").strip() or None
            variedade = input("Digite a variedade (ou Enter para pular): ").strip() or None
            criar_produto(telefone, nome, descricao, variedade)
        
        elif opcao == "4":
            telefone = input("\nDigite o telefone: ").strip()
            hash_gerado = gerar_hash(telefone)
            print(f"\n📱 Telefone: {telefone}")
            print(f"🔐 Hash: {hash_gerado}")
            print("\nCopie este hash para usar nas requisições da API WhatsApp")
        
        elif opcao == "5":
            print("\n" + "="*60)
            print("EXEMPLO COMPLETO: VERIFICAR E CRIAR PRODUTO")
            print("="*60)
            
            telefone = input("\nDigite o telefone: ").strip()
            
            # Passo 1: Verificar telefone
            print("\n>>> PASSO 1: Verificando telefone...")
            usuario = verificar_telefone(telefone)
            
            if usuario and usuario['exists']:
                # Passo 2: Criar produto
                print("\n>>> PASSO 2: Criando produto...")
                nome = input("\nDigite o nome do produto: ").strip()
                descricao = input("Digite a descrição (opcional): ").strip() or None
                criar_produto(telefone, nome, descricao)
            else:
                print("\n⚠️ Usuário não cadastrado. Não é possível criar produto.")
        
        elif opcao == "0":
            print("\n👋 Encerrando...")
            break
        
        else:
            print("\n❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    print("\n🚀 Script de Teste - Integração WhatsApp ProRAF")
    print(f"📡 API Base URL: {API_BASE_URL}")
    if API_KEY:
        print(f"🔑 API_KEY   : {API_KEY[:8]}...{API_KEY[-8:]}")
    else:
        print("⚠️  API_KEY não configurada. Defina no .env (header X-API-Key).")

    if HASH_KEY:
        print(f"🔐 SECRET_KEY: {HASH_KEY[:8]}...{HASH_KEY[-8:]}")
    else:
        print("❌ SECRET_KEY não configurada. Defina no .env — sem ela o hash será inválido e todas as chamadas retornarão 401.")
        exit(1)
    
    try:
        # Testa conexão com API
        response = _request("GET", "/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está online e acessível")
        else:
            print("⚠️ API respondeu mas com status inesperado")
    except Exception as e:
        print(f"❌ Não foi possível conectar à API: {e}")
        print("\nCertifique-se de que a API está rodando em https://proraf.cloud/api")
        exit(1)
    
    menu_principal()
