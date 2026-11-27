# Estratégia de testes

Este documento descreve a estratégia atualmente implementada no repositório. Ela combina testes automatizados do servidor FastAPI com testes de fluxo da aplicação web usando Playwright. A rotina atual apresenta resultados dos testes sem calcular cobertura percentual.

## Localização

- **Servidor:** `apps/server/src/tests/`
  - `auth/`: erros de autenticação, login, bloqueio após tentativas inválidas, recuperação de senha, sessão ociosa e repositório de usuários.
  - `transactions/`: criação, consulta, atualização, exclusão, filtros, ordenação, validação e isolamento por usuário de transações.
  - `goals/`: CRUD de metas, validações, filtros, progresso e isolamento por usuário.
- **Web:** `apps/web/src/tests/*.test.tsx`
  - `login.test.tsx`: formulário responsivo, validações, visibilidade da senha, login, recuperação e redirecionamento.
  - `cadastro.test.tsx`: formulário responsivo, validações, visibilidade das senhas, e-mail já cadastrado, cadastro e redirecionamento.
  - `password-recovery.test.tsx`: links inválidos, validação e confirmação de recuperação de senha.

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

O comando web usa Playwright com os projetos `chromium` e `mobile-chrome`. O próprio Playwright inicia o Next em `127.0.0.1:3100` e reutiliza um servidor existente fora de CI. O teste do servidor não inicia Docker, banco, migrations ou seed automaticamente.

## Fixtures e configuração

### Servidor

Os testes usam `pytest` com arquivos nomeados `*.test.py`, habilitados pelo `--override-ini`. Os testes de transações e metas usam `TestClient`, sobrescrevem a dependência `get_db_session` e criam registros diretamente na sessão. A sessão é vinculada a uma conexão e usa `join_transaction_mode="create_savepoint"`.

Os testes de autenticação usam `monkeypatch` para substituir serviços, adaptadores Supabase, relógio e dependências de banco por doubles/fakes. Assim, os cenários de login, recuperação e sessão podem validar respostas, cookies, contagem de tentativas, bloqueio e falhas sem depender das respostas reais do provedor.

### Web

O Playwright usa `baseURL` `http://127.0.0.1:3100`, um worker e execução não paralela. Os testes rodam em Chrome desktop e emulador Pixel 7. Os cenários interceptam chamadas HTTP quando necessário para simular sucesso, credenciais rejeitadas, cadastro existente, recuperação e falhas do backend.

## Cobertura funcional atual

- validações de entrada de login, cadastro e recuperação de senha;
- autenticação por cookies HTTP-only, respostas públicas genéricas e não exposição de tokens/senhas;
- tentativas inválidas, bloqueio temporário, expiração e renovação de sessão ociosa;
- recuperação de senha por adaptador Supabase e tratamento de erros do provedor;
- operações CRUD de transações, validação de valor/categoria/origem, filtros por período e categoria e ordenação;
- operações CRUD de metas, cálculo de progresso, atualização de status, filtros e isolamento por usuário;
- isolamento de transações por usuário e rejeição de requisições sem sessão;
- responsividade e navegação básica dos fluxos de login, cadastro e recuperação.

## Escopo e cobertura atual

- A configuração atual do pytest não gera relatório percentual de cobertura.
- Os cenários Playwright documentados se concentram nos fluxos de autenticação; operações de transações e metas têm cobertura nos testes do servidor.
- Os testes do servidor usam mocks/fakes para integrações Supabase e não constituem um teste de integração contra um projeto Supabase real.
- Os testes do servidor usam o banco configurado por `get_db_session`; migrations e seed são executados separadamente.
- O Playwright inicia a aplicação Next.js na porta `3100`; a API FastAPI é iniciada conforme o ambiente de desenvolvimento.
- Os comandos de teste são distribuídos entre os workspaces web e server.
