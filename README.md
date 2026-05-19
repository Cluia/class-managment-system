# Smart Class Plan

Sistema web para **gerenciamento de planos de aula** com assistente pedagógico baseado em IA. A aplicação oferece CRUD completo de planos, filtros e busca na listagem, e o recurso **Smart Assist**, que sugere conteúdos complementares, tópicos relacionados e tags a partir do título, da disciplina e da ementa informados.

**Repositório:** https://github.com/Cluia/class-managment-system  
**Vídeo de apresentação:** https://github.com/Cluia/class-managment-<br>system/releases/tag/v1

**Contexto:** solução do Desafio Técnico — Sistema de Gerenciamento de Planos de Aula (VLab).

---

## Sumário

- [Visão geral da solução](#visão-geral-da-solução)
- [Atendimento aos requisitos do edital](#atendimento-aos-requisitos-do-edital)
- [Arquitetura e decisões técnicas](#arquitetura-e-decisões-técnicas)
- [Stack tecnológica](#stack-tecnológica)
- [Execução com Docker](#execução-com-docker)
- [Execução local (alternativa)](#execução-local-alternativa)
- [Integração com IA (Groq)](#integração-com-ia-groq)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [API REST](#api-rest)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Testes, lint e CI](#testes-lint-e-ci)
- [Observabilidade e DevOps](#observabilidade-e-devops)
- [Segurança](#segurança)
- [Referência de troubleshooting](#referência-de-troubleshooting)

---

## Visão geral da solução

A solução é composta por três serviços orquestrados via Docker Compose:

| Serviço   | Função |
|-----------|--------|
| `frontend` | SPA estática (HTML/CSS/JS) servida por Nginx, com proxy reverso para a API |
| `backend`  | API REST em Flask, validação Pydantic, integração Groq |
| `db`       | PostgreSQL 16 para persistência em ambiente containerizado |

O fluxo do Smart Assist: o formulário envia título, disciplina e ementa → o backend monta um prompt de “Assistente Pedagógico” → a Groq responde em JSON → o frontend preenche conteúdos, recursos e tags automaticamente.

---

## Atendimento aos requisitos do edital

### Requisitos funcionais

| Requisito | Status | Observação |
|-----------|--------|------------|
| CRUD de planos de aula | Atendido | Todos os campos exigidos; paginação na listagem |
| Smart Assist (IA) | Atendido | `POST /api/plans/recommendations`; preenchimento automático no formulário |
| Filtros (disciplina, tags, data) | Atendido | Query params em `GET /api/plans` |
| Busca por título | Atendido | Parâmetro `search` |
| Ordenação | Atendido | Por título ou data de cadastro (`sort_by`, `sort_order`) |
| Loading e tratamento de erro (IA) | Atendido | Spinner, toast e mensagens de alerta no frontend |

### Requisitos técnicos

| Requisito | Status | Observação |
|-----------|--------|------------|
| Backend Flask + validação | Atendido | Pydantic nos schemas de entrada |
| Banco relacional | Atendido | PostgreSQL (Docker); SQLite em dev local |
| Integração LLM via variável de ambiente | Atendido | `GROQ_API_KEY`; prompt com resposta JSON |
| SPA frontend | Atendido | Sem framework JS; módulos ES6 |
| Docker + um comando | Atendido | `docker compose up --build` |

### Itens diferenciais (bônus)

| Item | Status | Observação |
|------|--------|------------|
| CI (GitHub Actions) | Atendido | flake8, black, pytest em `.github/workflows/linter.yml` |
| Logs estruturados (IA) | Atendido | Ex.: `AI Request: Title="...", Discipline="...", Token Usage=..., Latency=...s` |
| Health check | Atendido | `GET /api/health` (inclui verificação do banco) |
| Containerização | Atendido | Dockerfiles + `docker-compose.yml` |

### Entrega documental

| Item do edital | Situação |
|----------------|----------|
| Repositório Git público | Disponível no link acima |
| README detalhado | Este documento |
| Vídeo de apresentação (até 5 min) | Entregue separadamente conforme orientação do edital |
| Segredos fora do versionamento | Chaves em `backend/.env` (listado no `.gitignore`); apenas `.env.example` versionado |

---

## Arquitetura e decisões técnicas

**Backend em camadas:** rotas (`routes.py`) → serviços (`services.py`) → modelos SQLAlchemy (`models.py`), com validação centralizada em `validators.py`.

**IA via Groq:** API compatível com OpenAI Chat Completions, modelo padrão `llama-3.1-8b-instant` (rápido e adequado ao volume do desafio). Respostas forçadas em JSON (`response_format: json_object`).

**Fallback configurável:** `AI_FALLBACK_TO_MOCK` permite servir sugestões de demonstração quando a API externa falha (útil em ambiente de avaliação sem chave ou sob rate limit).

**Proxy no frontend:** Nginx encaminha `/api/*` ao backend, evitando CORS e permitindo uso de caminhos relativos na SPA.

**Migração leve de schema:** `db_schema.py` detecta tabelas legadas incompatíveis e recria ou adiciona colunas ausentes na inicialização — relevante quando o volume PostgreSQL persiste entre versões do modelo.

---

## Stack tecnológica

| Camada | Tecnologias |
|--------|-------------|
| Backend | Python 3.12, Flask, SQLAlchemy, Pydantic, httpx, flask-limiter, flask-cors |
| Banco | PostgreSQL 16 (Docker), SQLite (desenvolvimento local) |
| IA | Groq — `llama-3.1-8b-instant` |
| Frontend | HTML5, CSS3, JavaScript (ES modules) |
| Infra | Docker, Docker Compose, Nginx, GitHub Actions |

---

## Execução com Docker

### Pré-requisitos

- Docker Engine e Docker Compose v2
- Arquivo `backend/.env` configurado (ver seção [Integração com IA](#integração-com-ia-groq))

### Procedimento

```bash
git clone https://github.com/Cluia/class-managment-system.git
cd class-managment-system
cp backend/.env.example backend/.env
# Inserir GROQ_API_KEY em backend/.env
docker compose up --build
```

### Endpoints de acesso

| Recurso | URL |
|---------|-----|
| Interface web | http://localhost:8080 |
| API REST | http://localhost:5000/api |
| Health check | http://localhost:5000/api/health |

### Encerramento

```bash
docker compose down          # mantém dados do Postgres
docker compose down -v       # remove volume do banco
```

---

## Execução local (alternativa)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env
# Editar .env: GROQ_API_KEY e manter DATABASE_URL=sqlite:///smart_class_plan.db
python run.py
```

API disponível em http://localhost:5000/api/health.

### Frontend

A SPA depende do proxy Nginx para rotear `/api` ao backend. Para avaliação completa da interface, recomenda-se a execução via Docker Compose. Execução isolada do `index.html` (protocolo `file://`) não atende ao fluxo integrado.

---

## Integração com IA (Groq)

1. Obter chave em https://console.groq.com/keys  
2. Configurar `backend/.env`:

```env
GROQ_API_KEY=<chave>
GROQ_MODEL=llama-3.1-8b-instant
GROQ_API_BASE=https://api.groq.com/openai/v1
AI_FALLBACK_TO_MOCK=false
```

### Modelos compatíveis

| Modelo | Perfil |
|--------|--------|
| `llama-3.1-8b-instant` | Padrão do projeto; baixa latência |
| `llama-3.3-70b-versatile` | Alternativa com maior qualidade textual |

Documentação oficial: https://console.groq.com/docs/models

Com `AI_FALLBACK_TO_MOCK=true`, falhas da API externa são substituídas por sugestões fixas, sinalizadas na interface (`fallback_mock: true` na resposta JSON).

---

## Variáveis de ambiente

Referência: `backend/.env.example`

| Variável | Descrição |
|----------|-----------|
| `FLASK_ENV` | Ambiente Flask (`development` / `production`) |
| `SECRET_KEY` | Chave secreta da aplicação |
| `DATABASE_URL` | URI do banco (sobrescrita para Postgres no Compose) |
| `GROQ_API_KEY` | Credencial da API Groq |
| `GROQ_MODEL` | Identificador do modelo |
| `GROQ_API_BASE` | URL base da API (padrão: `https://api.groq.com/openai/v1`) |
| `AI_FALLBACK_TO_MOCK` | Habilita respostas mock em falha da IA |
| `CORS_ORIGINS` | Origens permitidas pelo CORS |
| `RATELIMIT_AI` | Rate limit do endpoint de IA (ex.: `10 per minute`) |

---

## API REST

Prefixo: `/api`

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da aplicação e conectividade com o banco |
| `GET` | `/plans` | Listagem paginada com filtros e ordenação |
| `GET` | `/plans/:id` | Detalhe de um plano |
| `POST` | `/plans` | Criação |
| `PUT` / `PATCH` | `/plans/:id` | Atualização |
| `DELETE` | `/plans/:id` | Exclusão |
| `POST` | `/plans/recommendations` | Recomendações Smart Assist |
| `POST` | `/plans/generate` | Geração e persistência de plano via IA |

### Health check

```bash
curl http://localhost:5000/api/health
```

Resposta esperada (HTTP 200):

```json
{"status": "healthy", "database": "connected"}
```

Se o banco estiver indisponível: HTTP `503`, `"status": "degraded"`.

### Exemplo — recomendações de IA

```bash
curl -X POST http://localhost:5000/api/plans/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introdução ao OSPF",
    "subject": "Redes",
    "syllabus_summary": "Aula sobre roteamento dinâmico e protocolos."
  }'
```

### Parâmetros de listagem (`GET /plans`)

| Parâmetro | Função |
|-----------|--------|
| `page`, `per_page` | Paginação |
| `subject` | Filtro por disciplina (parcial) |
| `tags` | Filtro por tags |
| `scheduled_date` | Filtro por data prevista (`YYYY-MM-DD`) |
| `search` | Busca no título |
| `sort_by` | `title` ou `created_at` |
| `sort_order` | `asc` ou `desc` |

---

## Estrutura do repositório

```
smart-class-plan/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Application factory
│   │   ├── config.py
│   │   ├── routes.py
│   │   ├── services.py       # Regras de negócio e cliente Groq
│   │   ├── models.py
│   │   ├── validators.py
│   │   ├── security.py
│   │   ├── logging_config.py
│   │   └── db_schema.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── src/css/main.css
│   ├── src/js/main.js
│   ├── src/js/api.js
│   ├── nginx.conf
│   └── Dockerfile
├── .github/workflows/linter.yml
├── docker-compose.yml
└── README.md
```

---

## Testes, lint e CI

### Testes automatizados

```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
```

Cobertura atual: 26 testes (rotas, validadores, segurança, recomendações, modelos, resiliência Groq).

### Análise estática

```bash
cd backend
flake8 app/ tests/ --max-line-length=100 --extend-ignore=E501
black --check app/ tests/
```

### Pipeline CI

O workflow `.github/workflows/linter.yml` executa, em push/PR para `main` e `develop`:

- `lint-backend` — flake8 e black  
- `test-backend` — pytest com cobertura  
- `lint-frontend` — verificação de estrutura do frontend  

---

## Observabilidade e DevOps

- **Logs:** formato `[LEVEL] mensagem`; requisições à IA registram título, disciplina, tokens e latência.  
- **Health check:** `GET /api/health` com probe SQL (`SELECT 1`).  
- **Containers:** imagens slim para backend (Python) e frontend (Nginx Alpine).  
- **Orquestração:** `depends_on` com healthcheck do Postgres antes do backend.

---

## Segurança

- Chaves de API e `SECRET_KEY` exclusivamente via variáveis de ambiente (`backend/.env`).  
- `.env` incluído no `.gitignore`; repositório versiona apenas `.env.example`.  
- Headers HTTP de segurança (X-Content-Type-Options, X-Frame-Options, etc.).  
- Rate limiting nos endpoints de IA (`RATELIMIT_AI`).  
- Detalhes internos de erro ocultados em produção (`public_error_message`).  
- Validação de entrada com Pydantic (`extra="forbid"` nos schemas).

---

## Referência de troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| Backend não inicia | Postgres indisponível ou schema legado | `docker compose up --build`; ou `docker compose down -v` |
| Erro 500 ao salvar plano | Incompatibilidade de schema | Reiniciar backend (migração automática em `db_schema.py`) |
| IA em modo demonstração | Chave ausente, rate limit ou `AI_FALLBACK_TO_MOCK=true` | Verificar `GROQ_API_KEY`; reiniciar backend |
| Frontend sem dados da API | Acesso via `file://` em vez do Nginx | Usar http://localhost:8080 |
| Health check 404 | Rota incorreta | Utilizar `/api/health` |
| Porta ocupada | Conflito local | Ajustar mapeamento em `docker-compose.yml` (5000, 5432, 8080) |

Logs do backend:

```bash
docker compose logs backend
```
