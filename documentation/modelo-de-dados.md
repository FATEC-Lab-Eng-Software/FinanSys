# Modelo de dados

Documento de referência para DEV sobre os modelos persistidos pelo backend.

## Entidades

### `users`

Modelo SQLAlchemy: `src.models.auth.User`.

| Campo | Tipo | Obrigatório | Regras e observações |
|---|---|---:|---|
| `id` | UUID PostgreSQL | Sim | Chave primária. É o identificador sincronizado com o Supabase Auth. |
| `email` | `varchar(320)` | Sim | Único (`uq_users_email`). Repositórios normalizam e-mails para minúsculas em operações de autenticação. |
| `first_name` | `varchar(100)` | Não | Nome obtido dos metadados do usuário no seed/autenticação. |
| `last_name` | `varchar(100)` | Não | Sobrenome obtido dos metadados do usuário no seed/autenticação. |
| `role` | `varchar(20)` | Sim | Default `client`; valores permitidos: `admin`, `client` (`ck_users_role_valid`). |
| `login_attempts` | `integer` | Sim | Default `0`; não pode ser negativo (`ck_users_login_attempts_nonnegative`). |
| `lockout_until` | `timestamptz` | Não | Fim do bloqueio temporário após tentativas inválidas. |
| `created_at` | `timestamptz` | Sim | Default de servidor `now()`. |
| `last_access_at` | `timestamptz` | Não | Último acesso registrado. |
| `last_activity_at` | `timestamptz` | Não | Usado para validar atividade da sessão. |

### `transactions`

Modelo SQLAlchemy: `src.models.transaction.Transaction`.

| Campo | Tipo | Obrigatório | Regras e observações |
|---|---|---:|---|
| `id` | `integer` | Sim | Chave primária. |
| `user_id` | UUID PostgreSQL | Sim | FK para `users.id`, com `ON DELETE CASCADE`. |
| `type` | `varchar(20)` | Sim | Enum `TransactionType`: `inflow` ou `outflow`; também validado por `ck_transactions_type_valid`. |
| `category` | `varchar(50)` | Sim | O schema Pydantic aceita apenas `work`, `housing`, `utilities`, `food`, `transportation`, `medical`, `pets`, `travel` e `other`. O modelo/migration do banco não possui constraint SQL para essa lista e aceita qualquer texto de até 50 caracteres quando gravado diretamente. |
| `transaction_date` | `date` | Sim | Data informada para a transação. |
| `value` | `numeric(12,2)` | Sim | Maior que zero (`ck_transactions_value_positive`); schemas limitam a precisão/escala. |
| `source_money` | `varchar(100)` | Sim | Texto não vazio após trim nos schemas de criação/atualização. |
| `created_at` | `timestamptz` | Sim | Default de servidor `now()`. |
| `updated_at` | `timestamptz` | Sim | Default `now()` e atualização via `onupdate=func.now()` no ORM. |

## Isolamento por usuário

`TransactionRepository` recebe sempre `user_id`. A consulta individual filtra por `id` **e** `user_id`; a listagem começa com `Transaction.user_id == user_id`; criação grava o `user_id` recebido pelo contexto autenticado. Portanto, o repositório não permite buscar ou listar transações de outro usuário através desses métodos. A FK mantém a transação vinculada ao usuário e o cascade remove suas transações quando o usuário é removido.

Há um índice composto `ix_transactions_user_id_transaction_date` para acelerar o acesso por usuário e data. Os filtros de período, tipo e categoria são aplicados adicionalmente; a listagem ordena por data decrescente e, em empate, por `id` decrescente.

## Migrations Alembic

A cadeia atual é:

1. `df3d4badaf3a_`: cria `users` inicialmente, incluindo UUID, e-mail único, papel, contagem de tentativas e timestamps.
2. `9c81f05e2a7b_users_from_auth_attempts`: consolida usuários a partir de `auth_login_attempts` quando essa tabela existe e remove as tabelas legadas `auth_login_attempts` e `financial_categories`.
3. `4b8e91d263fa_auth_session_controls`: adiciona `lockout_until` e `last_activity_at`, copiando `last_access_at` para a nova coluna quando aplicável.
4. `48f554e1dfff_create_transactions_table`: cria `transactions`, suas constraints, FK com cascade e índice por usuário/data.

Aplicar alterações com `alembic upgrade head` a partir de `apps/server`. A migration de transações depende da existência de `users`; não criar `transactions` manualmente antes de executar a cadeia.

## Seed e sincronização

`src.seeds.auth.seed` usa a API administrativa do Supabase Auth e depois sincroniza os usuários retornados na tabela `users` por meio de `UserRepository.sync_auth_user`. Os perfis explicitamente preparados são:

- `admin@finansys.com` (`admin`, Admin FinanSys);
- `pedro@gmail.com` (`client`, Pedro Cliente);
- `maria@gmail.com` (`client`, Maria Cliente).

O seed usa a senha `123456789` para essas contas, confirma o e-mail e grava `role`, `first_name` e `last_name` nos metadados do Auth. Ele não cria transações: não há seed de registros em `transactions` no código inspecionado. Para executar, é necessário configurar `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`; a sincronização também depende da conexão do banco.

## Fontes do código

- `apps/server/src/models/auth/user.py`
- `apps/server/src/models/transaction.py`
- `apps/server/src/schemas/transactions_schemas.py`
- `apps/server/src/repositories/auth/user_repository.py`
- `apps/server/src/repositories/transactions_repository.py`
- `apps/server/alembic/versions/`
- `apps/server/src/seeds/auth/seed.py`
