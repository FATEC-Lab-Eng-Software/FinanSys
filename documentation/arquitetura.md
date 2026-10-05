# Arquitetura do FinanSys

Este documento descreve a arquitetura implementada atualmente no repositório. Ele é voltado para desenvolvimento (DEV) e deve ser atualizado quando a estrutura real do código, os contratos da API ou a topologia de execução mudarem.

## Visão geral

O FinanSys é organizado como um monorepo com duas aplicações principais:

- `apps/web`: frontend Next.js 16, React 19 e TypeScript.
- `apps/server`: backend FastAPI em Python, com Pydantic, SQLAlchemy e Alembic.

O ambiente local é orquestrado pelo `docker-compose.yml`. O frontend é exposto em `http://localhost:3000` e a API em `http://localhost:8000`. A autenticação é fornecida pelo Supabase Auth (GoTrue), mas o navegador não conversa diretamente com o Supabase: ele chama o backend, que intermedeia as operações de autenticação e administra os cookies de sessão.

```text
Navegador
   |
   | HTTP/JSON + credentials: include
   v
Next.js (web:3000) -----> FastAPI (server:8000)
                              |\
                              | \-- SQLAlchemy/psycopg --> PostgreSQL (supabase-db:5432)
                              |
                              \---- HTTP/JSON --> Kong (supabase-kong:8000)
                                                   |--> GoTrue / Supabase Auth
                                                   |--> PostgREST
                                                   \--> Storage API
```

## Frontend Next.js

O frontend fica em `apps/web` e usa o App Router do Next.js. A entrada da aplicação está em `src/app/layout.tsx` e `src/app/page.tsx`; a rota catch-all `src/app/[...slug]/page.tsx` integra as rotas de tela geradas a partir de `src/routes` pelo script `scripts/generate-routes.mjs`.

As páginas e fluxos de autenticação estão em `src/routes` e são compostos por componentes em `src/components`. O `src/app/providers.tsx` configura o `QueryClientProvider` do TanStack Query. Estilos globais ficam em `src/app/global.css` e `src/styles/variaveis.css`.

As chamadas de autenticação estão centralizadas em `src/services/auth.ts`. A URL da API é obtida de `NEXT_PUBLIC_API_BASE_URL`, com fallback para `http://localhost:8000`. As requisições enviam `credentials: "include"`, permitindo que o navegador envie e receba os cookies de sessão entre frontend e backend quando a política de CORS e os atributos dos cookies estão configurados corretamente.

## Backend FastAPI

O ponto de entrada é `apps/server/main.py`. Ele:

1. cria a aplicação FastAPI;
2. configura CORS com origens permitidas, credenciais, métodos `GET`, `POST` e `OPTIONS`, e os cabeçalhos usados pela aplicação. Apesar de o router expor `PATCH` e `DELETE` para o CRUD de transações, esses métodos ainda não estão liberados no CORS; chamadas cross-origin do navegador para atualização/exclusão podem falhar no preflight;
3. registra os routers de autenticação e transações;
4. libera o cliente Supabase e o engine SQLAlchemy no encerramento da aplicação.

As rotas atuais são:

- `GET /`: health check simples da API;
- `POST /auth/login`: autentica e cria a sessão;
- `POST /auth/refresh`: renova a sessão;
- `POST /auth/logout`: revoga a sessão e remove cookies;
- `GET /auth/me`: retorna o usuário da sessão atual;
- `POST /auth/password-recovery`: solicita recuperação de senha sem revelar se o e-mail existe;
- `POST /auth/password-recovery/complete`: conclui a troca de senha;
- `POST /transactions`: cria uma transação;
- `GET /transactions`: lista transações do usuário com filtros e paginação;
- `GET /transactions/{transaction_id}`: consulta uma transação do usuário;
- `PATCH /transactions/{transaction_id}`: atualiza uma transação do usuário;
- `DELETE /transactions/{transaction_id}`: remove uma transação do usuário.

O frontend também implementa uma chamada para `POST /auth/register` em `src/services/auth.ts`, mas esse endpoint não está presente no router FastAPI atual. Até que os dois lados sejam alinhados, o cadastro deve ser tratado como uma integração pendente, não como uma capacidade disponível da API.

O backend já possui o CRUD de transações completo. No entanto, `apps/web/src/services` contém atualmente apenas `auth.ts`; a integração do frontend com `POST`, `GET`, `PATCH` e `DELETE /transactions` ainda não está implementada.

