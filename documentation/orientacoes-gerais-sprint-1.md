# 📋 Orientações Gerais sobre o Projeto | Sprint 1

> **Autora:** Yasmin Cristina Padilha  
> **Documento:** Regras de desenvolvimento do FinanSys (válidas para todos os integrantes e todas as tarefas do Jira).

---

## 1. Sobre este Documento
Este documento reúne as regras de desenvolvimento do FinanSys e vale para todos os integrantes e todas as tarefas do Jira.

---

## 2. Responsabilidades

### 🎨 Frontend
Quem assume uma tarefa de frontend é responsável por:
- **Integração:** Integrar a tela com a tarefa de backend correspondente (quando houver).
- **Responsividade:** Deixar a tela responsiva em diferentes resoluções.
- **Design System:** Seguir o protótipo do Figma, sempre baseado na tela de login como referência visual.
- **Feedback Visual (Estados da Tela):**
  - Mostrar aviso quando não houver dados cadastrados (*empty state*).
  - Exibir indicador enquanto os dados carregam (*loading*).
  - Exibir mensagem amigável e clara em caso de erro.

### ⚙️ Backend
Quem assume uma tarefa de backend é responsável por:
- **Banco de Dados:** Criar as tabelas e migrações necessárias no banco de dados.
- **Segurança e Validação:** Validar os dados recebidos e **garantir que cada usuário acesse apenas os seus próprios dados** (isolamento de tenant/usuário).
- **Comunicação:** Avisar a pessoa responsável pelo frontend sobre qualquer mudança na API.

---

## 3. Fluxo de Trabalho (Git & Jira)

1. **Jira:** Atribua a tarefa a você no Jira e mova para **Em andamento**.
2. **Branch:** Crie uma branch a partir da `develop` com o nome da sua task:
   - **Padrão de nome de branch:** `tipo/CHAVE-DA-TASK` (Exemplo: `feature/FINANSYS-12`).
3. **Desenvolvimento:** Desenvolva e teste localmente.
4. **Pull Request:** Abra o PR e mova a tarefa no Jira para **Em revisão**.
5. **Comunicação:** Avise no canal de comunicação da equipe que abriu o PR e precisa de revisão.
6. **Finalização:** Após aprovação e merge na `develop`, mova a tarefa para **Concluído**.

### Convenção de Commits
- **Formato:** `tipo(CHAVE): descrição`
- **Exemplo:** `feat(FINANSYS-13): cria endpoint de autenticação`

---

## 4. Pull Requests (PRs)

- **Proibido Force Push:** Não utilize `git push --force`.
- **Relação 1:1:** Cada PR corresponde a exatamente uma tarefa do Jira.
- **Aprovação Obrigatória:** O PR precisa da aprovação de pelo menos outro integrante antes do merge.

### Modelo de Descrição do PR (Copiar e Preencher)
```markdown
# Tarefa: FINANSYS-XX
# O que foi feito:
- 

# Como testar:
1. 
2. 

# Resultado esperado:

# Prints ou exemplos (opcional):
```

---

## 5. Boas Práticas

- **Testes de Regressão:** Antes de abrir o PR, confira se suas alterações não quebraram outras partes do sistema.
- **Empty States:** Quando ainda não houver dados cadastrados, o componente deve exibir mensagem amigável (Ex: *"Você ainda não cadastrou nenhuma meta"*).
- **Loading & Error:** Sempre indique carregamento e trate mensagens de erro de forma clara.
- ⚠️ **Moeda e Valores Financeiros:** **NUNCA use `float` para valores em dinheiro**, evitando erros de precisão e arredondamento (utilize `Numeric`/`Decimal` no Python/Postgres ou inteiros em centavos).

---

## 6. Tabelas do Banco de Dados

Campos base para alinhamento entre frontend e backend. Se precisar de outros campos durante o desenvolvimento, avise o responsável pela tarefa relacionada.

> **Regra Geral:** Todas as tabelas devem conter `created_at` (data de criação) e `updated_at` (data de atualização). Registros financeiros e metas **sempre pertencem a um usuário** (`user_id`).

### 👤 Usuários (`users`)
- `id`
- `nome de usuário` (username)
- `e-mail` (único)
- `senha` (armazenar exclusivamente o hash)
- `tentativas de login` (failed_login_attempts)
- `bloqueado até` (locked_until)

### 💰 Transações / Registro Financeiro (`transactions`)
- `id`
- `id do usuário` (foreign key)
- `tipo` (`entrada` ou `saída`)
- `categoria` (`alimentação`, `trabalho`, `transporte`, etc.)
- `data`
- `valor` (**Numeric/Decimal**, nunca float)
- `fonte do dinheiro` (`carteira`, `cartão`, etc.)

### 🎯 Metas (`goals`)
- `id`
- `id do usuário` (foreign key)
- `nome`
- `prazo`
- `valor total` (**Numeric/Decimal**)
- `valor acumulado` (**Numeric/Decimal**)
- `status` (`pendente` ou `concluída`)

---

## 7. Critérios de Conclusão (Definition of Done - DoD)

Uma tarefa só é considerada pronta quando:
1. Todos os critérios de aceite da task no Jira forem cumpridos.
2. Frontend e backend estiverem integrados (quando houver as duas partes).
3. O Pull Request for revisado, aprovado e mesclado.
4. Nenhuma outra parte do sistema foi quebrada.
