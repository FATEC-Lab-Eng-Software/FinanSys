# Infraestrutura e organização do FinanSys

Este guia resume a topologia local do monorepo. A descrição detalhada de camadas, fluxos e integrações está em [arquitetura.md](arquitetura.md); o passo a passo de configuração fica no [README da raiz](../README.md) e na [wiki de execução](https://github.com/FATEC-Lab-Eng-Software/FinanSys/wiki).

## Monorepo

O workspace pnpm contém duas aplicações:

- `apps/web`: Next.js 16, React 19 e TypeScript;
- `apps/server`: FastAPI, Pydantic, SQLAlchemy e Alembic.

O diretório `documentation/` reúne guias técnicos, contrato da API, modelo de dados, testes e backlog. O arquivo `docker-compose.yml` da raiz orquestra o ambiente local.

## Topologia local

```text
Navegador
  └── Next.js (localhost:3000)
       └── FastAPI (localhost:8000)
            ├── SQLAlchemy/psycopg → PostgreSQL (supabase-db:5432)
            ├── HTTP/JSON → Hermes (hermes:8642)
            └── HTTP → Kong (localhost:8080) → serviços Supabase
```

O Compose também define os serviços auxiliares do Supabase, o Studio, o Mailpit para e-mails locais e Hermes para o assistente financeiro. O PostgreSQL mantém os dados no volume `supabase-db-data`.

## Inicialização

Configure as variáveis copiando `.env.example` para `.env` e gere as chaves locais do Supabase conforme o [README](../README.md). Inicie o ambiente na raiz:

```sh
docker compose up -d --build
```

Para desenvolvimento sem subir toda a stack, use `pnpm dev:web` ou `pnpm dev:server`. A documentação interativa da API fica em `http://localhost:8000/docs`. Migrations e seed são executados separadamente; veja [modelo-de-dados.md](modelo-de-dados.md) e a wiki de execução.

## Referências técnicas

- [Arquitetura e fluxos](arquitetura.md)
- [Contrato da API](api.md)
- [Modelo de dados](modelo-de-dados.md)
- [Estratégia de testes](testes.md)
- [Guia de contribuição](contribuicao.md)
