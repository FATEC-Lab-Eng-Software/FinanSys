# FinanSys

Sistema web de organização e análise financeira pessoal.

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/) [![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)](https://www.typescriptlang.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](https://fastapi.tiangolo.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-4169e1?logo=postgresql)](https://www.postgresql.org/) [![Docker](https://img.shields.io/badge/Docker-development-2496ed?logo=docker)](https://www.docker.com/)

## Navegação

- [Sobre o projeto](#sobre-o-projeto)
- [Desafio](#desafio)
- [Tecnologias](#tecnologias)
- [Backlog e documentação](#backlog-e-documentação)
- [Wiki de execução](#wiki-de-execução)
- [Calendário e sprints](#calendário-e-sprints)
- [Execução local](#execução-local)
- [Estrutura](#estrutura-do-repositório)
- [Equipe](#equipe)

## Sobre o projeto

O FinanSys centraliza o acompanhamento das finanças pessoais em uma única aplicação, permitindo registrar e visualizar receitas, despesas, metas e indicadores.

## Desafio

Muitas pessoas controlam a vida financeira em anotações dispersas ou planilhas difíceis de manter. O projeto transforma esses dados em uma visão clara, com dashboard, filtros, comparações, evolução do saldo e análises assistidas por IA.

## Tecnologias

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS e Playwright.
- **Backend:** Python, FastAPI, Pydantic e SQLAlchemy.
- **Dados e autenticação:** PostgreSQL e Supabase Auth.
- **Infraestrutura:** Docker Compose, Kong e pnpm workspaces.
- **Qualidade:** ESLint, testes automatizados, Alembic e Conventional Commits.

## Backlog e documentação

O backlog do produto está versionado neste repositório e usa histórias no formato **Como..., quero..., para...**.

O backlog completo está em [backlog-produto-finansys.pdf](documentation/backlog-produto-finansys.pdf).

- [Arquitetura e infraestrutura](documentation/infraestructure.md)
- [Wiki de execução no GitHub](https://github.com/FATEC-Lab-Eng-Software/FinanSys/wiki)
- [Requisições de autenticação](rest-client/auth.rest)
- [Configuração do frontend](apps/web/README.md)

## Wiki de execução

Consulte a [wiki de execução do FinanSys no GitHub](https://github.com/FATEC-Lab-Eng-Software/FinanSys/wiki) para seguir o fluxo completo de preparação, configuração, inicialização, migrations, seed, testes, troubleshooting e encerramento do ambiente local.

## Calendário e sprints

O planejamento está organizado em ciclos incrementais. A divisão funcional é:

### Sprint 1 — Fundação do produto

Criação de conta, login, interface centralizadora das finanças, componentes e cores padrão e metas financeiras.

### Sprint 2 — Dashboard e indicadores

Com uma equipe reduzida a três pessoas, a sprint concentra o dashboard sem retirar funcionalidades: saldo, receitas, despesas, filtros por período, despesas por categoria, comparação entre receitas e despesas, evolução do saldo e maiores despesas.

### Sprint 3 — Inteligência e análises avançadas

Entrega do agente de IA e de análises avançadas para interpretar os dados financeiros e apoiar o planejamento do usuário.

## Execução local

### Pré-requisitos

Docker, Node.js, pnpm 11.9 ou compatível e Python 3.11 ou superior para executar o backend fora do container.

### Configuração

Copie `.env.example` para `.env` e configure `JWT_SECRET` com pelo menos 32 caracteres. Gere as chaves locais do Supabase:

```sh
pnpm install
pnpm supabase:keys
```

O comando grava `ANON_KEY` e `SUPABASE_SERVICE_ROLE_KEY` no `.env` raiz sem exibir os valores no terminal. Para outro arquivo:

```sh
pnpm supabase:keys -- --env-file caminho/para/.env
```

O gerador não substitui chaves existentes. Use `--force` somente após alterar o `JWT_SECRET`:

```sh
pnpm supabase:keys -- --force
```

### Subir a aplicação

```sh
docker compose up -d --build
```

Ou, pelos scripts do monorepo:

```sh
pnpm dev
pnpm dev:web
pnpm dev:server
```

### Testes e qualidade

```sh
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/server test
```

Após iniciar a stack, a documentação interativa da API fica disponível no endpoint `/docs` do serviço FastAPI.

## Estrutura do repositório

```text
FinanSys/
├── apps/server/       # API FastAPI, modelos, serviços e testes
├── apps/web/          # Aplicação Next.js e testes E2E
├── documentation/     # Documentação técnica, wiki e backlog do produto
├── docker/             # Configurações auxiliares
├── rest-client/       # Requisições HTTP
├── docker-compose.yml  # Ambiente local
└── package.json        # Scripts do monorepo
```
