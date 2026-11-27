# API do FinanSys

Contrato observado em `apps/server/main.py`, nos routers, schemas e testes do backend. A API FastAPI não usa prefixo global; em desenvolvimento, a base usual é `http://localhost:8000`. A documentação interativa fica em `/docs`.

## Autenticação

As sessões são mantidas por cookies `HttpOnly`: `finansys_access_token` (path `/`) e `finansys_refresh_token` (path `/auth`). O cliente envia os cookies nas chamadas autenticadas; os atributos `Secure` e `SameSite` são configurados pelo servidor.

Respostas de erro usam, em geral, o formato:

```json
{"detail":{"code":"codigo_estavel","message":"Mensagem para o cliente."}}
```

O login, refresh, logout e recuperação validam a origem do navegador. Payloads inválidos retornam `422`; uma origem não confiável retorna `403`. Falhas específicas do provedor e limites de tentativa podem retornar `429`, `502` ou `503`, conforme o fluxo.

## Endpoints de autenticação

### `POST /auth/register`

Cria uma conta no Supabase Auth. Requer origem confiável. Entrada: `{"name":"Dev User","email":"dev@example.com","password":"password"}`. `name` aceita 2–120 caracteres e espaços são normalizados; `email` aceita 3–320 caracteres e é normalizado para minúsculas; `password` exige no mínimo 8 caracteres. Resposta `201`: `{"message":"Cadastro realizado com sucesso."}`. Dados inválidos retornam `422`, e-mail já cadastrado retorna `409` (`email_already_registered`), indisponibilidade do serviço retorna `503` e falhas do provedor podem retornar `502`.

### `POST /auth/login`

Autentica o usuário e grava os cookies de sessão. Não exige autenticação prévia.

Entrada:

```json
{"email":"dev@example.com","password":"password"}
```

`email` tem 3–320 caracteres, é aparado e convertido para minúsculas; `password` exige no mínimo 8 caracteres.

Resposta `200`:

```json
{"user":{"id":"uuid","email":"dev@example.com","first_name":"Dev","last_name":"User"},"expires_in":3600}
```

Possíveis respostas observadas: `401` credenciais inválidas, `403` origem não confiável, `422` dados inválidos, `423` conta temporariamente bloqueada (inclui `locked_until` e header `Retry-After`), `429` limite de tentativas, `500` erro interno, `502` falha do provedor e `503` serviço de autenticação indisponível.

### `POST /auth/refresh`

Renova a sessão usando o cookie `finansys_refresh_token`. A chamada é feita sem corpo. Retorna `200` com o mesmo schema de login e substitui os cookies. Sem sessão válida retorna `401` (`invalid_session`); também pode retornar `500` ou `503`.

### `GET /auth/me`

Retorna o usuário da sessão atual. Exige o cookie de acesso.

Resposta `200`:

```json
{"id":"uuid","email":"dev@example.com","first_name":"Dev","last_name":"User"}
```

Sem cookie, sessão expirada ou inválida: `401` (`invalid_session`). Falhas de autenticação/configuração podem retornar `500` ou `503`.

### `POST /auth/logout`

Encerra a sessão e remove os cookies. Usa a sessão atual quando disponível, mas a operação de limpeza é idempotente. Resposta `204`, sem corpo.

### `POST /auth/password-recovery`

Solicita recuperação de senha. Não exige sessão. Entrada: `{"email":"dev@example.com"}`. O e-mail segue as mesmas validações do login.

Resposta `202`:

```json
{"message":"Se houver uma conta associada, enviaremos instruções para redefinir a senha."}
```

O texto é igual para contas existentes e desconhecidas. Dados inválidos retornam `422`; indisponibilidade do provedor retorna `503`.

### `POST /auth/password-recovery/complete`

Conclui a troca usando o token recebido no fluxo de recuperação. Entrada:

```json
{"access_token":"token-do-link","new_password":"nova-senha"}
```

`new_password` exige no mínimo 8 caracteres. Resposta `200`: `{"message":"Senha redefinida com sucesso."}`. Dados inválidos retornam `422`; link inválido/expirado retorna `400` (`invalid_recovery_link`); senha rejeitada pelo provedor retorna `422` (`weak_password`); indisponibilidade retorna `503`.

## Endpoints de transações

Todos exigem sessão válida (`finansys_access_token`). O backend implementa o CRUD completo, e o frontend possui o serviço `apps/web/src/services/transactions.ts`. Os dados são sempre filtrados pelo usuário autenticado; acessar uma transação de outro usuário resulta em `404`, não em exposição do recurso.

Tipos aceitos: `type`: `inflow` ou `outflow`; `category`: `work`, `housing`, `utilities`, `food`, `transportation`, `medical`, `pets`, `travel` ou `other`.

Schema de criação:

```json
{
  "type":"outflow",
  "category":"food",
  "transaction_date":"2026-10-04",
  "value":"25.90",
  "source_money":"Cartão"
}
```

`value` deve ser maior que zero, com até 12 dígitos e 2 casas decimais. `source_money` tem 1–100 caracteres não vazios.

Schema de saída:

