# Smart Class Plan

Plataforma para **gerenciamento de planos de aula** com assistente pedagógico baseado em IA. O sistema permite cadastrar, filtrar, ordenar e editar planos, além de sugerir conteúdos complementares, tópicos relacionados e tags a partir do título, da disciplina e da ementa.

Desenvolvido como solução do **Desafio Técnico — Sistema de Gerenciamento de Planos de Aula** (VLab).

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Stack tecnológica](#stack-tecnológica)
- [Pré-requisitos](#pré-requisitos)
- [Como rodar com Docker (recomendado)](#como-rodar-com-docker-recomendado)
- [Como rodar sem Docker (desenvolvimento local)](#como-rodar-sem-docker-desenvolvimento-local)
- [Configuração da IA (Groq)](#configuração-da-ia-groq)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Endpoints da API](#endpoints-da-api)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Testes e qualidade de código](#testes-e-qualidade-de-código)
- [Itens bônus implementados](#itens-bônus-implementados)
- [Entrega do desafio (checklist)](#entrega-do-desafio-checklist)
- [Solução de problemas](#solução-de-problemas)

---

## Funcionalidades

### CRUD de planos de aula

- Listagem com **paginação**
- **Cadastro**, **edição** e **exclusão**
- Campos: título, objetivo, ementa/resumo, data prevista, disciplina, conteúdos, recursos de apoio e tags

### Smart Assist (IA)

- Botão **“Gerar Recomendações com IA”** no formulário
- O frontend envia título, disciplina e ementa; o backend consulta a **Groq** e retorna:
  - conteúdos complementares
  - tópicos relacionados
  - 3 tags sugeridas
- Estados de **carregamento** e **erro** tratados na interface
- Fallback para sugestões de demonstração quando a API falha (configurável)

### Organização e consulta

- Filtros por **disciplina**, **tags** e **data prevista**
- Busca por **título**
- Ordenação por **título** ou **data de cadastro** (crescente/decrescente)

---

## Stack tecnológica

| Camada    | Tecnologia                                      |
|-----------|--------------------------------------------------|
| Backend   | Python 3.12, Flask, SQLAlchemy, Pydantic, httpx |
| Banco     | PostgreSQL (Docker) / SQLite (dev local)        |
| IA        | [Groq](https://groq.com) (`llama-3.1-8b-instant`) |
| Frontend  | HTML, CSS e JavaScript (SPA)                    |
| Proxy     | Nginx (container frontend)                      |
| DevOps    | Docker, Docker Compose, GitHub Actions          |

---

## Pré-requisitos

Escolha **uma** das formas de execução:

### Opção A — Docker (mais simples)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) ou Docker Engine + Compose (Linux)
- Conta e chave de API na [Groq Console](https://console.groq.com/keys) (para o Smart Assist)

### Opção B — Desenvolvimento local

- Python 3.12+
- `pip`
- Navegador moderno
- Chave Groq (opcional; sem chave, a IA usa modo demonstração)

---

## Como rodar com Docker (recomendado)

### 1. Clone o repositório

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd smart-class-plan
```

### 2. Configure o ambiente

Copie o exemplo e preencha sua chave Groq:

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env` e defina pelo menos:

```env
GROQ_API_KEY=sua_chave_aqui
GROQ_MODEL=llama-3.1-8b-instant
AI_FALLBACK_TO_MOCK=false
```

> **Importante:** nunca commite o arquivo `.env`. Ele já está listado no `.gitignore`.

### 3. Suba toda a aplicação com um comando

Na raiz do projeto:

```bash
docker compose up --build
```

Aguarde os três serviços ficarem ativos: `db`, `backend` e `frontend`.

### 4. Acesse no navegador

| Serviço   | URL |
|-----------|-----|
| **Aplicação (frontend)** | http://localhost:8080 |
| **API (backend)**        | http://localhost:5000/api |
| **Health check**         | http://localhost:5000/api/health |

### 5. Parar os containers

```bash
docker compose down
```

Para remover também o volume do banco (dados apagados):

```bash
docker compose down -v
```

---

## Como rodar sem Docker (desenvolvimento local)

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edite .env: GROQ_API_KEY e DATABASE_URL=sqlite:///smart_class_plan.db

python run.py
```

A API ficará em http://localhost:5000/api/health.

### Frontend

O frontend usa caminhos relativos (`/api/...`) e depende do **proxy do Nginx** no Docker. Para testar localmente sem Docker:

1. Sirva a pasta `frontend` com um servidor estático (ex.: extensão Live Server no VS Code), **ou**
2. Prefira usar `docker compose up` apenas para o frontend e backend.

Para desenvolvimento ágil, use **Docker Compose** na raiz.

---

## Configuração da IA (Groq)

1. Crie uma conta em https://console.groq.com
2. Gere uma API Key em **API Keys**
3. Cole em `backend/.env`:

```env
GROQ_API_KEY=gsk_xxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant
GROQ_API_BASE=https://api.groq.com/openai/v1
```

### Modelos sugeridos

| Modelo | Uso |
|--------|-----|
| `llama-3.1-8b-instant` | Rápido, ideal para desenvolvimento e demo (**padrão**) |
| `llama-3.3-70b-versatile` | Melhor qualidade nas sugestões, um pouco mais lento |

Lista atualizada: https://console.groq.com/docs/models

### Fallback (modo demonstração)

Se a Groq estiver indisponível ou sem chave:

```env
AI_FALLBACK_TO_MOCK=true
```

O sistema preenche o formulário com sugestões fixas e informa na interface. Em produção, recomenda-se `AI_FALLBACK_TO_MOCK=false` para expor erros reais da API.

---

## Variáveis de ambiente

Arquivo de referência: `backend/.env.example`

| Variável | Descrição |
|----------|-----------|
| `FLASK_ENV` | `development` ou `production` |
| `SECRET_KEY` | Chave secreta do Flask (obrigatória em produção) |
| `DATABASE_URL` | URL do banco (Postgres no Docker; SQLite local) |
| `GROQ_API_KEY` | Chave da API Groq |
| `GROQ_MODEL` | Modelo Groq (ex.: `llama-3.1-8b-instant`) |
| `GROQ_API_BASE` | Base da API (padrão: `https://api.groq.com/openai/v1`) |
| `AI_FALLBACK_TO_MOCK` | `true` = usa mock se a IA falhar |
| `CORS_ORIGINS` | Origens permitidas (ex.: `http://localhost:8080`) |
| `RATELIMIT_AI` | Limite de requisições à IA (ex.: `10 per minute`) |

No Docker, `DATABASE_URL` do Postgres é sobrescrita pelo `docker-compose.yml` para apontar ao serviço `db`.

---

## Endpoints da API

Prefixo base: `/api`

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/plans` | Lista planos (filtros, busca, ordenação, paginação) |
| `GET` | `/plans/:id` | Detalhe de um plano |
| `POST` | `/plans` | Cria plano |
| `PUT` / `PATCH` | `/plans/:id` | Atualiza plano |
| `DELETE` | `/plans/:id` | Remove plano |
| `POST` | `/plans/recommendations` | Smart Assist — recomendações de IA |
| `POST` | `/plans/generate` | Gera e salva plano via IA |

### Exemplo — health check

```bash
curl http://localhost:5000/api/health
```

Resposta:

```json
{"status": "healthy"}
```

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

### Query params da listagem (`GET /plans`)

| Parâmetro | Descrição |
|-----------|-----------|
| `page`, `per_page` | Paginação |
| `subject` | Filtro por disciplina |
| `tags` | Filtro por tags |
| `scheduled_date` | Filtro por data prevista (`YYYY-MM-DD`) |
| `search` | Busca no título |
| `sort_by` | `title` ou `created_at` |
| `sort_order` | `asc` ou `desc` |

---

## Estrutura do projeto

```
smart-class-plan/
├── backend/
│   ├── app/
│   │   ├── __init__.py      # Factory Flask
│   │   ├── config.py        # Configurações
│   │   ├── routes.py        # Endpoints REST
│   │   ├── services.py      # Regras de negócio + Groq
│   │   ├── models.py        # Modelo ClassPlan
│   │   ├── validators.py    # Schemas Pydantic
│   │   ├── security.py      # CORS, rate limit, headers
│   │   ├── logging_config.py
│   │   └── db_schema.py       # Migração leve de schema
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

## Testes e qualidade de código

### Executar testes (backend)

```bash
cd backend
pip install -r requirements.txt
pytest
```

Com cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

### Linter e formatação

```bash
cd backend
flake8 app/ tests/ --max-line-length=100 --extend-ignore=E501
black --check app/ tests/
```

O pipeline **GitHub Actions** (`.github/workflows/linter.yml`) executa flake8, black e pytest a cada push/PR nas branches `main` e `develop`.

---

## Itens bônus implementados

Conforme o documento do desafio (seção DevOps & Observabilidade):

| Item | Implementação |
|------|----------------|
| **CI (GitHub Actions)** | Workflow com flake8, black e pytest |
| **Logs estruturados** | Logs de requisições à IA, ex.: `AI Request: Title="...", Discipline="...", Token Usage=..., Latency=...s` |
| **Health check** | `GET /api/health` |
| **Containerização** | `Dockerfile` no backend e frontend + `docker-compose.yml` |
| **Subida com um comando** | `docker compose up --build` |

---

## Entrega do desafio (checklist)

O edital solicita:

- [ ] **Repositório Git público** — publique este projeto no GitHub/GitLab e atualize a URL no README
- [x] **README detalhado** — este documento
- [ ] **Vídeo (até 5 min)** — grave apresentando:
  - principais escolhas técnicas (Flask, Groq, Docker)
  - organização do projeto
  - demonstração do CRUD, filtros e Smart Assist
  - itens bônus (CI, logs, health check, Docker)
  - dificuldades encontradas (ex.: migração de schema do banco, cota de API)
- [ ] **`.env` fora do Git** — confirme que a chave Groq não foi commitada

### Sugestão de roteiro para o vídeo

1. `docker compose up --build` e abertura em http://localhost:8080  
2. Cadastro de um plano manualmente  
3. Uso do botão **Gerar Recomendações com IA**  
4. Filtros e busca na listagem  
5. `curl` no `/api/health` e trecho dos logs no terminal  
6. Menção ao workflow no GitHub Actions  

---

## Solução de problemas

### Backend não sobe / erro de banco

- Com Docker, use `docker compose up --build` (sobe `db` + `backend`).
- Se aparecer erro de coluna inexistente, reinicie o backend (há migração automática de schema legado) ou resete o volume: `docker compose down -v`.

### “Erro interno do servidor” ao salvar

- Verifique os logs: `docker compose logs backend`
- Confirme que o Postgres está saudável: `docker compose ps`

### IA retorna modo demonstração

- Verifique `GROQ_API_KEY` em `backend/.env`
- Reinicie: `docker compose restart backend`
- Teste com `AI_FALLBACK_TO_MOCK=false` para ver erros reais da API

### Frontend não carrega a API

- Acesse **http://localhost:8080** (Nginx faz proxy de `/api` para o backend).
- Não abra `index.html` direto pelo explorador de arquivos (`file://`).

### Porta em uso

- Backend: `5000` — Postgres: `5432` — Frontend: `8080`
- Altere o mapeamento em `docker-compose.yml` se necessário.

### Health check retorna 404

- Use **`/api/health`**, não `/health`.

---

## Licença e autoria

Projeto acadêmico / desafio técnico. Ajuste a licença e os créditos conforme a orientação do laboratório.

---

**Smart Class Plan** — planejamento de aulas com apoio de IA pedagógica.
