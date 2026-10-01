# FinanSys

## Gerar chaves locais do Supabase

Copie `.env.example` para `.env` e configure `JWT_SECRET` com pelo menos 32
caracteres. Gere as chaves JWT `anon` e `service_role` com:

```sh
pnpm supabase:keys
```

O comando grava `ANON_KEY` e `SUPABASE_SERVICE_ROLE_KEY` no `.env` raiz, usado
pelo Docker Compose, sem exibir os valores no terminal. Para outro arquivo:

```sh
pnpm supabase:keys -- --env-file caminho/para/.env
```

O gerador não substitui chaves existentes. Use `--force` somente quando tiver
alterado `JWT_SECRET` e precisar regenerá-las:

```sh
pnpm supabase:keys -- --force
```

Após gerar as chaves, inicie a stack Supabase com `docker compose up -d`.
