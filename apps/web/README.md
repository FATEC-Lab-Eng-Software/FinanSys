# Aplicação web do FinanSys

Frontend do FinanSys desenvolvido com Next.js 16, React 19 e TypeScript. O projeto faz parte do monorepo pnpm e consome a API FastAPI definida em `apps/server`.

## Requisitos

- Node.js compatível com o Next.js 16;
- pnpm 11.9 ou compatível;
- API FinanSys disponível em `http://localhost:8000`, localmente ou via Docker Compose.

## Instalação e execução

Na raiz do repositório:

```sh
pnpm install
pnpm dev:web
```

A aplicação fica disponível em `http://localhost:3000`. Para subir web, API, banco e serviços auxiliares juntos, use `docker compose up -d --build` na raiz.

## Configuração

O cliente usa `NEXT_PUBLIC_API_BASE_URL` como endereço da API e assume `http://localhost:8000` quando a variável não está definida. As requisições de autenticação incluem credenciais do navegador para transportar os cookies de sessão. Configure as origens permitidas e os atributos dos cookies no backend para o ambiente utilizado.

## Estrutura

- `src/app/(auth)`: páginas de login, cadastro e recuperação de senha;
- `src/app/(system)`: dashboard, gastos, metas, análises e assistente;
- `src/components`: componentes compartilhados e de interface;
- `src/services`: clientes de autenticação, assistente, transações e metas;
- `src/tests`: testes de interface executados pelo Playwright.

Os grupos entre parênteses organizam layouts e proteção de rotas sem aparecer no caminho da URL. A página inicial redireciona para `/dashboard`; as rotas de sistema sem sessão são direcionadas para `/login`.

## Qualidade

```sh
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web test:ui
```

Os testes usam Playwright. O runner inicia o Next em `127.0.0.1:3100` conforme `playwright.config.ts`; pode ser necessário instalar o Chromium com `pnpm --dir apps/web exec playwright install chromium`.

Consulte [a documentação de testes do monorepo](../../documentation/testes.md) para detalhes de configuração e cobertura.
