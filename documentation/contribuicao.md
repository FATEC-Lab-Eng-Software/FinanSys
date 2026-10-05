# Guia de contribuição do FinanSys

Este guia reúne o fluxo seguro para desenvolvimento no repositório. As seções marcadas como **Fato do repositório** descrevem arquivos e comandos atualmente versionados. As seções marcadas como **Recomendação** são práticas sugeridas e não representam regras automatizadas pelo projeto.

## Antes de começar

### Fato do repositório

- O projeto é um monorepo pnpm com os workspaces `apps/server` e `apps/web`.
- O backend usa Python, FastAPI, SQLAlchemy e Alembic; o frontend usa Next.js, React e TypeScript.
- O ambiente local é orquestrado por `docker-compose.yml` e inclui a API, o frontend, PostgreSQL/Supabase, Kong e Mailpit.
- Os pré-requisitos informados no README são Docker, Node.js, pnpm 11.9 ou compatível e Python 3.11 ou superior quando o backend for executado fora do container.

### Recomendação

1. Atualize sua cópia local antes de criar uma alteração.
2. Leia o README, a documentação de infraestrutura e o código da área que será alterada.
3. Não trabalhe diretamente em `main` ou `develop`; use uma branch de trabalho e abra um PR.

## Branches e isolamento do trabalho

### Fato do repositório

O histórico local/remoto contém `main`, `develop` e branches de trabalho como `feature/FINANSYS-7`, `finansys-12`, `finansys-13`, `finansys-19`, `finansys-21` e `finansys-docs`. O repositório não contém uma política formal de branching ou um workflow de CI que defina a branch de destino.

### Recomendação

Use `main` como referência de integração apenas quando o time confirmar esse fluxo. Crie uma branch curta e relacionada à tarefa, por exemplo:

```sh
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c feature/<chave-ou-descricao-curta>
```

Se a equipe estiver trabalhando a partir de `develop`, substitua `main` por `develop` de forma consistente. Não deduza a branch de destino apenas pelo nome da sua branch; confirme no PR ou com o responsável do repositório.

## Instalação e execução local

### Configuração de secrets

### Fato do repositório

O arquivo `.env` é ignorado pelo Git. O arquivo `.env.example` lista `POSTGRES_PASSWORD`, `JWT_SECRET`, `ANON_KEY` e `SUPABASE_SERVICE_ROLE_KEY`. O README exige um `JWT_SECRET` com pelo menos 32 caracteres. O script de chaves não exibe os valores no terminal e não sobrescreve chaves existentes sem `--force`.

```sh
Copy-Item .env.example .env
pnpm install
pnpm supabase:keys
```

Para regenerar as chaves depois de trocar o `JWT_SECRET`:

```sh
pnpm supabase:keys -- --force
```

### Recomendação

- Nunca faça commit de `.env`, chaves Supabase, senhas, tokens ou valores reais de serviços.
- Compartilhe somente nomes de variáveis e valores fictícios em exemplos, issues e PRs.
- O Compose possui alguns valores padrão voltados ao ambiente local; não os trate como configuração de produção sem revisão de segurança.

### Subir a aplicação

### Fato do repositório

Pela raiz, a stack completa pode ser iniciada com:

```sh
docker compose up -d --build
```

Também existem os scripts:

```sh
pnpm dev          # web e server em background
pnpm dev:web      # somente o serviço web
pnpm dev:server   # somente o serviço server
```

`pnpm dev` usa modo desacoplado (`-d`). Os comandos `pnpm dev:web` e `pnpm dev:server` permanecem em primeiro plano. Com a stack iniciada, a documentação interativa da API fica em `http://localhost:8000/docs`. O Compose expõe, por padrão, a aplicação web em `http://localhost:3000`, a API em `http://localhost:8000` e o gateway Supabase/Kong em `http://localhost:8080`.

## Banco de dados e migrations

### Fato do repositório

As migrations ficam em `apps/server/alembic/versions`. Os scripts disponíveis em `apps/server/package.json` são:

```sh
pnpm --dir apps/server db:migration:generate
pnpm --dir apps/server db:migration:apply
pnpm --dir apps/server db:seed
```

`db:migration:generate` usa o autogenerate do Alembic e depende de uma conexão válida com o banco e das variáveis de ambiente configuradas. Revise a migration gerada antes de aplicá-la.

Também é possível instalar as dependências do backend fora do container com:

```sh
pnpm --dir apps/server db:install
```

### Recomendação

- Inspecione a migration gerada antes de aplicá-la; `--autogenerate` não substitui revisão humana.
- Em alterações de schema, descreva no PR a ordem de aplicação, compatibilidade e eventual necessidade de seed.
- Faça backup ou use um banco descartável antes de testar operações destrutivas. Não aplique migrations experimentais no banco compartilhado sem autorização.
- Não edite migrations já aplicadas para “corrigir” o histórico; crie uma nova migration, salvo decisão explícita do responsável pelo banco.

## Testes e qualidade

### Fato do repositório

Os comandos versionados para validação são:

```sh
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/server test
```

O frontend também possui `test:ui`, `build` e geração de rotas. O backend executa pytest com o padrão de arquivos `*.test.py`. Não há script global de lint/teste nem workflow de CI versionado em `.github`.

### Recomendação

Execute pelo menos o lint do frontend e os testes dos dois aplicativos quando a alteração puder afetá-los. Para mudanças de banco, autenticação ou infraestrutura, suba a stack e teste o fluxo relevante. Registre no PR os comandos executados e qualquer limitação ambiental.

## Commits e hooks

### Fato do repositório

O projeto usa Husky e commitlint. O hook `.husky/commit-msg` executa:

```sh
pnpm exec commitlint --edit "$1"
```

O `commitlint.config.js` estende `@commitlint/config-conventional`; portanto, as mensagens de commit devem seguir Conventional Commits para passar pelo hook.

### Recomendação

Use mensagens curtas e específicas, por exemplo:

```text
docs: document contribution workflow
fix(auth): handle expired session
```

Não desabilite o hook para contornar uma mensagem inválida. Se o hook falhar por dependência ausente, rode `pnpm install` e investigue a causa antes de usar qualquer bypass.

## Pull request

### Fato do repositório

O template `.github/PULL_REQUEST_TEMPLATE.md` solicita: chave e título da task, descrição da alteração, como testar e observações sobre decisões, dependências e limitações. O repositório não define aprovadores obrigatórios, quantidade de revisores, checks obrigatórios ou branch de merge em arquivos versionados.

### Checklist recomendado

- [ ] A alteração está limitada à task e não inclui secrets ou arquivos gerados indevidos.
- [ ] O PR informa a chave da task, objetivo e escopo.
- [ ] Os comandos de teste/lint executados e seus resultados estão descritos.
- [ ] Migrations, seeds, variáveis de ambiente e mudanças de infraestrutura estão explicitadas.
- [ ] A documentação foi atualizada quando o fluxo de uso ou contribuição mudou.
- [ ] O diff foi revisado e não contém mudanças acidentais.
- [ ] O PR está pronto para revisão ou identifica claramente o que ainda está pendente.

Antes de publicar, revise localmente:

```sh
git diff --check
git status --short
git diff --stat
```

## Referências do repositório

- [README](../README.md)
- [Arquitetura e infraestrutura](./infraestructure.md)
- [Template de pull request](../.github/PULL_REQUEST_TEMPLATE.md)
- [Configuração do backend](../apps/server/package.json)
- [Configuração do frontend](../apps/web/package.json)
- [Orquestração local](../docker-compose.yml)
