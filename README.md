# API Test

## Instalação

```bash
poetry install
```

## Configuração de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4.1-mini
```

> Se `OPENAI_MODEL` não for informado, o padrão já é `gpt-4.1-mini`.

## Rodar servidor com Taskipy

### Desenvolvimento (com reload)

```bash
poetry run task server
```

### Produção (sem reload)

```bash
poetry run task server-prod
```

## Rodar com Docker

### Subir container

```bash
docker compose up -d --build
```

### Ver logs

```bash
docker compose logs -f
```

### Parar container

```bash
docker compose down
```

Também via Taskipy:

```bash
poetry run task docker-build
poetry run task docker-up
poetry run task docker-down
```

## Multiagentes IA

Foram implementados dois agentes simples:
- Agente de `produto` agrícola
- Agente de `lote`

A rota de conversa é:

- `POST /mensagem`

Payload:

```json
{
	"message": "cadastrar lote de laranja com 50 unidades plantado no talhão C3"
}
```