```json
{
  "id":1,
  "type":"outflow",
  "category":"food",
  "transaction_date":"2026-10-04",
  "value":"25.90",
  "source_money":"Cartão",
  "created_at":"2026-10-04T12:00:00Z",
  "updated_at":"2026-10-04T12:00:00Z"
}
```

### `POST /transactions`

Cria uma transação. Resposta `201` com o schema de saída. Erros: `401` sessão inválida, `422` payload inválido e `503` (`transaction_store_unavailable`) quando o armazenamento não está disponível.

### `GET /transactions`

Lista as transações do usuário. Query params opcionais: `start_date`, `end_date` (ISO `YYYY-MM-DD`), `type`, `category`, `limit` (padrão `50`, de 1 a 200) e `offset` (padrão `0`, mínimo 0). `start_date` não pode ser posterior a `end_date`.

Resposta `200`: array de objetos de transação. Também pode retornar `401`, `422` ou `503`.

Exemplo: `GET /transactions?type=outflow&limit=20&offset=0`.

### `GET /transactions/{transaction_id}`

Consulta uma transação do usuário. Resposta `200` com o schema de saída; `401` para sessão inválida, `404` (`transaction_not_found`) quando não existe ou pertence a outro usuário, e `503` em falha de armazenamento.

### `PATCH /transactions/{transaction_id}`

Atualiza parcialmente uma transação. O corpo pode conter um ou mais campos de criação; campos enviados não podem ser nulos. Exemplo:

```json
{"value":"29.90","category":"food"}
```

Resposta `200` com o recurso atualizado. Erros: `401`, `404`, `422` (corpo vazio, valor inválido ou enum desconhecido) e `503`.

### `DELETE /transactions/{transaction_id}`

Exclui uma transação do usuário. Resposta `204`, sem corpo. Erros: `401`, `404` (`transaction_not_found`) ou `503`.

## Endpoints de metas

Todos exigem sessão válida. As operações são limitadas ao usuário autenticado, e metas pertencentes a outra pessoa são respondidas como `404`.

Categorias válidas: `work`, `housing`, `utilities`, `food`, `transportation`, `medical`, `pets`, `travel` e `other`. O status é calculado pela regra de domínio: `pending` ou `done`.

Exemplo de criação:

```json
{
  "name":"Reserva de emergência",
  "category":"other",
  "target_date":"2027-12-31",
  "target_value":"5000.00",
  "accumulated_value":"250.00"
}
```

`target_date` é opcional. `target_value` deve ser maior que zero; `accumulated_value` deve ser maior ou igual a zero. Valores aceitam até 12 dígitos e 2 casas decimais.

### `POST /goals`

Cria uma meta. Resposta `201` com `id`, nome, categoria, prazo, valores, status e timestamps.

### `GET /goals`

Lista metas do usuário. Filtros opcionais: `status`, `category`, `limit` (padrão `50`, de 1 a 200) e `offset` (padrão `0`, mínimo 0). Resposta `200` com array de metas.

### `GET /goals/{goal_id}`

Retorna a meta do usuário. Respostas: `200`, `404` se não encontrada ou de outro usuário.

### `GET /goals/{goal_id}/progress`

Retorna `goal_id`, `remaining_value` e `remaining_percentage`, calculados a partir dos valores alvo e acumulado. Respostas: `200` ou `404`.

### `PATCH /goals/{goal_id}`

Atualiza parcialmente nome, categoria, prazo, valor alvo ou valor acumulado. Informe pelo menos um campo; campos não nulos não podem receber `null`, exceto `target_date`, que pode ser limpo. A aplicação recalcula o status ao alterar valores. Respostas: `200`, `404` ou `422` para payload inválido.

### `DELETE /goals/{goal_id}`

Remove a meta. Resposta `204`, sem corpo; também pode retornar `404`.

## Assistente financeiro

### `POST /assistant/chat`

Envia o histórico da conversa ao assistente Hermes. Exige cookie de sessão válido e origem confiável. O corpo contém de 1 a 20 mensagens, cada uma com `role` igual a `user` ou `assistant` e `content` não vazio de até 4.000 caracteres. A última mensagem deve ser do usuário e o conteúdo total deve ter até 12.000 caracteres.

Entrada:

```json
{"messages":[{"role":"user","content":"Como foram minhas despesas neste mês?"}]}
```

Resposta `200` segue `AssistantChatResponse`:

```json
{
  "message":"Seu resumo financeiro...",
  "artifacts":[],
  "books":[]
}
```

`message` contém a resposta textual. `artifacts` pode incluir arquivos gerados como PDF, com `filename`, `content_type` e `content_base64`. `books` pode incluir até 10 recomendações com título, autores, descrição, data de publicação e link de referência. Falhas dos provedores ou ferramentas usam o envelope de erro da API com código e mensagem.

## Endpoint de diagnóstico

### `GET /`

Não exige autenticação. Retorna `200` com `{"status":"Backend FastAPI rodando perfeitamente!"}`.

## Testes de referência

Os contratos são exercitados em `apps/server/src/tests/auth/`, `apps/server/src/tests/transactions/` e `apps/server/src/tests/goals/`. Esses testes confirmam, entre outros, lockout (`423`), recuperação de senha, sessão ociosa, isolamento por usuário, filtros, paginação, validação e códigos `201/200/204/401/404/422/503`.
