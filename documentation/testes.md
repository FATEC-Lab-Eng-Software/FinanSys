# Estratégia de testes

Este documento descreve a estratégia atualmente implementada no repositório. Ela combina testes automatizados do servidor FastAPI com testes de fluxo da aplicação web usando Playwright. Não há, nos scripts ou na configuração inspecionados, uma etapa de geração de cobertura percentual.

## Localização

- **Servidor:** `apps/server/src/tests/`
  - `auth/`: erros de autenticação, login, bloqueio após tentativas inválidas, recuperação de senha, sessão ociosa e repositório de usuários.
  - `transactions/`: criação, consulta, atualização, exclusão, filtros, ordenação, validação e isolamento por usuário de transações.
- **Web:** `apps/web/src/routes/*.test.tsx`
  - `login.test.tsx`: formulário responsivo, validações, visibilidade da senha, login, recuperação e redirecionamento.
  - `cadastro.test.tsx`: formulário responsivo, validações, visibilidade das senhas, e-mail já cadastrado, cadastro e redirecionamento.
  - `password-recovery.test.tsx`: links inválidos, validação e confirmação de recuperação de senha.
- **Script auxiliar:** `apps/web/scripts/generate-routes.test.mjs` usa `node:test` para validar a geração do manifesto de rotas. Ele não é descoberto pelo Playwright, porque o `playwright.config.ts` restringe `testDir` a `./src` e `testMatch` a `**/*.test.tsx`.

## Comandos reais

Antes de executar testes fora dos containers, instale as dependências:

```sh
pnpm install
pnpm --dir apps/server db:install
```

Para os testes Playwright, pode ser necessário instalar o navegador Chromium:

```sh
pnpm --dir apps/web exec playwright install chromium
```

Os testes de transações dependem de um PostgreSQL configurado e acessível pela aplicação. A stack Docker pode ser iniciada com `docker compose up -d --build`; migrations e seed não são executados automaticamente.

Na raiz do repositório:

```sh
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/server test
```

O teste do servidor executa:

```sh
python -m pytest -q --override-ini="python_files=*.test.py" --import-mode=importlib
```

Para abrir a interface do Playwright:

```sh
pnpm --dir apps/web test:ui
```

Para executar diretamente o teste do gerador de rotas:

```sh
node --test apps/web/scripts/generate-routes.test.mjs
```

O comando web usa Playwright com os projetos `chromium` e `mobile-chrome`. O próprio Playwright inicia o Next em `127.0.0.1:3100`, gera as rotas antes de subir o servidor e reutiliza um servidor existente fora de CI. O teste do servidor não inicia Docker, banco, migrations ou seed automaticamente.

## Fixtures e configuração

### Servidor

Os testes usam `pytest` com arquivos nomeados `*.test.py`, habilitados pelo `--override-ini`. Os testes de transações usam `TestClient`, sobrescrevem a dependência `get_db_session` e criam usuários/transações diretamente na sessão. A sessão é vinculada a uma conexão e usa `join_transaction_mode="create_savepoint"`.

Os testes de autenticação usam `monkeypatch` para substituir serviços, adaptadores Supabase, relógio e dependências de banco por doubles/fakes. Assim, os cenários de login, recuperação e sessão podem validar respostas, cookies, contagem de tentativas, bloqueio e falhas sem depender das respostas reais do provedor.

### Web

O Playwright usa `baseURL` `http://127.0.0.1:3100`, um worker e execução não paralela. Os testes rodam em Chrome desktop e emulador Pixel 7. Os cenários interceptam chamadas HTTP quando necessário para simular sucesso, credenciais rejeitadas, cadastro existente, recuperação e falhas do backend.

## Cobertura funcional atual

- validações de entrada de login, cadastro e recuperação de senha;
- autenticação por cookies HTTP-only, respostas públicas genéricas e não exposição de tokens/senhas;
- tentativas inválidas, bloqueio temporário, expiração e renovação de sessão ociosa;
- recuperação de senha por adaptador Supabase e tratamento de erros do provedor;
- operações CRUD de transações, validação de valor/categoria/origem, filtros por período e categoria e ordenação;
- isolamento de transações por usuário e rejeição de requisições sem sessão;
- responsividade e navegação básica dos fluxos de login, cadastro e recuperação;
- geração e manifesto de rotas no script auxiliar.

## Limites conhecidos

- Não há configuração de `pytest-cov`, relatório de cobertura ou limiar de cobertura.
- O teste Playwright valida as rotas de autenticação existentes; não há testes E2E equivalentes documentados para todas as telas ou para o CRUD de transações.
- O teste `apps/web/scripts/generate-routes.test.mjs` precisa ser executado separadamente; `pnpm --dir apps/web test` não o inclui.
- Os testes do servidor usam mocks/fakes para integrações Supabase e não constituem um teste de integração contra um projeto Supabase real.
- O teste de transações depende da configuração de banco usada por `get_db_session`; o script de teste não prepara o banco por migrations nem executa seed.
- A configuração do Playwright sobe o Next, mas não inicia a API FastAPI separadamente. Portanto, os testes web não comprovam a integração completa entre frontend, API, banco e Supabase.
- Não há, nos scripts inspecionados, um comando único que execute todos os testes do servidor, do frontend e do gerador de rotas em uma só etapa.
- Em uma execução local revisada, foram observadas falhas de testes de transações quando a tabela `transactions` ainda não existia no banco. Aplique as migrations antes de interpretar esse resultado como falha da implementação.
