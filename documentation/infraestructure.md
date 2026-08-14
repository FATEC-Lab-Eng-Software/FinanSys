# 🏗️ Arquitetura e Infraestrutura do FinanSys

Este documento descreve a topologia atualizada da infraestrutura, as ferramentas utilizadas e a arquitetura de pastas do monorepo **FinanSys**. O projeto utiliza uma abordagem modular e altamente escalável.

---

## 🗺️ Visão Geral do Monorepo

O repositório é gerenciado via **pnpm workspaces** (`pnpm-workspace.yaml`), permitindo a orquestração e execução simultânea de múltiplos microsserviços e frontends em um único repositório.

```text
FinanSys/
├── apps/                 # Código-fonte das aplicações
│   ├── server/           # Backend (FastAPI, Python)
│   └── web/              # Frontend (Next.js, TypeScript)
├── documentation/        # Documentações gerais do projeto
├── infraestrutura/       # Orquestração do ambiente Docker (Supabase, Banco de Dados)
├── package.json          # Scripts globais do monorepo
└── pnpm-workspace.yaml   # Configuração do workspace do pnpm
```

## 🐳 Infraestrutura e DevOps (`infraestrutura/`)

Todo o ambiente de banco de dados e serviços auxiliares foi isolado nesta pasta para não poluir a raiz do projeto.

- **`docker-compose.yml`**: Arquivo de orquestração responsável por levantar o ecossistema local (PostgreSQL via Supabase, serviços de Autenticação, Storage, Studio e Mailpit).
- **`.env.example`**: Variáveis de ambiente padrão necessárias para o funcionamento seguro dos containers Docker.

## ⚙️ Backend Architecture (`apps/server/`)

O backend foi construído em **Python com FastAPI** e adota uma arquitetura limpa dividida em camadas lógicas. Essa estrutura garante que regras de negócio, validações HTTP e acesso ao banco de dados não se misturem.

### Árvore de Diretórios

```text
apps/server/
├── src/
│   ├── core/             # ⚙️ Configurações (ex: database.py, config.py)
│   ├── models/           # 🗄️ Entidades do Banco de Dados (ORM)
│   ├── schemas/          # 🛡️ Contratos de API (Pydantic) 
│   ├── repositories/     # 🔍 Consultas e Persistência no Banco 
│   ├── services/         # 💼 Regras de Negócio e Lógica 
│   └── routers/          # 🌐 Endpoints e Controladores HTTP 
├── main.py               # 🚀 Arquivo principal que inicializa o servidor FastAPI
├── requirements.txt      # 📦 Dependências do Python
└── .env.example          # 🔑 Variáveis de ambiente do servidor
```

### O Fluxo de uma Requisição (Camada por Camada)

1. **Routers**: Recebem a requisição HTTP (ex: `POST /users`), injetam as dependências e repassam os dados.
2. **Schemas**: O Pydantic valida automaticamente o corpo da requisição e garante o formato correto dos dados de entrada e saída.
3. **Services**: Executam a inteligência da aplicação. Verificam se o e-mail já existe, fazem o hash da senha e preparam os dados.
4. **Repositories**: Isolam a linguagem SQL/SQLAlchemy. Recebem o comando do serviço para salvar no banco.
5. **Models**: Representam a estrutura física da tabela no PostgreSQL.

## 🎨 Frontend Architecture (`apps/web/`)

O frontend é desenvolvido com **Next.js (App Router)** e **TypeScript**, estruturado para componentização, separação de layouts e integração otimizada com a API.

### Árvore de Diretórios

```text
apps/web/
├── src/
│   ├── app/                  # 🛣️ Rotas da Aplicação (App Router)
│   │   ├── (auth)/           # Grupo de rotas públicas (Login, Register)
│   │   └── (dashboard)/      # Grupo de rotas protegidas (Painel, Transações)
│   ├── components/           # 🧩 Componentes Reutilizáveis
│   │   ├── layout/           # Componentes de estrutura (Sidebars, Headers)
│   │   └── ui/               # Componentes visuais primários (Botões, Inputs)
│   ├── hooks/                # 🎣 Funções React customizadas (Custom Hooks)
│   ├── services/             # 🔌 Clientes e chamadas à API do backend
│   ├── store/                # 📦 Gerenciamento de estado global
│   ├── style/                # 💅 Estilizações globais ou tokens CSS
│   ├── types/                # 🏷️ Definições de interfaces e tipos globais (TypeScript)
│   └── utils/                # 🧰 Funções utilitárias puras e formatadores
├── public/                   # 🖼️ Arquivos estáticos e mídias
├── next.config.ts            # ⚙️ Configurações do compilador Next.js
└── package.json              # 📦 Dependências do frontend
```

### Destaques do Frontend

- **Isolamento Visual** **`(Route Groups)`**: Pastas como `(auth)` não adicionam segmentos à URL, permitindo compartilhar layouts (como uma barra lateral) em várias páginas logadas, sem poluir as telas de login.
- **Ecossistema Moderno**: Integrado com ferramentas rigorosas de qualidade de código (`eslint.config.mjs`) e processadores de estilo (`postcss.config.mjs`).