## Relação com o trabalho em andamento

Na revisão do projeto FINANSYS, a implementação do CRUD de transações foi confirmada como concluída no backend. As tarefas de frontend relacionadas à visualização, cadastro e filtros de movimentações ainda representam trabalho de integração na aplicação web. Portanto, a existência das rotas da API não deve ser interpretada como disponibilidade da funcionalidade completa para o usuário final.

### Camadas do backend

O backend segue uma separação por responsabilidade:

- `src/routers`: camada HTTP. Declara endpoints, parâmetros, dependências, schemas de entrada/saída e códigos de status.
- `src/schemas`: contratos Pydantic da API, incluindo dados de autenticação e transações.
- `src/services`: regras de negócio. `TransactionService` valida o acesso por usuário e coordena o repositório; os serviços em `services/auth` coordenam login, refresh, logout, recuperação de senha, lockout e atividade de sessão.
- `src/repositories`: acesso a dados com SQLAlchemy. As consultas de transações sempre restringem o `user_id` autenticado.
- `src/models`: modelos ORM e restrições de domínio para `users` e `transactions`.
- `src/core`: configuração por variáveis de ambiente, engine/sessões do SQLAlchemy, CORS, cookies e dependências de autenticação.
- `src/shared/supabase`: cliente HTTP e adaptador para os endpoints de autenticação do Supabase.
- `alembic`: histórico de migrations e configuração de `Base.metadata`.

Para as rotas protegidas, a dependência consulta o cookie de acesso, valida o token no Supabase Auth e verifica no PostgreSQL se a atividade da sessão do usuário continua válida. Em transações, o usuário autenticado é passado ao serviço e usado para limitar todas as operações aos próprios registros.

## Fluxo de requisição

### Requisição pública ou de autenticação

1. Uma tela do Next.js chama uma função de `src/services`.
2. O frontend envia JSON para o endereço configurado em `NEXT_PUBLIC_API_BASE_URL` e inclui credenciais de navegador.
3. O router FastAPI valida o corpo com Pydantic e aplica a verificação de origem nos fluxos que alteram autenticação.
4. O serviço de autenticação chama o Supabase Auth por HTTP através de `SUPABASE_URL` (no Compose, `http://supabase-kong:8000`).
5. O backend traduz respostas e falhas do provedor para o contrato público da API.
6. Em login ou refresh, os tokens retornados pelo provedor são gravados em cookies; o corpo da resposta retorna somente os dados públicos do usuário e `expires_in`.

### Requisição protegida

1. O navegador envia o cookie `finansys_access_token` automaticamente.
2. A dependência de autenticação lê o cookie e chama o endpoint de usuário do Supabase Auth para validar o token.
3. O backend verifica a atividade da sessão na tabela local `users`.
4. A rota passa o identificador do usuário ao service.
5. O service chama o repository com uma sessão SQLAlchemy criada por dependência.
6. O repository consulta ou altera o PostgreSQL; a resposta é convertida para o schema da API.

## Autenticação e cookies

O backend usa dois cookies HttpOnly:

- `finansys_access_token`, disponível no caminho `/`;
- `finansys_refresh_token`, disponível no caminho `/auth`.

Ambos são configurados em `src/core/auth_cookies.py` com `HttpOnly`, `Secure` conforme `AUTH_COOKIE_SECURE` (obrigatoriamente `true` quando `SameSite=None`) e `SameSite` conforme `AUTH_COOKIE_SAMESITE`, cujo padrão é `lax`. O refresh tem duração máxima de 30 dias no cookie; a validade efetiva do access token continua sendo controlada pelo Supabase e pelo campo `expires_in`.

O login consulta lockout e registra sucesso ou falha na tabela local `users`. O refresh exige o cookie de refresh, valida a correspondência do usuário e verifica a atividade da sessão. Logout tenta revogar o token no Supabase e sempre limpa os cookies locais. Sessões inválidas retornam `401` e também removem os cookies.

Como os cookies não são acessíveis por JavaScript, o frontend deve continuar usando `credentials: "include"`. Em desenvolvimento local, `AUTH_COOKIE_SECURE=false` é definido pelo Compose; em HTTPS, essa configuração deve ser ajustada.

## Persistência: PostgreSQL e Supabase

O PostgreSQL é o serviço `supabase-db` do Compose e persiste seus dados no volume `supabase-db-data`. O backend monta a URL SQLAlchemy em `src/core/config.py` a partir de `DATABASE_URL`/`SUPABASE_DB_URL` ou de `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`. O driver utilizado é `psycopg`.

O acesso relacional da aplicação não passa pelo PostgREST: `src/core/database.py` cria o engine e as sessões SQLAlchemy diretamente contra o PostgreSQL. As migrations são executadas com Alembic. O modelo local inclui:

- `users`: identidade local associada ao UUID do usuário do Supabase, papel, tentativas de login, lockout e atividade;
- `transactions`: transações financeiras vinculadas a `users.id`, com tipo, categoria, data, valor e origem do dinheiro.

O Supabase é executado localmente por serviços Docker. O Kong (`supabase-kong`) publica a entrada em `http://localhost:8080` e roteia para GoTrue (`supabase-auth`), PostgREST (`supabase-rest`) e Storage (`supabase-storage`). O backend usa o cliente HTTP próprio em `src/shared/supabase/client.py` e `SupabaseAuthAdapter` para login, refresh, consulta de usuário, logout e recuperação de senha. O Supabase Studio fica disponível em `http://localhost:3001`; o Mailpit, usado pelo fluxo de e-mail local, em `http://localhost:8025`.

## Docker Compose e operação local

Os serviços definidos no `docker-compose.yml` são:

- `web`: Next.js, porta `3000`;
- `server`: FastAPI, porta `8000`;
- `supabase-db`: PostgreSQL, porta `5432`;
- `supabase-auth`: GoTrue;
- `supabase-rest`: PostgREST;
- `supabase-storage`: API de Storage, com volume `supabase-storage-data`;
- `supabase-kong`: gateway Supabase, porta `8080`;
- `supabase-meta`: API de metadados usada pelo Studio;
- `supabase-studio`: painel administrativo, porta `3001`;
- `mailpit`: SMTP local na porta `1025` e interface web na porta `8025`;
- `templates-server`: servidor dos templates de e-mail.

Os serviços de aplicação, banco e Supabase compartilham a rede Docker `finansys-net`. O `server` depende do banco saudável e do Kong iniciado; o `web` depende do `server` iniciado. O código de `apps/server` e `apps/web` é montado como volume no desenvolvimento, com volumes anônimos para `node_modules` e `.next` no frontend.

Para iniciar a stack:

```sh
docker compose up -d --build
```

Depois de subir o backend, a documentação OpenAPI interativa fica em `http://localhost:8000/docs`. Migrations e seed são operações do backend e devem ser executadas conforme os scripts documentados no README e na wiki do projeto.

## Pontos de integração

| Integração | Origem | Destino | Contrato/configuração |
| --- | --- | --- | --- |
| Frontend → API | `apps/web/src/services` | FastAPI | `NEXT_PUBLIC_API_BASE_URL`, JSON, `credentials: include` |
| API → Supabase Auth | `apps/server/src/shared/supabase` | Kong/GoTrue | `SUPABASE_URL`, chave pública e endpoints `/auth/v1/*` |
| API → PostgreSQL | `apps/server/src/core/database.py` e repositories | `supabase-db` | `DATABASE_URL` ou variáveis `POSTGRES_*`, SQLAlchemy/psycopg |
| Supabase Auth → banco | `supabase-auth` | `supabase-db` | `GOTRUE_DB_DATABASE_URL` |
| GoTrue → e-mail local | `supabase-auth` | `mailpit` | SMTP em `mailpit:1025` |
| Studio → serviços Supabase | `supabase-studio` | `supabase-meta`, PostgreSQL e Kong | URLs internas do Compose e chaves Supabase |

## Limites e cuidados para DEV

- Não colocar chaves do Supabase ou tokens em código, logs ou respostas da API.
- Alterações no contrato HTTP devem ser refletidas simultaneamente nos schemas/routers do backend, nos serviços do frontend e nos testes.
- Alterações no modelo relacional devem vir acompanhadas de migration Alembic; não depender apenas da definição ORM.
- Não acessar transações apenas pelo ID: o filtro por usuário é parte da regra de autorização implementada no repository.
- Ao alterar domínio, portas ou origens, revisar `docker-compose.yml`, `.env.example`, `src/core/config.py`, configuração do Playwright e os arquivos de requisições em `rest-client`.
